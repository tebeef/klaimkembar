"""Layar 2 - Daftar Prioritas: tabel terurut skor tertinggi, bar skor berwarna, pencarian nama, tombol Lihat detail."""
import html
import math
import streamlit as st
import config as C
import db
from components.badges import badge_jenis, badge_status, bar_skor
from components.cards import header_halaman, fmt_angka, fmt_rupiah
from components.pickers import filter_periode, filter_samping, nama_tampil

header_halaman("Daftar Prioritas", "Klaim berisiko diurutkan dari skor tertinggi. Pilih 'Lihat detail' untuk membandingkan dua klaim.")
df = db.muat_klaim()
ambang = db.muat_parameter_aktif()["ambang_ditandai"]

utama, samping = st.columns([3.8, 1], gap="large")
with samping:
    df_periode, _ = filter_periode(df, "dp")
    f = filter_samping(df_periode, "dp", skor_awal=int(ambang), df_opsi=df)
with utama:
    cari = st.text_input("Cari berdasarkan nama peserta", key="dp_cari", placeholder="mis. bud (juga bisa ID klaim atau ID peserta)")
    data = f["hasil"]
    if cari.strip():
        q = cari.strip()
        data = data[data["nama_peserta"].str.contains(q, case=False, regex=False)
                    | data["id_klaim"].str.contains(q, case=False, regex=False)
                    | data["id_peserta_samaran"].str.contains(q, case=False, regex=False)]
    data = data.sort_values(["skor_risiko", "tanggal_masuk"], ascending=[False, False])
    total = len(data)
    
    if total == 0:
        st.info("Tidak ada klaim yang cocok. Turunkan batas bawah rentang skor di panel filter untuk melihat klaim berskor rendah.")
        st.stop()
        
    n_hal = max(1, math.ceil(total / C.BARIS_PER_HALAMAN))
    if st.session_state.get("dp_hal", 1) > n_hal:
        st.session_state["dp_hal"] = 1
        
    atas_kiri, atas_kanan = st.columns([3, 1], vertical_alignment="bottom")
    with atas_kanan:
        hal = st.number_input("Halaman", min_value=1, max_value=n_hal, value=1, step=1, key="dp_hal")
    awal = (hal - 1) * C.BARIS_PER_HALAMAN
    potong = data.iloc[awal:awal + C.BARIS_PER_HALAMAN]
    
    with atas_kiri:
        st.caption(f"Menampilkan {awal + 1}–{awal + len(potong)} dari {fmt_angka(total)} klaim · halaman {hal}/{n_hal}")
        
    LEBAR = [0.85, 1.75, 1.75, 0.95, 0.8, 1.1, 1.45, 1.55, 1.15, 0.95]
    JUDUL = ["ID klaim", "Peserta", "Faskes", "Tanggal", "Diagnosis", "Nilai", "Jenis indikasi", "Skor", "Status", ""]
    
    with st.container(key="tabel_prioritas"):
        for c, j in zip(st.columns(LEBAR), JUDUL):
            c.markdown(f"<div class='kk-th'>{j}</div>", unsafe_allow_html=True)
        for r in potong.itertuples(index=False):
            c = st.columns(LEBAR)
            c[0].markdown(f"<div class='kk-td kk-mono'>{html.escape(r.id_klaim)}</div>", unsafe_allow_html=True)
            c[1].markdown(f"<div class='kk-td'>{html.escape(nama_tampil(r.nama_peserta))}</div>"
                          f"<div class='kk-sub'>{html.escape(r.id_peserta_samaran)}</div>", unsafe_allow_html=True)
            c[2].markdown(f"<div class='kk-td'>{html.escape(r.nama_faskes)}</div>"
                          f"<div class='kk-sub'>{html.escape(r.kota)}</div>", unsafe_allow_html=True)
            c[3].markdown(f"<div class='kk-td'>{r.tanggal_masuk:%d/%m/%Y}</div>", unsafe_allow_html=True)
            c[4].markdown(f"<div class='kk-td'>{html.escape(r.kode_diagnosis)}</div>"
                          f"<div class='kk-sub'>{html.escape(r.kode_tindakan)}</div>", unsafe_allow_html=True)
            c[5].markdown(f"<div class='kk-td'>{fmt_rupiah(r.nilai_klaim)}</div>", unsafe_allow_html=True)
            c[6].markdown(badge_jenis(r.jenis_indikasi), unsafe_allow_html=True)
            c[7].markdown(bar_skor(r.skor_risiko), unsafe_allow_html=True)
            c[8].markdown(badge_status(r.status), unsafe_allow_html=True)
            if c[9].button("Lihat detail", key=f"lihat_{r.id_klaim}"):
                st.session_state["buka_klaim"] = r.id_klaim
                st.switch_page("views/perbandingan.py")
    st.caption(C.CATATAN_INDIKASI)