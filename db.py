"""
db.py - koneksi SQLAlchemy ke Supabase, fungsi baca/tulis, dan cache untuk aplikasi Streamlit.
Kredensial hanya dari .env (lokal) atau environment variable/secrets platform hosting.
"""
import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import config as C

# ----------------------------------------------------------------------
# Koneksi
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_engine():
    """Satu engine untuk seluruh sesi aplikasi (pool kecil, hemat memori)."""
    load_dotenv(C.ROOT_DIR / ".env")
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        try:
            url = str(st.secrets["DATABASE_URL"]).strip()
        except Exception:
            url = ""
    if not url:
        st.error("DATABASE_URL belum diisi (.env lokal atau environment variable di hosting).")
        st.stop()
    for awal in ("postgresql://", "postgres://"):
        if url.startswith(awal):
            url = "postgresql+psycopg://" + url[len(awal):]
    return create_engine(url, connect_args={"prepare_threshold": None}, pool_size=3, max_overflow=2,
                         pool_pre_ping=True, pool_recycle=1800)

def _baca(sql, params=None):
    with get_engine().connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)

def _py(x):
    """Ubah tipe numpy/NaN menjadi tipe Python murni agar aman untuk driver."""
    if x is None:
        return None
    if hasattr(x, "item"):
        x = x.item()
    if isinstance(x, float) and x != x:
        return None
    return x

def bersihkan_cache():
    st.cache_data.clear()

# ----------------------------------------------------------------------
# Pembacaan (di-cache)
# ----------------------------------------------------------------------
SQL_KLAIM = """
SELECT k.id_klaim, k.no_episode, k.id_peserta_samaran, p.nama_peserta, k.id_faskes, f.nama_faskes, f.kota,
       k.tanggal_masuk, k.tanggal_keluar, k.periode_pengajuan, k.kode_diagnosis, k.kode_tindakan,
       k.kode_inacbg, k.nilai_klaim, k.teks_resume_medis,
       COALESCE(h.skor_risiko, 0) AS skor_risiko, h.jenis_indikasi, h.kode_aturan,
       h.kemiripan_teks, h.kemiripan_kode, h.id_klaim_pasangan, h.alasan,
       kt.keputusan AS status_raw
FROM klaim k
JOIN peserta p ON p.id_peserta_samaran = k.id_peserta_samaran
JOIN faskes f ON f.id_faskes = k.id_faskes
LEFT JOIN hasil_deteksi h ON h.id_klaim = k.id_klaim
LEFT JOIN (SELECT DISTINCT ON (id_klaim) id_klaim, keputusan
           FROM keputusan ORDER BY id_klaim, waktu DESC) kt ON kt.id_klaim = k.id_klaim
"""

@st.cache_data(ttl=C.TTL_CACHE_DETIK, show_spinner="Memuat data klaim...")
def muat_klaim():
    """Semua klaim + peserta + faskes + hasil deteksi + status terakhir."""
    df = _baca(SQL_KLAIM)
    for k in ("tanggal_masuk", "tanggal_keluar"):
        df[k] = pd.to_datetime(df[k])
    for k in ("skor_risiko", "nilai_klaim", "kemiripan_teks", "kemiripan_kode"):
        df[k] = pd.to_numeric(df[k], errors="coerce")
    df["skor_risiko"] = df["skor_risiko"].fillna(0).astype(int)
    df["status"] = df["status_raw"].map(C.LABEL_KEPUTUSAN).fillna(C.STATUS_BELUM)
    df["kelompok_dx"] = df["kode_diagnosis"].astype(str).str[:3]
    return df

@st.cache_data(ttl=C.TTL_CACHE_DETIK)
def muat_faskes():
    return _baca("SELECT id_faskes, nama_faskes, jenis_faskes, kota FROM faskes ORDER BY nama_faskes")

@st.cache_data(ttl=C.TTL_CACHE_DETIK)
def muat_peserta():
    return _baca("SELECT id_peserta_samaran, nama_peserta FROM peserta ORDER BY nama_peserta")

@st.cache_data(ttl=C.TTL_CACHE_DETIK)
def muat_verifikator():
    return _baca("SELECT id_verifikator, nama_verifikator, peran FROM verifikator ORDER BY id_verifikator")

