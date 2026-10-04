"""Pengaturan: ambang tanda, ambang cosine, jendela R3, daftar pengecualian layanan.
Perubahan dicatat di audit log dan memicu perhitungan ulang seluruh klaim."""
import pandas as pd
import streamlit as st
import db
from components.cards import header_halaman, fmt_angka

def _s(x):
    return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x).strip()

header_halaman("Pengaturan", "Ambang bersifat rancangan awal dan dikalibrasi saat pengujian. Setiap perubahan dicatat di audit log.")
p = db.muat_parameter_aktif()

with st.container(border=True):
    st.markdown("**Ambang deteksi**")
    a1, a2 = st.columns(2, gap="large")
    ambang = a1.slider("Ambang klaim ditandai (skor)", 0, 100, int(p["ambang_ditandai"]), key="pg_ambang",
                       help="Diturunkan untuk pemeriksaan lebih luas, dinaikkan untuk fokus pada kasus paling mencurigakan.")
    jendela = a2.slider("Jendela R3 (hari)", 1, 30, int(p["jendela_r3_hari"]), key="pg_r3",
                        help="Selisih tanggal masuk maksimum untuk klaim berulang pada peserta, diagnosis, dan tindakan yang sama.")
    cos_tinjau = a1.slider("Ambang cosine: perlu ditinjau", 0.50, 1.00, float(p["ambang_cosine_tinjau"]), 0.01, key="pg_cos_tinjau")
    cos_kuat = a2.slider("Ambang cosine: indikasi kuat", 0.50, 1.00, float(p["ambang_cosine_kuat"]), 0.01, key="pg_cos_kuat")
    
with st.container(border=True):
    st.markdown("**Pengecualian layanan rutin yang sah**")
    st.caption("Cuci darah, kemoterapi terjadwal, dan kontrol rutin penyakit kronis tidak diberi skor Berulang (R3 dan R4). "
               "Kosongkan kode tindakan untuk berlaku pada semua tindakan diagnosis itu.")
    awal = db.muat_pengecualian_df()
    edit = st.data_editor(
        awal, num_rows="dynamic", hide_index=True, width="stretch", key="pg_pengecualian",
        column_config={
            "kode_diagnosis": st.column_config.TextColumn("Kode diagnosis (ICD-10)", required=True),
            "kode_tindakan": st.column_config.TextColumn("Kode tindakan (ICD-9-CM)"),
            "keterangan": st.column_config.TextColumn("Keterangan"),
        })

if st.button("Simpan & hitung ulang", type="primary", key="pg_simpan"):
    id_ver = st.session_state.get("id_verifikator")
    if not id_ver:
        st.error("Pilih nama pada 'Masuk sebagai' di sidebar terlebih dahulu.")
    elif cos_tinjau >= cos_kuat:
        st.error("Ambang 'perlu ditinjau' harus lebih rendah daripada ambang 'indikasi kuat'.")
    else:
        baris = [(_s(r["kode_diagnosis"]).upper(), _s(r["kode_tindakan"]).upper(), _s(r["keterangan"]))
                 for _, r in edit.iterrows() if _s(r["kode_diagnosis"])]
        lama_penuh = {(_s(r["kode_diagnosis"]).upper(), _s(r["kode_tindakan"]).upper(), _s(r["keterangan"]))
                      for _, r in awal.iterrows()}
        pasangan_lama = {(a, b) for a, b, _ in lama_penuh}
        pasangan_baru = {(a, b) for a, b, _ in baris}
        baru = {"ambang_ditandai": str(ambang), "jendela_r3_hari": str(jendela),
                "ambang_cosine_tinjau": f"{cos_tinjau:.2f}", "ambang_cosine_kuat": f"{cos_kuat:.2f}"}
        berubah = [k for k in baru if abs(float(baru[k]) - float(p[k])) > 1e-9]
        daftar_berubah = set(baris) != lama_penuh
        if not berubah and not daftar_berubah:
            st.info("Tidak ada perubahan untuk disimpan.")
        else:
            if berubah:
                db.simpan_pengaturan(baru, id_ver)
            if daftar_berubah:
                db.simpan_pengecualian(baris, id_ver)
            perlu_hitung = bool(set(berubah) - {"ambang_ditandai"}) or pasangan_lama != pasangan_baru
            if perlu_hitung:
                with st.spinner("Menghitung ulang seluruh klaim, mohon tunggu..."):
                    n, t = db.hitung_ulang_semua()
                st.success(f"Tersimpan dan tercatat di audit log. {fmt_angka(n)} klaim dihitung ulang; {fmt_angka(t)} ditandai.")
            else:
                st.success("Tersimpan dan tercatat di audit log. Ambang tanda berlaku langsung tanpa hitung ulang.")