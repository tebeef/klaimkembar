"""Riwayat: keputusan verifikator dan audit log, dengan filter."""
import json
import pandas as pd
import streamlit as st
import config as C
import db
from components.cards import header_halaman
from components.pickers import nama_tampil

def format_waktu(seri):
    """Waktu ke zona Asia/Jakarta (WIB); bila gagal, tampilkan apa adanya (UTC)."""
    w = pd.to_datetime(seri, utc=True, errors="coerce")
    try:
        w = w.dt.tz_convert("Asia/Jakarta")
    except Exception:
        pass
    return w.dt.strftime("%d/%m/%Y %H:%M")

header_halaman("Riwayat", "Keputusan verifikator dan jejak audit seluruh perubahan.")
tab_keputusan, tab_audit = st.tabs(["Keputusan verifikator", "Audit log"])

with tab_keputusan:
    rw = db.muat_riwayat()
    if rw.empty:
        st.info("Belum ada keputusan yang tersimpan.")
    else:
        c1, c2, c3 = st.columns(3)
        ver = c1.multiselect("Verifikator", sorted(rw["nama_verifikator"].dropna().unique()), key="rw_ver", placeholder="Semua")
        kep = c2.multiselect("Keputusan", list(C.LABEL_KEPUTUSAN.values()), key="rw_kep", placeholder="Semua")
        cari = c3.text_input("Cari klaim atau nama peserta", key="rw_cari")
        d = rw.copy()
        d["keputusan_label"] = d["keputusan"].map(C.LABEL_KEPUTUSAN).fillna(d["keputusan"])
        if ver:
            d = d[d["nama_verifikator"].isin(ver)]
        if kep:
            d = d[d["keputusan_label"].isin(kep)]
        if cari.strip():
            q = cari.strip()
            d = d[d["id_klaim"].astype(str).str.contains(q, case=False, regex=False)
                  | d["nama_peserta"].fillna("").str.contains(q, case=False, regex=False)]
        tampil = pd.DataFrame({
            "Waktu": format_waktu(d["waktu"]), "Klaim": d["id_klaim"],
            "Peserta": d["nama_peserta"].fillna("").map(nama_tampil),
            "Verifikator": d["nama_verifikator"], "Keputusan": d["keputusan_label"], "Catatan": d["catatan"],
        })
        st.caption(f"{len(tampil)} keputusan")
        st.dataframe(tampil, hide_index=True, width="stretch")

with tab_audit:
    au = db.muat_audit()
    if au.empty:
        st.info("Belum ada catatan audit.")
    else:
        a1, a2 = st.columns(2)
        aksi = a1.multiselect("Aksi", sorted(au["aksi"].dropna().unique()), key="au_aksi", placeholder="Semua")
        ver_a = a2.multiselect("Verifikator", sorted(au["nama_verifikator"].dropna().unique()), key="au_ver", placeholder="Semua")
        d = au.copy()
        if aksi:
            d = d[d["aksi"].isin(aksi)]
        if ver_a:
            d = d[d["nama_verifikator"].isin(ver_a)]
        tampil = pd.DataFrame({
            "Waktu": format_waktu(d["waktu"]), "Verifikator": d["nama_verifikator"], "Aksi": d["aksi"],
            "Klaim": d["id_klaim"],
            "Detail": d["detail"].map(lambda x: x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, default=str)),
        })
        st.caption(f"{len(tampil)} catatan (maksimal 2.000 terbaru)")
        st.dataframe(tampil, hide_index=True, width="stretch")