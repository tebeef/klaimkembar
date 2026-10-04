"""
Layar 3 - Detail & Perbandingan: kotak alasan, pemilih klaim berbasis nama, dua panel berdampingan
dengan sorotan kuning, skor kemiripan, dan tombol keputusan (catatan wajib saat Tunda/Tolak).
"""
import html
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import config as C
import db
from components.badges import badge_jenis, badge_status, badge_tingkat
from components.cards import header_halaman, html_kartu, kotak_alasan, fmt_rupiah
from components.highlight import sorot_identik, teks_aman
from components.pickers import pilih_klaim_nama, nama_tampil
from engine.preprocess import normalisasi_teks
from engine.similarity import jaccard, kunci_blok

def hitung_kemiripan(df, a, b):
    """Kemiripan teks (TF-IDF + cosine, idf dari kelompok diagnosis A) dan kode (Jaccard), dihitung langsung."""
    blok = df.loc[df["kode_diagnosis"].astype(str).map(kunci_blok) == kunci_blok(str(a["kode_diagnosis"])),
                  "teks_resume_medis"].map(normalisasi_teks).tolist()
    ta, tb = normalisasi_teks(a["teks_resume_medis"]), normalisasi_teks(b["teks_resume_medis"])
    try:
        vek = TfidfVectorizer(ngram_range=C.TFIDF_NGRAM).fit(blok + [ta, tb])
        X = vek.transform([ta, tb])
        teks = float(cosine_similarity(X[0], X[1])[0, 0])
    except ValueError:
        teks = 0.0
    kode = jaccard({a["kode_diagnosis"], a["kode_tindakan"]}, {b["kode_diagnosis"], b["kode_tindakan"]})
    return min(1.0, teks), kode

def panel(judul, r, resume_html):
    kv = [("ID klaim", r["id_klaim"]),
          ("Peserta", f"{nama_tampil(r['nama_peserta'])} ({r['id_peserta_samaran']})"),
          ("Faskes", r["nama_faskes"]),
          ("Tanggal", f"{r['tanggal_masuk']:%d/%m/%Y} – {r['tanggal_keluar']:%d/%m/%Y}"),
          ("Diagnosis / Tindakan", f"{r['kode_diagnosis']} / {r['kode_tindakan']}"),
          ("Kelompok INA-CBG", r["kode_inacbg"]),
          ("Nilai klaim", fmt_rupiah(r["nilai_klaim"])),
          ("Periode pengajuan", r["periode_pengajuan"]),
          ("No. episode", r["no_episode"])]
    isi = "".join(f"<div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(v))}</div>" for k, v in kv)
    return (f"<div class='kk-panel'><div class='kk-panel-judul'>{html.escape(judul)}</div>"
            f"<div class='kk-kv'>{isi}</div><div class='kk-resume'>{resume_html}</div></div>")

header_halaman("Detail & Perbandingan", "Dua klaim berdampingan. Bagian resume yang sama disorot kuning.")
pesan = st.session_state.pop("pb_pesan", None)
if pesan:
    st.success(pesan)
    
df = db.muat_klaim()
idx = df.set_index("id_klaim", drop=False)

# --- Arahkan pemilih ke klaim yang dibuka dari Daftar Prioritas (atau klaim berskor tertinggi) ---
buka = st.session_state.pop("buka_klaim", None)
if buka in idx.index:
    r0 = idx.loc[buka]
    st.session_state["pb_kiri_cari"] = ""
    st.session_state[f"pb_kiri_peserta_"] = r0["id_peserta_samaran"]
    st.session_state[f"pb_kiri_klaim_{r0['id_peserta_samaran']}"] = buka
    st.session_state["pb_mode_kanan"] = "Otomatis dari sistem"
elif "pb_kiri_cari" not in st.session_state and "pb_kiri_peserta_" not in st.session_state:
    r0 = df.sort_values("skor_risiko", ascending=False).iloc[0]
    st.session_state["pb_kiri_cari"] = ""
    st.session_state["pb_kiri_peserta_"] = r0["id_peserta_samaran"]
    st.session_state[f"pb_kiri_klaim_{r0['id_peserta_samaran']}"] = r0["id_klaim"]

wadah_alasan = st.container()          # kotak alasan di atas, diisi setelah klaim terpilih
with st.container(border=True):
    st.markdown("**Pilih klaim**")
    kolom_kiri, kolom_kanan = st.columns(2, gap="large")
    with kolom_kiri:
        st.markdown("Klaim yang diperiksa")
        id_a = pilih_klaim_nama(df, "pb_kiri", "Klaim")
    with kolom_kanan:
        mode = st.radio("Klaim yang mirip", ["Otomatis dari sistem", "Pilih manual"], horizontal=True, key="pb_mode_kanan")
        if mode == "Pilih manual":
            id_b = pilih_klaim_nama(df, "pb_kanan", "Klaim pembanding")
        else:
            id_b = None
            if id_a:
                pasangan = idx.loc[id_a]["id_klaim_pasangan"]
                id_b = pasangan if isinstance(pasangan, str) and pasangan in idx.index else None
                if id_b is None:
                    st.info("Sistem tidak menemukan pasangan untuk klaim ini. Pilih manual untuk membandingkan dengan klaim lain.")
                else:
                    st.caption(f"Pasangan dari sistem: {id_b}")

