"""Pindai Klaim Baru: formulir klaim baru, pindai terhadap data yang ada, tampilkan skor/alasan/pasangan, simpan ke antrean."""
import html
import pandas as pd
import streamlit as st
import config as C
import db
from components.badges import badge_jenis
from components.cards import header_halaman, html_kartu, kotak_alasan, fmt_rupiah
from components.highlight import sorot_identik
from components.pickers import pilih_peserta, pilih_faskes, nama_tampil
from engine.pipeline import KOLOM_KLAIM
from engine.scan import scan_claim

ID_PESERTA_BARU = "P-BARU"
header_halaman("Pindai Klaim Baru", "Periksa satu klaim baru terhadap seluruh klaim yang sudah ada sebelum masuk verifikasi.")
df = db.muat_klaim()
idx = df.set_index("id_klaim", drop=False)
params = db.muat_parameter_aktif()
ambang = params["ambang_ditandai"]

# ---------------------------------------------------------------- Formulir
with st.container(border=True):
    st.markdown("**1. Peserta dan faskes**")
    k1, k2 = st.columns(2, gap="large")
    with k1:
        mode_p = st.radio("Peserta", ["Pilih peserta yang ada", "Buat peserta sintetis baru"], horizontal=True, key="pk_mode_peserta")
        if mode_p.startswith("Pilih"):
            id_peserta, nama_baru = pilih_peserta(db.muat_peserta(), "pk_peserta"), None
        else:
            nama_baru = st.text_input("Nama peserta sintetis baru", key="pk_nama_baru", placeholder="Nama fiktif, mis. Sari Wulandari")
            id_peserta = ID_PESERTA_BARU
    with k2:
        id_faskes = pilih_faskes(db.muat_faskes(), "pk_faskes", "Faskes pengirim (pilih berdasarkan nama)")
        
with st.container(border=True):
    st.markdown("**2. Data klaim**")
    c1, c2, c3 = st.columns(3)
    kode_dx = c1.text_input("Kode diagnosis (ICD-10)", value="J18.9", key="pk_dx")
    kode_tind = c2.text_input("Kode tindakan (ICD-9-CM)", value="99.21", key="pk_tind")
    nilai = c3.number_input("Nilai klaim (Rp)", min_value=0, value=2_000_000, step=10_000, key="pk_nilai")
    d1, d2, d3 = st.columns(3)
    tgl_masuk = d1.date_input("Tanggal masuk", value=df["tanggal_masuk"].max().date(), key="pk_masuk")
    tgl_keluar = d2.date_input("Tanggal keluar", value=df["tanggal_masuk"].max().date(), min_value=tgl_masuk, key="pk_keluar")
    no_episode = d3.text_input("Nomor episode (kosongkan untuk dibuat otomatis)", key="pk_episode")
    resume = st.text_area("Teks ringkasan resume medis", height=140, key="pk_resume",
                          placeholder="Contoh: Demam, batuk, terapi antibiotik.")
    st.caption(f"Periode pengajuan otomatis: {tgl_keluar:%Y-%m}. Kelompok INA-CBG diambil dari klaim lain dengan kode yang sama bila ada.")

if st.button("Pindai", type="primary", key="pk_pindai"):
    dx, tind = kode_dx.strip().upper(), kode_tind.strip().upper()
    if not id_peserta or (mode_p.startswith("Buat") and not (nama_baru or "").strip()):
        st.error("Pilih peserta, atau isi nama peserta sintetis baru.")
    elif not dx or not tind or not resume.strip() or nilai <= 0:
        st.error("Kode diagnosis, kode tindakan, nilai klaim, dan resume wajib diisi.")
    else:
        serupa = df[(df["kode_diagnosis"] == dx) & (df["kode_tindakan"] == tind)]["kode_inacbg"].dropna()
        baru = {
            "id_peserta_samaran": id_peserta, "id_faskes": id_faskes, "no_episode": no_episode.strip(),
            "tanggal_masuk": pd.Timestamp(tgl_masuk), "tanggal_keluar": pd.Timestamp(tgl_keluar),
            "periode_pengajuan": f"{tgl_keluar:%Y-%m}", "kode_diagnosis": dx, "kode_tindakan": tind,
            "kode_inacbg": serupa.mode().iloc[0] if not serupa.empty else "-",
            "nilai_klaim": int(nilai), "teks_resume_medis": resume.strip(),
        }
        with st.spinner("Memindai terhadap klaim yang ada..."):
            hasil = scan_claim(baru, df[KOLOM_KLAIM], db.muat_daftar_pengecualian(), params)
        st.session_state["pk_hasil"] = {"hasil": hasil, "baru": baru, "nama_baru": (nama_baru or "").strip()}
        st.session_state.pop("pk_tersimpan", None)

