from pathlib import Path

# Lokasi folder
ROOT_DIR = Path(__file__).resolve().parent
CSV_DIR = ROOT_DIR / "data" / "csv"

# Nama tabel database
T_FASKES = "faskes"
T_PESERTA = "peserta"
T_VERIFIKATOR = "verifikator"
T_KLAIM = "klaim"
T_LABEL = "label_sintetis"
T_HASIL = "hasil_deteksi"
T_KEPUTUSAN = "keputusan"
T_AUDIT = "audit_log"
T_PENGATURAN = "pengaturan"
T_PENGECUALIAN = "pengecualian_layanan"

# DATA SINTETIS (Tahap 2)
SEED = 20260907                 # seed tetap 
JUMLAH_KLAIM = 5000             # total klaim (ubah untuk uji skala, mis. 20000)
PERSEN_KEMBAR = 0.05            # +-5% klaim kembar
JUMLAH_PESERTA = 3200           # kolam peserta sintetis
TANGGAL_MULAI = "2026-06-01"    # rentang tanggal_masuk klaim asli
TANGGAL_AKHIR = "2026-09-20"

# Pembagian klaim kembar
PROPORSI_KEMBAR = {
    "duplikat_persis": 0.30,          # (a) klaim persis sama dikirim ulang
    "duplikat_tanggal_geser": 0.28,   # (b) tanggal geser 1-7 hari, no_episode beda
    "resume_disalin": 0.36,           # (c) resume disalin ke pasien lain
    "kasus_sulit_lolos": 0.06,        # (d) geser 8-10 hari + resume diparafrasekan berat
}
GESER_HARI_MIN, GESER_HARI_MAX = 1, 7          # untuk jenis (b)
GESER_SULIT_MIN, GESER_SULIT_MAX = 8, 10       # untuk jenis (d): di luar jendela R3
JEDA_SALIN_MIN, JEDA_SALIN_MAX = 1, 25         # jenis (c): klaim salinan muncul 1-25 hari setelah asli
PROB_SALIN_FASKES_BEDA = 0.70                  # peluang klaim salinan berada di faskes lain

# Kasus sulit yang SAH (label is_fraud = False)
JUMLAH_PASIEN_HD = 12           # hemodialisis, tiap pasien beberapa sesi
SESI_HD_PER_PASIEN = 8
JUMLAH_PASIEN_KEMO = 10         # kemoterapi terjadwal
SESI_KEMO_PER_PASIEN = 4
JUMLAH_PASIEN_KONTROL = 40      # kontrol rutin penyakit kronis (DM, hipertensi)
SESI_KONTROL_PER_PASIEN = 3
JUMLAH_TEMPLATE_BAKU = 40       # klaim sah beda pasien dengan resume template baku nyaris sama

# Faskes & verifikator sintetis (NAMA FIKTIF; ganti bila kebetulan sama dengan faskes nyata)
DAFTAR_FASKES = [
    ("F-001", "RS Medika Utama", "Rumah Sakit", "Malang"),
    ("F-002", "RS Harapan Nusantara", "Rumah Sakit", "Surabaya"),
    ("F-003", "RS Bunda Sejahtera", "Rumah Sakit", "Bandung"),
    ("F-004", "RSU Cahaya Kasih", "Rumah Sakit", "Semarang"),
    ("F-005", "RS Sentra Husada", "Rumah Sakit", "Yogyakarta"),
    ("F-006", "RS Permata Bangsa", "Rumah Sakit", "Jakarta"),
    ("F-007", "RSU Mitra Sehat", "Rumah Sakit", "Medan"),
    ("F-008", "RS Gemilang Waluyo", "Rumah Sakit", "Makassar"),
    ("F-009", "RS Tirta Kencana", "Rumah Sakit", "Denpasar"),
    ("F-010", "Klinik Utama Arunika", "Klinik Utama", "Malang"),
    ("F-011", "Klinik Utama Sehati", "Klinik Utama", "Surabaya"),
    ("F-012", "Klinik Pratama Lestari", "Klinik Pratama", "Bandung"),
    ("F-013", "Klinik Pratama Nusa Medika", "Klinik Pratama", "Semarang"),
    ("F-014", "RS Kartika Dharma", "Rumah Sakit", "Palembang"),
]
DAFTAR_VERIFIKATOR = [
    ("V-01", "Rina Kusumawati", "verifikator"),
    ("V-02", "Agus Prasetyo", "verifikator"),
    ("V-03", "Dewi Anggraini", "verifikator"),
    ("V-04", "Hendra Wijaya", "admin"),
]

# Daftar pengecualian layanan rutin (dimuat ke tabel pengecualian_layanan; bisa diubah di UI)
DAFTAR_PENGECUALIAN = [
    ("N18.6", "39.95", "Hemodialisis (cuci darah) terjadwal"),
    ("Z51.1", "99.25", "Kemoterapi terjadwal"),
    ("E11.9", "89.03", "Kontrol rutin diabetes melitus"),
    ("I10", "89.03", "Kontrol rutin hipertensi"),
]