if not id_a:
    st.warning("Pilih klaim yang diperiksa terlebih dahulu.")
    st.stop()
a = idx.loc[id_a]
b = idx.loc[id_b] if id_b else None

# --- Kotak alasan ---
with wadah_alasan:
    st.markdown(f"{badge_jenis(a['jenis_indikasi'])} &nbsp; {badge_tingkat(a['skor_risiko'])} &nbsp; {badge_status(a['status'])}",
                unsafe_allow_html=True)
    teks_alasan = a["alasan"] if isinstance(a["alasan"], str) and a["alasan"] else "Belum ada hasil deteksi untuk klaim ini."
    kotak_alasan(teks_alasan, f"Alasan sistem untuk {a['id_klaim']} · skor risiko {int(a['skor_risiko'])}")
    st.caption(C.CATATAN_INDIKASI)

# --- Dua panel berdampingan ---
if b is not None:
    kemiripan_teks, kemiripan_kode = hitung_kemiripan(df, a, b)
    sorot_a, sorot_b = sorot_identik(a["teks_resume_medis"], b["teks_resume_medis"])
else:
    kemiripan_teks = kemiripan_kode = None
    sorot_a = teks_aman(a["teks_resume_medis"])
p1, p2 = st.columns(2, gap="large")
with p1:
    st.markdown(panel("Klaim yang diperiksa", a, sorot_a), unsafe_allow_html=True)
with p2:
    if b is not None:
        st.markdown(panel("Klaim yang mirip", b, sorot_b), unsafe_allow_html=True)
    else:
        st.markdown("<div class='kk-panel'><div class='kk-panel-judul'>Klaim yang mirip</div>"
                    "<div class='kk-kosong'>Belum ada klaim pembanding.</div></div>", unsafe_allow_html=True)

# --- Skor ---
st.write("")
s1, s2, s3 = st.columns(3)
s1.markdown(html_kartu("Skor risiko sistem", int(a["skor_risiko"]), "Skala 0–100 · indikasi, bukan bukti", "risiko_tinggi"), unsafe_allow_html=True)
s2.markdown(html_kartu("Kemiripan teks resume", "-" if kemiripan_teks is None else f"{kemiripan_teks:.0%}",
                       "TF-IDF + cosine, dihitung langsung", "biru"), unsafe_allow_html=True)
s3.markdown(html_kartu("Kemiripan kode (Jaccard)", "-" if kemiripan_kode is None else f"{kemiripan_kode:.2f}",
                       "Himpunan kode diagnosis dan tindakan", "hijau"), unsafe_allow_html=True)

# --- Keputusan ---
st.markdown("### Keputusan verifikator")
st.caption("Catatan verifikator wajib saat menunda atau menolak. Sistem tidak pernah menolak klaim secara otomatis.")
id_ver = st.session_state.get("id_verifikator")
reset = st.session_state.get("pb_reset", 0)
catatan = st.text_area("Catatan verifikator", key=f"pb_catatan_{id_a}_{reset}", height=100,
                       placeholder="Tulis alasan keputusan (wajib untuk Tunda atau Tolak)...")
t1, t2, t3 = st.columns(3)
setuju = t1.button("Setujui", key="btn_setuju", width="stretch")
tunda = t2.button("Tunda untuk klarifikasi", key="btn_tunda", width="stretch")
tolak = t3.button("Tolak", key="btn_tolak", width="stretch")
aksi = "disetujui" if setuju else ("ditunda" if tunda else ("ditolak" if tolak else None))

if aksi:
    if not id_ver:
        st.error("Pilih nama pada 'Masuk sebagai' di sidebar terlebih dahulu.")
    elif aksi in ("ditunda", "ditolak") and not catatan.strip():
        st.error("Catatan wajib diisi saat menunda atau menolak klaim. Keputusan belum disimpan.")
    else:
        db.simpan_keputusan(id_a, id_ver, aksi, catatan.strip() or None)
        st.session_state["pb_pesan"] = f"Keputusan '{C.LABEL_KEPUTUSAN[aksi]}' untuk {id_a} tersimpan dan tercatat di audit log."
        st.session_state["pb_reset"] = reset + 1
        st.rerun()

with st.expander("Riwayat keputusan untuk klaim ini"):
    rw = db.muat_riwayat()
    rw = rw[rw["id_klaim"] == id_a]
    if rw.empty:
        st.caption("Belum ada keputusan.")
    else:
        st.dataframe(rw[["waktu", "nama_verifikator", "keputusan", "catatan"]], hide_index=True, width="stretch")