# ---------------------------------------------------------------- Hasil
data = st.session_state.get("pk_hasil")
if data:
    h, baru = data["hasil"], data["baru"]
    skor = int(h["skor_risiko"])
    st.markdown("### Hasil pemindaian")
    if skor < ambang:
        kotak_alasan(f"Skor risiko {skor} (di bawah ambang {ambang:g}). Lolos, lanjut verifikasi biasa.",
                     "Lolos", gaya="lolos")
    else:
        kotak_alasan(h["alasan"], f"Ditandai · skor risiko {skor}")
        
    m1, m2, m3 = st.columns(3)
    m1.markdown(html_kartu("Skor risiko", skor, "Skala 0–100 · indikasi, bukan bukti", "risiko_tinggi" if skor >= ambang else "hijau"), unsafe_allow_html=True)
    m2.markdown(f"<div class='kk-card'><div class='kk-card-judul'>Jenis indikasi</div><div class='kk-card-nilai' style='font-size:1.2rem'>{badge_jenis(h['jenis_indikasi'])}</div>"
                f"<div class='kk-card-ket'>Aturan: {html.escape(str(h['kode_aturan'] or '-'))}</div></div>", unsafe_allow_html=True)
    m3.markdown(html_kartu("Klaim pasangan", h["id_klaim_pasangan"] or "-", "Klaim yang paling mirip di data yang ada", "biru"), unsafe_allow_html=True)
    
    pasangan = h["id_klaim_pasangan"]
    if isinstance(pasangan, str) and pasangan in idx.index:
        p = idx.loc[pasangan]
        st.markdown("#### Perbandingan dengan klaim pasangan")
        sa, sb = sorot_identik(baru["teks_resume_medis"], p["teks_resume_medis"])
        def mini_panel(judul, kv, resume_html):
            isi = "".join(f"<div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(v))}</div>" for k, v in kv)
            return (f"<div class='kk-panel'><div class='kk-panel-judul'>{html.escape(judul)}</div>"
                    f"<div class='kk-kv'>{isi}</div><div class='kk-resume'>{resume_html}</div></div>")
        q1, q2 = st.columns(2, gap="large")
        with q1:
            st.markdown(mini_panel("Klaim baru (belum disimpan)", [
                ("Diagnosis / Tindakan", f"{baru['kode_diagnosis']} / {baru['kode_tindakan']}"),
                ("Faskes", id_faskes),
                ("Tanggal masuk", f"{baru['tanggal_masuk']:%d/%m/%Y}"),
                ("Nilai klaim", fmt_rupiah(baru["nilai_klaim"])),
            ], sa), unsafe_allow_html=True)
        with q2:
            st.markdown(mini_panel(f"Klaim pasangan {pasangan}", [
                ("Peserta", f"{nama_tampil(p['nama_peserta'])} ({p['id_peserta_samaran']})"),
                ("Faskes", p["nama_faskes"]),
                ("Tanggal masuk", f"{p['tanggal_masuk']:%d/%m/%Y}"),
                ("Nilai klaim", fmt_rupiah(p["nilai_klaim"])),
            ], sb), unsafe_allow_html=True)
            
    # ------------------------------------------------------------ Simpan ke antrean
    st.markdown("### Simpan ke antrean")
    tersimpan = st.session_state.get("pk_tersimpan")
    if tersimpan:
        st.success(f"Klaim tersimpan sebagai {tersimpan} dan masuk antrean verifikasi.")
        if st.button("Buka di Detail & Perbandingan", key="pk_buka"):
            st.session_state["buka_klaim"] = tersimpan
            st.switch_page("views/perbandingan.py")
    else:
        st.caption("Menyimpan menambahkan klaim ini ke tabel klaim beserta hasil pemindaian, dan dicatat di audit log.")
        if st.button("Simpan ke antrean verifikasi", key="pk_simpan"):
            id_ver = st.session_state.get("id_verifikator")
            if not id_ver:
                st.error("Pilih nama pada 'Masuk sebagai' di sidebar terlebih dahulu.")
            else:
                data_simpan = dict(baru)
                if baru["id_peserta_samaran"] == ID_PESERTA_BARU:
                    data_simpan["id_peserta_samaran"] = db.buat_peserta_sintetis(data["nama_baru"], id_ver)
                id_klaim = db.simpan_klaim_baru(data_simpan, h, id_ver)
                st.session_state["pk_tersimpan"] = id_klaim
                st.rerun()
    st.caption(C.CATATAN_INDIKASI)