@st.cache_data(ttl=C.TTL_CACHE_DETIK)
def muat_pengecualian_df():
    return _baca("SELECT kode_diagnosis, kode_tindakan, keterangan FROM pengecualian_layanan ORDER BY kode_diagnosis")

@st.cache_data(ttl=C.TTL_CACHE_DETIK)
def muat_daftar_pengecualian():
    from engine.exceptions import muat_pengecualian
    return muat_pengecualian(get_engine())

@st.cache_data(ttl=C.TTL_CACHE_DETIK)
def muat_parameter_aktif():
    """Parameter deteksi: default config ditimpa nilai di tabel pengaturan."""
    from engine.pipeline import muat_parameter
    return muat_parameter(get_engine())

@st.cache_data(ttl=60)
def muat_riwayat():
    return _baca("""
        SELECT kt.id, kt.waktu, kt.id_klaim, p.nama_peserta, p.id_peserta_samaran,
               v.nama_verifikator, kt.keputusan, kt.catatan
        FROM keputusan kt
        LEFT JOIN klaim k ON k.id_klaim = kt.id_klaim
        LEFT JOIN peserta p ON p.id_peserta_samaran = k.id_peserta_samaran
        LEFT JOIN verifikator v ON v.id_verifikator = kt.id_verifikator
        ORDER BY kt.waktu DESC""")

@st.cache_data(ttl=60)
def muat_audit():
    return _baca("""
        SELECT a.id, a.waktu, v.nama_verifikator, a.aksi, a.id_klaim, a.detail
        FROM audit_log a LEFT JOIN verifikator v ON v.id_verifikator = a.id_verifikator
        ORDER BY a.waktu DESC LIMIT 2000""")

# ----------------------------------------------------------------------
# Penulisan
# ----------------------------------------------------------------------
def _audit(conn, aksi, id_verifikator, id_klaim=None, detail=None):
    conn.execute(
        text("INSERT INTO audit_log (waktu, id_verifikator, aksi, id_klaim, detail) "
             "VALUES (now(), :v, :a, :k, CAST(:d AS jsonb))"),
        {"v": id_verifikator, "a": aksi, "k": id_klaim, "d": json.dumps(detail or {}, ensure_ascii=False, default=str)})

def simpan_keputusan(id_klaim, id_verifikator, keputusan, catatan):
    """Simpan keputusan + audit log. Status klaim mengikuti keputusan terakhir."""
    with get_engine().begin() as conn:
        conn.execute(
            text("INSERT INTO keputusan (id_klaim, id_verifikator, keputusan, catatan, waktu) "
                 "VALUES (:k, :v, :d, :c, now())"),
            {"k": id_klaim, "v": id_verifikator, "d": keputusan, "c": catatan})
        _audit(conn, f"keputusan_{keputusan}", id_verifikator, id_klaim, {"keputusan": keputusan, "catatan": catatan})
    bersihkan_cache()

def simpan_pengaturan(nilai_baru, id_verifikator):
    """Simpan pengaturan (dict kunci -> nilai) dan catat perubahan di audit log."""
    with get_engine().begin() as conn:
        lama = dict(conn.execute(text("SELECT kunci, nilai FROM pengaturan")).fetchall())
        for k, v in nilai_baru.items():
            conn.execute(
                text("INSERT INTO pengaturan (kunci, nilai) VALUES (:k, :v) "
                     "ON CONFLICT (kunci) DO UPDATE SET nilai = EXCLUDED.nilai"),
                {"k": k, "v": str(v)})
        _audit(conn, "ubah_pengaturan", id_verifikator, None,
               {"lama": {k: lama.get(k) for k in nilai_baru}, "baru": nilai_baru})
    bersihkan_cache()

def simpan_pengecualian(baris, id_verifikator):
    """Ganti seluruh daftar pengecualian layanan. baris: list (kode_diagnosis, kode_tindakan, keterangan)."""
    with get_engine().begin() as conn:
        lama = conn.execute(text("SELECT kode_diagnosis, kode_tindakan, keterangan FROM pengecualian_layanan")).fetchall()
        conn.execute(text("DELETE FROM pengecualian_layanan"))
        for a, b, c in baris:
            conn.execute(
                text("INSERT INTO pengecualian_layanan (kode_diagnosis, kode_tindakan, keterangan) VALUES (:a, :b, :c)"),
                {"a": a, "b": b, "c": c})
        _audit(conn, "ubah_pengecualian", id_verifikator, None,
               {"lama": [list(r) for r in lama], "baru": [list(r) for r in baris]})
    bersihkan_cache()

