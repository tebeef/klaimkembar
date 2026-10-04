"""Evaluasi Model - kerangka sementara; diisi setelah engine/evaluate.py diselaraskan."""
import streamlit as st
from components.cards import header_halaman

header_halaman("Evaluasi Model", "Hasil pada data sintetis (bukti konsep); akurasi pada data nyata belum diketahui.")
st.info("Halaman ini akan menampilkan recall, presisi, tingkat salah tanda, dan uji ambang "
        "setelah disambungkan ke engine/evaluate.py.")