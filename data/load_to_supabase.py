"""
load_to_supabase.py - muat data sintetis ke Supabase (PostgreSQL), bertahap dan AMAN DIJALANKAN ULANG.

Jalankan dari folder utama proyek:
    python -m data.load_to_supabase              # upsert (aman diulang)
    python -m data.load_to_supabase --reset      # kosongkan tabel data dulu, lalu muat ulang
    python -m data.load_to_supabase --cek        # hanya bandingkan jumlah baris CSV vs database

Butuh DATABASE_URL di file .env, misalnya:
    postgresql+psycopg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
(awalan postgresql:// atau postgres:// otomatis diubah menjadi postgresql+psycopg://)

Sumber data: faskes, peserta, klaim, label_sintetis dari CSV; verifikator, pengecualian_layanan,
dan pengaturan dari config.py.
"""
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

import config as C

# (tabel, file csv atau None, kolom, kolom kunci, kolom tanggal)
# Urutan penting: tabel induk dulu, baru tabel yang punya foreign key.
TABEL = [
    (C.T_FASKES, "faskes.csv", ["id_faskes", "nama_faskes", "jenis_faskes", "kota"], ["id_faskes"], []),
    (C.T_PESERTA, "peserta.csv", ["id_peserta_samaran", "nama_peserta"], ["id_peserta_samaran"], []),
    (C.T_VERIFIKATOR, None, ["id_verifikator", "nama_verifikator", "peran"], ["id_verifikator"], []),
    (C.T_KLAIM, "klaim.csv",
     ["id_klaim", "no_episode", "id_peserta_samaran", "id_faskes", "tanggal_masuk", "tanggal_keluar",
      "periode_pengajuan", "kode_diagnosis", "kode_tindakan", "kode_inacbg", "nilai_klaim", "teks_resume_medis"],
     ["id_klaim"], ["tanggal_masuk", "tanggal_keluar"]),
    (C.T_LABEL, "label_sintetis.csv", ["id_klaim", "is_fraud", "jenis_fraud", "id_klaim_asal"], ["id_klaim"], []),
]

# Tabel yang dikosongkan oleh --reset (hasil_deteksi, keputusan, audit_log ikut karena bergantung pada klaim)
TABEL_RESET = [C.T_LABEL, C.T_HASIL, C.T_KEPUTUSAN, C.T_AUDIT, C.T_KLAIM, C.T_PESERTA,
               C.T_FASKES, C.T_VERIFIKATOR, C.T_PENGECUALIAN]


def buat_engine():
    """Buat koneksi SQLAlchemy dari DATABASE_URL (.env)."""
    load_dotenv(C.ROOT_DIR / ".env")
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        sys.exit("DATABASE_URL belum diisi. Isi file .env dengan connection string Supabase.")
    for awal in ("postgresql://", "postgres://"):
        if url.startswith(awal):
            url = "postgresql+psycopg://" + url[len(awal):]
    # prepare_threshold=None: aman untuk pooler mode transaksi (port 6543) yang tidak mendukung prepared statement
    return create_engine(url, connect_args={"prepare_threshold": None}, pool_pre_ping=True)


def ambil_baris(nama_tabel, nama_file, kolom, kolom_tanggal):
    """Ambil baris sebagai list dict bertipe Python murni (date, bool, int, None)."""
    if nama_file is None:                                  # verifikator berasal dari config.py
        return [dict(zip(kolom, v)) for v in C.DAFTAR_VERIFIKATOR]
    df = pd.read_csv(C.CSV_DIR / nama_file)[kolom]
    for k in kolom_tanggal:
        df[k] = pd.to_datetime(df[k]).dt.date
    df = df.astype(object).where(df.notna(), None)
    return df.to_dict("records")


def upsert(engine, tabel, kolom, kunci, baris):
    """Masukkan baris per batch; bila kunci sudah ada, perbarui kolom lainnya."""
    non_kunci = [k for k in kolom if k not in kunci]
    sql = (f"INSERT INTO {tabel} ({', '.join(kolom)}) VALUES ({', '.join(':' + k for k in kolom)}) "
           f"ON CONFLICT ({', '.join(kunci)}) DO "
           + (f"UPDATE SET {', '.join(f'{k} = EXCLUDED.{k}' for k in non_kunci)}" if non_kunci else "NOTHING"))
    n = C.UKURAN_BATCH
    for i in range(0, len(baris), n):
        with engine.begin() as conn:
            conn.execute(text(sql), baris[i:i + n])
        print(f"  {tabel}: {min(i + n, len(baris))}/{len(baris)}", end="\r")
    print(f"  {tabel}: {len(baris)} baris diproses" + " " * 10)