def buat_peserta_sintetis(nama, id_verifikator):
    """Tambah peserta sintetis baru dengan ID samaran berikutnya (P-xxxx)."""
    with get_engine().begin() as conn:
        n = conn.execute(text("SELECT COALESCE(MAX(CAST(SUBSTRING(id_peserta_samaran FROM 3) AS INTEGER)), 0) + 1 "
                              "FROM peserta")).scalar()
        id_baru = f"P-{int(n):04d}"
        conn.execute(text("INSERT INTO peserta (id_peserta_samaran, nama_peserta) VALUES (:i, :n)"),
                     {"i": id_baru, "n": nama})
        _audit(conn, "buat_peserta_sintetis", id_verifikator, None, {"id_peserta_samaran": id_baru})
    bersihkan_cache()
    return id_baru

def simpan_klaim_baru(data, hasil, id_verifikator):
    """Simpan klaim hasil Pindai Klaim beserta hasil deteksinya. Mengembalikan id_klaim baru."""
    with get_engine().begin() as conn:
        n = int(conn.execute(text("SELECT COALESCE(MAX(CAST(SUBSTRING(id_klaim FROM 4) AS INTEGER)), 0) + 1 "
                                  "FROM klaim")).scalar())
        id_klaim = f"KK-{n:04d}"
        conn.execute(
            text("INSERT INTO klaim (id_klaim, no_episode, id_peserta_samaran, id_faskes, tanggal_masuk, tanggal_keluar, "
                 "periode_pengajuan, kode_diagnosis, kode_tindakan, kode_inacbg, nilai_klaim, teks_resume_medis) "
                 "VALUES (:id_klaim, :no_episode, :id_peserta, :id_faskes, :masuk, :keluar, :periode, :dx, :tind, "
                 ":inacbg, :nilai, :resume)"),
            {"id_klaim": id_klaim, "no_episode": data.get("no_episode") or f"EP-N{n:07d}",
             "id_peserta": data["id_peserta_samaran"], "id_faskes": data["id_faskes"],
             "masuk": pd.Timestamp(data["tanggal_masuk"]).date(), "keluar": pd.Timestamp(data["tanggal_keluar"]).date(),
             "periode": data["periode_pengajuan"], "dx": data["kode_diagnosis"], "tind": data["kode_tindakan"],
             "inacbg": data["kode_inacbg"], "nilai": _py(data["nilai_klaim"]), "resume": data["teks_resume_medis"]})
        conn.execute(
            text("INSERT INTO hasil_deteksi (id_klaim, skor_risiko, jenis_indikasi, kode_aturan, kemiripan_teks, "
                 "kemiripan_kode, id_klaim_pasangan, alasan, dihitung_pada) "
                 "VALUES (:id_klaim, :skor, :jenis, :aturan, :ktk, :kkd, :pasangan, :alasan, now())"),
            {"id_klaim": id_klaim, "skor": _py(hasil["skor_risiko"]), "jenis": _py(hasil["jenis_indikasi"]),
             "aturan": _py(hasil["kode_aturan"]), "ktk": _py(hasil["kemiripan_teks"]),
             "kkd": _py(hasil["kemiripan_kode"]), "pasangan": _py(hasil["id_klaim_pasangan"]),
             "alasan": _py(hasil["alasan"])})
        _audit(conn, "pindai_klaim_baru", id_verifikator, id_klaim,
               {"skor_risiko": _py(hasil["skor_risiko"]), "jenis_indikasi": _py(hasil["jenis_indikasi"])})
    bersihkan_cache()
    return id_klaim

def hitung_ulang_semua():
    """Jalankan ulang deteksi pada SEMUA klaim dengan parameter terbaru, simpan, bersihkan cache."""
    from engine.pipeline import baca_klaim, jalankan_deteksi, simpan_hasil, muat_parameter
    from engine.exceptions import muat_pengecualian
    eng = get_engine()
    params = muat_parameter(eng)
    hasil = jalankan_deteksi(baca_klaim(eng), muat_pengecualian(eng), params)
    simpan_hasil(eng, hasil)
    bersihkan_cache()
    return len(hasil), int((hasil["skor_risiko"] >= params["ambang_ditandai"]).sum())