# Pengaturan awal yang bisa diubah verifikator (dimuat ke tabel pengaturan; "rancangan awal")
PENGATURAN_AWAL = {
    "ambang_ditandai": "50",
    "ambang_cosine_kuat": "0.90",
    "ambang_cosine_tinjau": "0.80",
    "jendela_r3_hari": "7",
}

# Ukuran batch saat memuat ke database
UKURAN_BATCH = 500

# ----------------------------------------------------------------------
# MESIN DETEKSI (Tahap 3) - rancangan awal, dikalibrasi saat pengujian
# ----------------------------------------------------------------------
BOBOT_ATURAN = {"R1": 95, "R2": 90, "R3": 60, "R4": 50}   # bobot awal, bukan hasil validasi
JENDELA_R3_HARI = 7                    # R3: selisih tanggal_masuk <= 7 hari
JENDELA_R4_HARI = 14                   # R4: "dikirim ulang dalam waktu berdekatan"
R4_WAJIB_PESERTA_SAMA = True           # False = R4 persis seperti prompt (banyak salah tanda)
PENGECUALIAN_BERLAKU_UNTUK = ("R3", "R4")   # aturan yang diredam oleh pengecualian layanan

BLOCKING_DIAGNOSIS_KARAKTER = 3        # 3 = 3 karakter pertama ICD-10; 0 = kode penuh
JENDELA_BLOCKING_HARI = 30             # bandingkan hanya klaim dalam +-30 hari
UKURAN_CHUNK = 500                     # baris per potongan matriks (hemat memori)
COSINE_KUAT = 0.90                     # >= ini: indikasi kuat
COSINE_TINJAU = 0.80                   # 0,80-0,90: perlu ditinjau
JACCARD_MINIMAL = 0.5                  # kemiripan kode minimum agar dihitung Jiplakan
TFIDF_NGRAM = (1, 1)

# Pemetaan cosine -> skor (interpolasi linear): (cosine_bawah, cosine_atas, skor_bawah, skor_atas)
PEMETAAN_COSINE = [(0.80, 0.90, 50, 65), (0.90, 1.00, 80, 95)]
BONUS_GABUNGAN = 5                     # bonus bila Berulang + Jiplakan muncul bersamaan (maks 100)

AMBANG_DITANDAI = 50                   # skor >= ini dianggap "ditandai" (bisa diatur di Pengaturan)
BATAS_RISIKO_TINGGI = 80               # tampilan: >= 80 merah lembut
BATAS_RISIKO_SEDANG = 50               # 50-79 kuning, di bawahnya hijau

# Kamus singkatan untuk preprocessing teks
SINGKATAN = {
    "pt": "pasien", "tdk": "tidak", "dgn": "dengan", "yg": "yang", "td": "tekanan darah",
    "bb": "berat badan", "ro": "rontgen", "px": "pemeriksaan", "tx": "terapi", "dx": "diagnosis",
}

# ----------------------------------------------------------------------
# ANTARMUKA (Tahap 5)
# ----------------------------------------------------------------------
APP_NAMA = "KlaimKembar"
APP_TAGAR = "#SEKALIBAYARSEKALIKLAIM"
APP_TIM = "Tim Apam"
BANNER_SINTETIS = "Data sintetis, bukan data peserta JKN riil."
CATATAN_INDIKASI = "Output adalah indikasi, bukan bukti kecurangan. Keputusan akhir di tangan verifikator."
TTL_CACHE_DETIK = 300              # lama cache data di aplikasi
BARIS_PER_HALAMAN = 20             # baris per halaman di Daftar Prioritas
MIN_KATA_SOROTAN = 2               # sorotan kuning hanya untuk rangkaian >= 2 kata identik
STATUS_BELUM = "Belum ditinjau"
LABEL_KEPUTUSAN = {"disetujui": "Disetujui", "ditunda": "Ditunda", "ditolak": "Ditolak"}

# Palet tema putih-hijau-biru (dipakai CSS lewat variabel --kk-<nama>)
WARNA = {
    "hijau": "#059669", "hijau_tua": "#047857", "hijau_muda": "#ECFDF5",
    "biru": "#2563EB", "biru_muda": "#EFF6FF", "navy": "#1E3A8A",
    "teks": "#1E293B", "teks_redup": "#64748B", "garis": "#E2E8F0", "latar": "#F8FAFC",
    "kuning_sorot": "#FDE047",                       # HANYA untuk sorotan teks identik
    "risiko_tinggi": "#F87171", "risiko_sedang": "#FACC15", "risiko_rendah": "#34D399",
    "setuju": "#059669", "tunda": "#FACC15", "tolak": "#DC2626",
}
WARNA_JENIS = {"Berulang": "#2563EB", "Jiplakan": "#059669", "Berulang + Jiplakan": "#1E3A8A"}
JENIS_INDIKASI = list(WARNA_JENIS)