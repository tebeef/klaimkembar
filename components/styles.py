"""styles.py - CSS kustom (kartu, badge, bar skor, panel, sorotan, tabel). Warna dari config.WARNA."""
import streamlit as st
import config as C

CSS_STATIS = """
.block-container{padding-top:3.5rem;padding-bottom:3rem;max-width:1500px;}
#MainMenu{visibility:hidden;} footer{visibility:hidden;}
/* ---------- Sidebar ---------- */
[data-testid="stSidebar"]{background:#FFFFFF;border-right:1px solid var(--kk-garis);}
.kk-logo{font-size:1.65rem;font-weight:800;letter-spacing:-.02em;line-height:1.1;margin-top:.2rem;}
.kk-logo-a{color:var(--kk-navy);} .kk-logo-b{color:var(--kk-hijau);}
.kk-tagar{font-size:.72rem;font-weight:600;color:var(--kk-biru);margin:.15rem 0 .9rem;letter-spacing:.02em;}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]{border-radius:10px;padding:.5rem .8rem;color:var(--kk-teks);}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover{background:var(--kk-hijau-muda);}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"]{background:var(--kk-hijau);}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] *{color:#FFFFFF !important;font-weight:600;}
.kk-banner{background:var(--kk-hijau-muda);border:1px solid #A7F3D0;color:var(--kk-hijau-tua);border-radius:10px;
  padding:.5rem .7rem;font-size:.78rem;font-weight:500;margin-top:.4rem;}
.kk-footer{font-size:.78rem;color:var(--kk-teks-redup);text-align:center;margin-top:1.2rem;}
/* ---------- Header halaman ---------- */
.kk-header h1{font-size:1.7rem;font-weight:700;color:var(--kk-teks);margin:0;padding:0;letter-spacing:-.01em;}
.kk-header p{margin:.25rem 0 1rem;color:var(--kk-teks-redup);font-size:.95rem;}
/* ---------- Kartu metrik ---------- */
.kk-card{background:#FFFFFF;border:1px solid var(--kk-garis);border-top:4px solid var(--kk-hijau);border-radius:16px;
  padding:1rem 1.15rem;box-shadow:0 1px 3px rgba(15,23,42,.06),0 6px 16px rgba(15,23,42,.04);height:100%;}
.kk-card-judul{font-size:.74rem;color:var(--kk-teks-redup);font-weight:700;text-transform:uppercase;letter-spacing:.04em;}
.kk-card-nilai{font-size:1.85rem;font-weight:700;color:var(--kk-teks);line-height:1.2;margin:.3rem 0 .2rem;}
.kk-card-ket{font-size:.78rem;color:var(--kk-teks-redup);line-height:1.35;}
/* ---------- Badge & bar skor ---------- */
.kk-badge{display:inline-block;border-radius:999px;padding:.12rem .62rem;font-size:.74rem;font-weight:600;white-space:nowrap;}
.kk-skor{display:flex;align-items:center;gap:.5rem;}
.kk-bar{flex:1;height:8px;background:#E2E8F0;border-radius:999px;overflow:hidden;min-width:48px;}
.kk-bar-fill{height:100%;border-radius:999px;}
.kk-bar-num{font-weight:700;font-size:.86rem;min-width:1.9rem;text-align:right;color:var(--kk-teks);}
/* ---------- Tabel Daftar Prioritas ---------- */
.kk-th{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--kk-teks-redup);}
.kk-td{font-size:.86rem;color:var(--kk-teks);line-height:1.3;}
.kk-sub{font-size:.73rem;color:var(--kk-teks-redup);}
.kk-mono{font-family:ui-monospace,Consolas,monospace;font-weight:600;}
.st-key-tabel_prioritas [data-testid="stHorizontalBlock"]{align-items:center;border-bottom:1px solid var(--kk-garis);padding:.45rem .25rem;}
.st-key-tabel_prioritas button{padding:.15rem .6rem;min-height:0;font-size:.78rem;}
/* ---------- Panel perbandingan ---------- */
.kk-panel{background:#FFFFFF;border:1px solid var(--kk-garis);border-radius:16px;padding:1.1rem 1.25rem;
  box-shadow:0 1px 3px rgba(15,23,42,.06),0 6px 16px rgba(15,23,42,.04);height:100%;}
.kk-panel-judul{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--kk-biru);margin-bottom:.7rem;}
.kk-kv{display:grid;grid-template-columns:150px 1fr;gap:.3rem .8rem;font-size:.88rem;margin-bottom:.9rem;}
.kk-kv .k{color:var(--kk-teks-redup);} .kk-kv .v{color:var(--kk-teks);font-weight:500;word-break:break-word;}
.kk-resume{background:var(--kk-latar);border:1px solid var(--kk-garis);border-radius:12px;padding:.85rem 1rem;line-height:1.8;font-size:.92rem;color:var(--kk-teks);}
.kk-resume mark{background:var(--kk-kuning-sorot);color:inherit;padding:.05rem .15rem;border-radius:4px;}
.kk-kosong{color:var(--kk-teks-redup);font-size:.9rem;padding:1.2rem 0;}
/* ---------- Kotak alasan ---------- */
.kk-alasan{background:var(--kk-biru-muda);border:1px solid #BFDBFE;border-left:5px solid var(--kk-biru);border-radius:12px;padding:.9rem 1.1rem;margin:.4rem 0 1rem;}
.kk-alasan.lolos{background:var(--kk-hijau-muda);border-color:#A7F3D0;border-left-color:var(--kk-hijau);}
.kk-alasan-judul{font-size:.74rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--kk-biru);margin-bottom:.25rem;}
.kk-alasan.lolos .kk-alasan-judul{color:var(--kk-hijau-tua);}
.kk-alasan-isi{color:var(--kk-teks);font-size:.96rem;line-height:1.55;}
/* ---------- Tombol keputusan ---------- */
.st-key-btn_setuju button{background:var(--kk-setuju);border-color:var(--kk-setuju);}
.st-key-btn_setuju button *{color:#FFFFFF !important;font-weight:600;}
.st-key-btn_tunda button{background:var(--kk-tunda);border-color:var(--kk-tunda);}
.st-key-btn_tunda button *{color:#1E293B !important;font-weight:600;}
.st-key-btn_tolak button{background:var(--kk-tolak);border-color:var(--kk-tolak);}
.st-key-btn_tolak button *{color:#FFFFFF !important;font-weight:600;}

.stTextInput div[data-baseweb="input"],
.stSelectbox div[data-baseweb="select"],
.stTextArea div[data-baseweb="textarea"],
.stNumberInput div[data-baseweb="input"],
.stDateInput div[data-baseweb="input"] {
    border: 1px solid #CBD5E1 !important; 
    border-radius: 8px !important;
    background-color: #FFFFFF !important;
    box-shadow: none !important;
}

.stTextInput div[data-baseweb="input"]:hover,
.stSelectbox div[data-baseweb="select"]:hover,
.stTextArea div[data-baseweb="textarea"]:hover,
.stNumberInput div[data-baseweb="input"]:hover,
.stDateInput div[data-baseweb="input"]:hover,
.stTextInput div[data-baseweb="input"]:focus-within,
.stSelectbox div[data-baseweb="select"]:focus-within,
.stTextArea div[data-baseweb="textarea"]:focus-within {
    border-color: var(--kk-hijau) !important;
}
"""

def _variabel():
    return ":root{" + "".join(f"--kk-{k.replace('_', '-')}:{v};" for k, v in C.WARNA.items()) + "}"

def pasang_css():
    st.markdown(f"<style>{_variabel()}{CSS_STATIS}</style>", unsafe_allow_html=True)