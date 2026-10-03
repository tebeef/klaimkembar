import os
import sys
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()


def ambil_url_database() -> str:
    """Mengambil DATABASE_URL dan menyesuaikan awalannya untuk psycopg 3."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL belum diisi. Isi di berkas .env (lokal) "
            "atau di environment variable (hosting)."
        )
    # SQLAlchemy memakai driver sesuai awalan; kita ingin psycopg 3.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Membuat satu engine yang dipakai bersama oleh seluruh aplikasi."""
    return create_engine(
        ambil_url_database(),
        pool_size=3,          # paket gratis punya batas koneksi, jadi kolam dibuat kecil
        max_overflow=2,
        pool_pre_ping=True,   # cek koneksi sebelum dipakai (menangani koneksi yang diputus)
        pool_recycle=300,     # daur ulang koneksi tiap 5 menit
    )


def cek_koneksi() -> dict:
    """Menjalankan beberapa query sederhana untuk memastikan koneksi hidup."""
    with get_engine().connect() as conn:
        nama_db = conn.execute(text("select current_database()")).scalar_one()
        waktu = conn.execute(text("select now()")).scalar_one()
        versi = conn.execute(text("select version()")).scalar_one()
    return {"database": nama_db, "waktu_server": waktu, "versi": versi}


def daftar_objek_public() -> list[tuple[str, str]]:
    """Mendaftar tabel dan view di schema public (untuk memeriksa skema)."""
    with get_engine().connect() as conn:
        baris = conn.execute(
            text(
                "select table_name, table_type "
                "from information_schema.tables "
                "where table_schema = 'public' "
                "order by table_type, table_name"
            )
        ).all()
    return [(b[0], b[1]) for b in baris]


def _petunjuk_error(pesan: str) -> str:
    """Memberi saran singkat berdasarkan isi pesan error yang umum."""
    p = pesan.lower()
    if "could not translate host name" in p or "network is unreachable" in p:
        return ("Host tidak terjangkau. Pastikan memakai string Session pooler "
                "(host berakhiran pooler.supabase.com), bukan Direct connection.")
    if "tenant or user not found" in p:
        return ("Username atau region tidak cocok. Username harus berbentuk "
                "postgres.<project-ref>; salin ulang string dari dashboard.")
    if "password authentication failed" in p:
        return ("Password salah, atau mengandung karakter khusus yang belum "
                "di-URL-encode. Cara termudah: reset password menjadi huruf dan angka saja.")
    if "timeout" in p or "timed out" in p:
        return "Koneksi kehabisan waktu. Cek koneksi internet dan status proyek di dashboard."
    return "Periksa DATABASE_URL di .env dan status proyek Supabase."


if __name__ == "__main__":
    try:
        info = cek_koneksi()
    except Exception as e:  # noqa: BLE001 - tujuan skrip ini memang menampilkan error apa pun
        print("GAGAL terhubung ke database.")
        print("Jenis error :", type(e).__name__)
        print("Pesan       :", str(e).splitlines()[0] if str(e) else "(kosong)")
        print("Saran       :", _petunjuk_error(str(e)))
        sys.exit(1)

    print("Koneksi berhasil.")
    print("Database     :", info["database"])
    print("Waktu server :", info["waktu_server"])
    print("Versi        :", info["versi"])

    objek = daftar_objek_public()
    if not objek:
        print("Objek di schema public: (belum ada)")
    else:
        print(f"Objek di schema public ({len(objek)}):")
        for nama, jenis in objek:
            print(f"  - {nama} ({jenis})")