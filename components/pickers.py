"""pickers.py - dropdown + pencarian nama (peserta, klaim, faskes), filter samping, dan penyamaran nama."""
import streamlit as st
import config as C

# ----------------------------------------------------------------------
# Mode privasi
# ----------------------------------------------------------------------
def samarkan_nama(nama):
    """'Budi Santoso' -> 'Budi S******'. Kata pertama tetap, kata berikutnya disamarkan."""
    bagian = str(nama).split()
    if not bagian:
        return ""
    if len(bagian) == 1:
        return bagian[0][:1] + "*" * max(len(bagian[0]) - 1, 1)
    return " ".join([bagian[0]] + [b[:1] + "*" * max(len(b) - 1, 1) for b in bagian[1:]])

def nama_tampil(nama):
    """Nama sesuai sakelar Mode privasi di sidebar (aktif secara default)."""
    return samarkan_nama(nama) if st.session_state.get("mode_privasi", True) else str(nama)

def label_klaim(r):
    return f"{nama_tampil(r['nama_peserta'])} · {r['id_peserta_samaran']} · {r['id_klaim']} · {r['nama_faskes']} · {r['tanggal_masuk']:%d/%m/%Y}"

# ----------------------------------------------------------------------
# Pemilih berbasis nama
# ----------------------------------------------------------------------
def _pilih_peserta(df_peserta, key, label="Peserta"):
    """Ketik sebagian nama untuk menyaring, lalu pilih peserta. df_peserta: id_peserta_samaran, nama_peserta."""
    cari = st.text_input("Cari nama peserta (ketik sebagian, mis. 'bud')", key=f"{key}_cari",
                         placeholder="ketik sebagian nama...")
    pes = df_peserta.drop_duplicates("id_peserta_samaran")
    if cari.strip():
        pes = pes[pes["nama_peserta"].str.contains(cari.strip(), case=False, regex=False)]
    if pes.empty:
        st.warning("Tidak ada nama yang cocok.")
        return None
    nama_by = dict(zip(pes["id_peserta_samaran"], pes["nama_peserta"]))
    return st.selectbox(label, list(nama_by), key=f"{key}_peserta_{cari.strip().lower()}",
                        format_func=lambda i: f"{nama_tampil(nama_by[i])} · {i}")

def pilih_peserta(df_peserta, key, label="Peserta"):
    """Pemilih peserta (untuk formulir Pindai Klaim). Mengembalikan id_peserta_samaran atau None."""
    return _pilih_peserta(df_peserta, key, label)

def pilih_klaim_nama(df, key, label="Klaim"):
    """
    Pilih klaim lewat nama: saring nama -> pilih peserta -> pilih salah satu klaim milik peserta itu.
    Label opsi klaim: Nama · P-xxxx · KK-xxxx · Nama faskes · tanggal. Mengembalikan id_klaim atau None.
    """
    pid = _pilih_peserta(df[["id_peserta_samaran", "nama_peserta"]], key)
    if pid is None:
        return None
    milik = df[df["id_peserta_samaran"] == pid].sort_values("tanggal_masuk")
    baris = {r["id_klaim"]: r for _, r in milik.iterrows()}
    return st.selectbox(label, list(baris), key=f"{key}_klaim_{pid}",
                        format_func=lambda i: label_klaim(baris[i]))

def pilih_faskes(df_faskes, key, label="Faskes"):
    """Dropdown faskes berdasarkan nama. Mengembalikan id_faskes."""
    nama_by = {r["id_faskes"]: f"{r['nama_faskes']} · {r['kota']}" for _, r in df_faskes.iterrows()}
    return st.selectbox(label, list(nama_by), key=key, format_func=lambda i: nama_by[i])

# ----------------------------------------------------------------------
# Filter (dipakai Ringkasan dan Daftar Prioritas)
# ----------------------------------------------------------------------
def filter_periode(df, key):
    opsi = ["Semua periode"] + sorted(df["periode_pengajuan"].dropna().unique().tolist())
    pilih = st.selectbox("Periode pengajuan", opsi, key=f"{key}_periode")
    return (df if pilih == "Semua periode" else df[df["periode_pengajuan"] == pilih]), pilih

def filter_samping(df, key, skor_awal=0, df_opsi=None):
    """
    Filter samping: faskes (nama), kelompok diagnosis, jenis indikasi, rentang skor.
    Mengembalikan dict: 'cakupan' (setelah faskes+diagnosis) dan 'hasil' (plus jenis+skor).
    """
    ref = df if df_opsi is None else df_opsi          # opsi dari data penuh agar pilihan stabil
    with st.container(border=True):
        st.markdown("**Filter**")
        faskes = st.multiselect("Faskes (nama)", sorted(ref["nama_faskes"].unique()),
                                key=f"{key}_faskes", placeholder="Semua faskes")
        dx = st.multiselect("Kelompok diagnosis (ICD-10)", sorted(ref["kelompok_dx"].unique()),
                            key=f"{key}_dx", placeholder="Semua kelompok")
        jenis = st.multiselect("Jenis indikasi", C.JENIS_INDIKASI, key=f"{key}_jenis", placeholder="Semua jenis")
        skor = st.slider("Rentang skor risiko", 0, 100, (int(skor_awal), 100), key=f"{key}_skor")
    cakupan = df
    if faskes:
        cakupan = cakupan[cakupan["nama_faskes"].isin(faskes)]
    if dx:
        cakupan = cakupan[cakupan["kelompok_dx"].isin(dx)]
    hasil = cakupan
    if jenis:
        hasil = hasil[hasil["jenis_indikasi"].isin(jenis)]
    hasil = hasil[hasil["skor_risiko"].between(skor[0], skor[1])]
    return {"cakupan": cakupan, "hasil": hasil}