def muat_tabel_kecil(engine):
    """pengecualian_layanan (hanya bila kosong) dan pengaturan (tidak menimpa nilai yang sudah diubah)."""
    with engine.begin() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {C.T_PENGECUALIAN}")).scalar()
        if n == 0:
            conn.execute(
                text(f"INSERT INTO {C.T_PENGECUALIAN} (kode_diagnosis, kode_tindakan, keterangan) "
                     f"VALUES (:kode_diagnosis, :kode_tindakan, :keterangan)"),
                [dict(kode_diagnosis=a, kode_tindakan=b, keterangan=c) for a, b, c in C.DAFTAR_PENGECUALIAN])
            print(f"  {C.T_PENGECUALIAN}: {len(C.DAFTAR_PENGECUALIAN)} baris dimasukkan")
        else:
            print(f"  {C.T_PENGECUALIAN}: sudah berisi {n} baris, dilewati")
        conn.execute(
            text(f"INSERT INTO {C.T_PENGATURAN} (kunci, nilai) VALUES (:kunci, :nilai) ON CONFLICT (kunci) DO NOTHING"),
            [dict(kunci=k, nilai=v) for k, v in C.PENGATURAN_AWAL.items()])
        print(f"  {C.T_PENGATURAN}: nilai awal dipastikan ada")


def cek_jumlah(engine):
    """Bandingkan jumlah baris yang seharusnya (CSV/config) dengan isi database."""
    label = pd.read_csv(C.CSV_DIR / "label_sintetis.csv")
    harapan = [
        (C.T_FASKES, len(C.DAFTAR_FASKES)),
        (C.T_PESERTA, len(pd.read_csv(C.CSV_DIR / "peserta.csv"))),
        (C.T_VERIFIKATOR, len(C.DAFTAR_VERIFIKATOR)),
        (C.T_KLAIM, len(pd.read_csv(C.CSV_DIR / "klaim.csv"))),
        (C.T_LABEL, len(label)),
        (C.T_PENGECUALIAN, len(C.DAFTAR_PENGECUALIAN)),
    ]
    semua_ok = True
    with engine.connect() as conn:
        for t, n_harap in harapan:
            n_db = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            ok = n_db == n_harap
            semua_ok &= ok
            print(f"  [{'OK' if ok else 'GAGAL'}] {t:<22} seharusnya={n_harap:>6} | database={n_db:>6}")
        n_fraud = conn.execute(text(f"SELECT COUNT(*) FROM {C.T_LABEL} WHERE is_fraud")).scalar()
        n_fraud_csv = int(label["is_fraud"].sum())
        ok = n_fraud == n_fraud_csv
        semua_ok &= ok
        print(f"  [{'OK' if ok else 'GAGAL'}] klaim kembar di label_sintetis: seharusnya={n_fraud_csv} | database={n_fraud}")
    print("\nRINGKASAN:", "SEMUA SESUAI" if semua_ok else "ADA YANG TIDAK SESUAI")


def main():
    ap = argparse.ArgumentParser(description="Muat data sintetis ke Supabase")
    ap.add_argument("--reset", action="store_true", help="kosongkan tabel data sebelum memuat")
    ap.add_argument("--yes", action="store_true", help="lewati konfirmasi --reset")
    ap.add_argument("--cek", action="store_true", help="hanya bandingkan jumlah baris CSV vs database")
    args = ap.parse_args()

    for t in TABEL:
        if t[1] and not (C.CSV_DIR / t[1]).exists():
            sys.exit(f"File {t[1]} belum ada. Jalankan dulu: python -m data.generate_synthetic")
    engine = buat_engine()
    with engine.connect() as conn:                     # tes koneksi cepat
        conn.execute(text("SELECT 1"))
    print("Koneksi database OK.")

    if args.cek:
        cek_jumlah(engine)
        return

    if args.reset:
        if not args.yes and input("Ini MENGOSONGKAN tabel data (klaim, peserta, hasil, keputusan, dll). Ketik YA: ") != "YA":
            sys.exit("Dibatalkan.")
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {', '.join(TABEL_RESET)} RESTART IDENTITY CASCADE"))
        print("Tabel dikosongkan.")

    for tabel, f, kolom, kunci, tgl in TABEL:
        upsert(engine, tabel, kolom, kunci, ambil_baris(tabel, f, kolom, tgl))
    muat_tabel_kecil(engine)
    print("\nSelesai. Verifikasi: python -m data.load_to_supabase --cek")


if __name__ == "__main__":
    main()