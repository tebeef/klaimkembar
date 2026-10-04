import pandas as pd
from sqlalchemy import text
from engine.rules import jalankan_rules
from engine.similarity import jalankan_kemiripan
from engine.scoring import gabung_dan_skoring
import config as C

KOLOM_KLAIM = ["id_klaim", "no_episode", "id_peserta_samaran", "id_faskes", "tanggal_masuk", "tanggal_keluar", "periode_pengajuan", "kode_diagnosis", "kode_tindakan", "kode_inacbg", "nilai_klaim", "teks_resume_medis"]

def muat_parameter(engine):
    with engine.connect() as conn:
        try:
            db_params = dict(conn.execute(text("SELECT kunci, nilai FROM pengaturan")).fetchall())
        except Exception:
            db_params = {}
    return {
        "ambang_ditandai": float(db_params.get("ambang_ditandai", C.AMBANG_DITANDAI)),
        "jendela_r3_hari": int(db_params.get("jendela_r3_hari", C.JENDELA_R3_HARI)),
        "ambang_cosine_tinjau": float(db_params.get("ambang_cosine_tinjau", C.COSINE_TINJAU)),
        "ambang_cosine_kuat": float(db_params.get("ambang_cosine_kuat", C.COSINE_KUAT)),
    }

def baca_klaim(engine):
    with engine.connect() as conn:
        df = pd.read_sql_query(text("SELECT * FROM klaim"), conn)
    for col in ["tanggal_masuk", "tanggal_keluar"]:
        df[col] = pd.to_datetime(df[col])
    return df

def jalankan_deteksi(df_klaim, df_pengecualian, params):
    r_hasil = jalankan_rules(df_klaim, df_pengecualian, params)
    c_hasil = jalankan_kemiripan(df_klaim, params)
    return gabung_dan_skoring(r_hasil, c_hasil, params)

def simpan_hasil(engine, df_hasil):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM hasil_deteksi"))
        if not df_hasil.empty:
            df_hasil.to_sql("hasil_deteksi", con=conn, if_exists="append", index=False)