"""Layar 1 - Ringkasan: filter periode, empat kartu metrik, grafik batang klaim ditandai per minggu."""
import altair as alt
import pandas as pd
import streamlit as st
import config as C
import db
from components.cards import header_halaman, kartu_metrik, fmt_angka, fmt_rupiah_ringkas
from components.pickers import filter_periode, filter_samping

df = db.muat_klaim()
ambang = db.muat_parameter_aktif()["ambang_ditandai"]
kiri, kanan = st.columns([3, 1], gap="large", vertical_alignment="bottom")
with kiri:
    header_halaman("Ringkasan", "Klaim yang berpotensi berulang atau dijiplak, dibandingkan lintas faskes dan lintas periode.")
with kanan:
    df_periode, label_periode = filter_periode(df, "rk")
utama, samping = st.columns([3.6, 1], gap="large")
with samping:
    f = filter_samping(df_periode, "rk", skor_awal=0, df_opsi=df)
with utama:
    cakupan, hasil = f["cakupan"], f["hasil"]
    ditandai = hasil[hasil["skor_risiko"] >= ambang]
    ditinjau = ditandai[ditandai["status"] != C.STATUS_BELUM]
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kartu_metrik("Total klaim dipindai", fmt_angka(len(cakupan)), f"Seluruh klaim pada cakupan filter ({label_periode.lower()})", "biru")
    with k2:
        persen = (len(ditandai) / len(cakupan) * 100) if len(cakupan) else 0
        kartu_metrik("Klaim ditandai", fmt_angka(len(ditandai)), f"Skor ≥ {ambang:g} · {persen:.1f}% dari yang dipindai", "hijau")
    with k3:
        kartu_metrik("Estimasi nilai klaim berisiko", fmt_rupiah_ringkas(ditandai["nilai_klaim"].sum()),
                     "Hanya klaim yang masuk belakangan dalam sepasang, agar tidak terhitung ganda", "risiko_tinggi")
    with k4:
        kartu_metrik("Klaim sudah ditinjau", fmt_angka(len(ditinjau)), f"dari {fmt_angka(len(ditandai))} klaim ditandai", "navy")
    
    st.markdown("#### Klaim ditandai per minggu")
    if ditandai.empty:
        st.info("Tidak ada klaim ditandai pada filter ini.")
    else:
        d = ditandai.copy()
        d["minggu"] = d["tanggal_masuk"] - pd.to_timedelta(d["tanggal_masuk"].dt.weekday, unit="D")
        g = d.groupby(["minggu", "jenis_indikasi"]).size().reset_index(name="jumlah")
        urutan = sorted(g["minggu"].unique())
        label_urut = [pd.Timestamp(x).strftime("%d %b") for x in urutan]
        g["label"] = g["minggu"].dt.strftime("%d %b")
        grafik = (
            alt.Chart(g)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=26)
            .encode(
                x=alt.X("label:N", sort=label_urut, title="Minggu (mulai hari Senin)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("jumlah:Q", title="Jumlah klaim ditandai"),
                color=alt.Color("jenis_indikasi:N", title="Jenis indikasi",
                                scale=alt.Scale(domain=list(C.WARNA_JENIS), range=list(C.WARNA_JENIS.values()))),
                tooltip=[alt.Tooltip("label:N", title="Minggu"), alt.Tooltip("jenis_indikasi:N", title="Jenis"),
                         alt.Tooltip("jumlah:Q", title="Jumlah")],
            )
            .properties(height=320)
        )
        st.altair_chart(grafik, width="stretch")
    st.caption(C.CATATAN_INDIKASI)