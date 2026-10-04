"""app.py - entry point KlaimKembar: konfigurasi halaman, navigasi, sidebar, dan CSS."""
import html
import streamlit as st
import config as C
import db
from components.styles import pasang_css

st.set_page_config(page_title=f"{C.APP_NAMA} | Deteksi Klaim Kembar JKN", layout="wide",
                   initial_sidebar_state="expanded")
pasang_css()

HALAMAN = [
    st.Page("views/ringkasan.py", title="Ringkasan", default=True),
    st.Page("views/daftar_prioritas.py", title="Daftar Prioritas", url_path="prioritas"),
    st.Page("views/perbandingan.py", title="Detail & Perbandingan", url_path="perbandingan"),
    st.Page("views/pindai_klaim.py", title="Pindai Klaim Baru", url_path="pindai"),
    st.Page("views/evaluasi.py", title="Evaluasi Model", url_path="evaluasi"),
    st.Page("views/riwayat.py", title="Riwayat", url_path="riwayat"),
    st.Page("views/pengaturan.py", title="Pengaturan", url_path="pengaturan"),
]
pg = st.navigation(HALAMAN, position="hidden")      # navigasi dibuat manual di sidebar agar urutannya terkontrol

try:
    verifikator = db.muat_verifikator()
except Exception as e:                               # database tidak terjangkau
    st.error("Tidak dapat terhubung ke database. Periksa DATABASE_URL dan koneksi internet.")
    st.caption(str(e)[:300])
    st.stop()

with st.sidebar:
    st.markdown(f"<div class='kk-logo'><span class='kk-logo-a'>Klaim</span><span class='kk-logo-b'>Kembar</span></div>"
                f"<div class='kk-tagar'>{html.escape(C.APP_TAGAR)}</div>", unsafe_allow_html=True)
    for h in HALAMAN:
        st.page_link(h)
    st.divider()
    nama_by = {r["id_verifikator"]: f"{r['nama_verifikator']} ({r['peran']})" for _, r in verifikator.iterrows()}
    st.selectbox("Masuk sebagai", list(nama_by), key="id_verifikator", format_func=lambda i: nama_by[i])
    st.caption("Identitas level prototipe untuk log audit, bukan autentikasi sungguhan.")
    st.toggle("Mode privasi (samarkan nama)", value=True, key="mode_privasi",
              help="Nama peserta ditampilkan samar, mis. 'Budi S*****'. Aktifkan saat demo.")
    st.markdown(f"<div class='kk-banner'>{html.escape(C.BANNER_SINTETIS)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kk-footer'>{html.escape(C.APP_TIM)}</div>", unsafe_allow_html=True)

pg.run()