"""cards.py - header halaman, kartu metrik, kotak alasan, dan pemformat angka."""
import html
import streamlit as st
import config as C

def fmt_angka(n):
    return f"{int(n):,}".replace(",", ".")

def fmt_rupiah(n):
    return "Rp" + fmt_angka(n)

def fmt_rupiah_ringkas(n):
    n = float(n)
    if n >= 1e9:
        return f"Rp{n / 1e9:.2f} miliar".replace(".", ",")
    if n >= 1e6:
        return f"Rp{n / 1e6:.1f} juta".replace(".", ",")
    return fmt_rupiah(n)

def header_halaman(judul, subjudul=None):
    sub = f"<p>{html.escape(subjudul)}</p>" if subjudul else ""
    st.markdown(f"<div class='kk-header'><h1>{html.escape(judul)}</h1>{sub}</div>", unsafe_allow_html=True)

def html_kartu(judul, nilai, keterangan="", aksen="hijau"):
    warna = C.WARNA.get(aksen, aksen)
    return (f"<div class='kk-card' style='border-top-color:{warna}'>"
            f"<div class='kk-card-judul'>{html.escape(str(judul))}</div>"
            f"<div class='kk-card-nilai'>{html.escape(str(nilai))}</div>"
            f"<div class='kk-card-ket'>{html.escape(str(keterangan))}</div></div>")

def kartu_metrik(judul, nilai, keterangan="", aksen="hijau"):
    st.markdown(html_kartu(judul, nilai, keterangan, aksen), unsafe_allow_html=True)

def kotak_alasan(teks, judul="Alasan sistem", gaya=""):
    """gaya: '' (biru) atau 'lolos' (hijau)."""
    st.markdown(f"<div class='kk-alasan {gaya}'><div class='kk-alasan-judul'>{html.escape(judul)}</div>"
                f"<div class='kk-alasan-isi'>{html.escape(str(teks))}</div></div>", unsafe_allow_html=True)