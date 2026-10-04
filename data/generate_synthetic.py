"""
generate_synthetic.py - pembuat data klaim SINTETIS KlaimKembar (seed tetap) + ringkasan pemeriksa.

Jalankan dari folder utama proyek:
    python -m data.generate_synthetic

Keluaran di data/csv/: faskes.csv, peserta.csv, klaim.csv, label_sintetis.csv
(verifikator dan pengecualian_layanan diambil dari config.py oleh load_to_supabase.py).

SEMUA DATA DI SINI BUATAN. Tidak ada data peserta JKN riil.
Mesin deteksi TIDAK BOLEH membaca label_sintetis (hanya evaluate.py).

CATATAN: pasangan ICD-10 / ICD-9-CM dan kode INA-CBG di bawah hanya ILUSTRATIF
untuk data sintetis; belum divalidasi tenaga medis atau tabel tarif resmi.
"""
import re
import sys
import random
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from faker import Faker

import config as C

# ======================================================================
# BAHAN BAKU RESUME (sintetis)
# ======================================================================
# Tiap entri: dx, tindakan, nama, inacbg (ilustratif), nilai (Rp), los (min,max hari),
# bobot (frekuensi relatif), usia (min,max), jk (None = acak), dan frasa penyusun resume.
DIAGNOSIS = [
    dict(dx="J18.9", tindakan="99.21", nama="Pneumonia", inacbg="J-4-12-II", nilai=2_000_000,
         los=(2, 5), bobot=10, usia=(5, 85), jk=None,
         gejala=["demam", "batuk berdahak", "sesak napas", "nyeri dada saat batuk", "lemas", "nafsu makan menurun", "menggigil"],
         periksa=["suhu {suhu} C", "frekuensi napas {rr} per menit", "saturasi oksigen {sat}%", "ronki basah di paru kanan", "ronki basah di paru kiri", "retraksi dinding dada ringan"],
         penunjang=["leukosit {leu}/uL", "foto toraks tampak infiltrat", "foto toraks infiltrat lapang paru bawah", "CRP meningkat"],
         terapi=["antibiotik intravena", "oksigen nasal kanul", "nebulisasi", "paracetamol", "ekspektoran", "infus kristaloid"],
         rencana=["observasi {hari} hari rawat", "evaluasi klinis dan foto toraks ulang", "rawat inap hingga demam turun", "pulang bila saturasi stabil"]),
    dict(dx="A09", tindakan="99.18", nama="Gastroenteritis", inacbg="K-4-18-I", nilai=1_300_000,
         los=(1, 3), bobot=9, usia=(1, 80), jk=None,
         gejala=["diare cair", "muntah", "mual", "nyeri perut", "demam ringan", "lemas", "buang air besar {hari} kali sehari"],
         periksa=["turgor kulit menurun", "mukosa mulut kering", "bising usus meningkat", "suhu {suhu} C", "nyeri tekan epigastrium ringan"],
         penunjang=["leukosit {leu}/uL", "elektrolit dalam batas wajar", "feses tidak ditemukan darah", "hematokrit meningkat ringan"],
         terapi=["rehidrasi infus ringer laktat", "zinc", "antiemetik", "probiotik", "oralit", "antibiotik sesuai indikasi"],
         rencana=["observasi {hari} hari rawat", "pulang bila toleransi oral baik", "edukasi kebersihan makanan", "kontrol bila diare menetap"]),
    dict(dx="A91", tindakan="99.18", nama="Demam berdarah dengue", inacbg="A-4-10-II", nilai=2_800_000,
         los=(3, 6), bobot=6, usia=(3, 60), jk=None,
         gejala=["demam tinggi {hari} hari", "nyeri kepala", "nyeri belakang mata", "nyeri otot dan sendi", "mual", "bintik merah di kulit", "mimisan"],
         periksa=["suhu {suhu} C", "tekanan darah {td}", "uji tourniquet positif", "petekie di lengan", "nyeri tekan perut kanan atas"],
         penunjang=["trombosit {trombosit}/uL", "hematokrit meningkat", "NS1 dengue positif", "leukosit {leu}/uL"],
         terapi=["infus kristaloid sesuai fase kritis", "paracetamol", "pemantauan trombosit tiap 12 jam", "antiemetik", "cairan oral banyak"],
         rencana=["observasi tanda syok", "pulang bila trombosit meningkat dan afebris", "edukasi tanda bahaya", "rawat inap {hari} hari"]),
    dict(dx="I10", tindakan="89.03", nama="Hipertensi esensial", inacbg="I-4-15-I", nilai=450_000,
         los=(0, 0), bobot=14, usia=(35, 85), jk=None,
         gejala=["sakit kepala", "tengkuk terasa berat", "pusing", "tidak ada keluhan", "berdebar", "kontrol rutin"],
         periksa=["tekanan darah {td}", "nadi {nadi} per menit", "tidak ada edema tungkai", "bunyi jantung reguler", "berat badan stabil"],
         penunjang=["profil lipid dalam evaluasi", "kreatinin {krea} mg/dl", "EKG sinus ritme"],
         terapi=["amlodipin", "captopril", "bisoprolol", "hidroklorotiazid", "diet rendah garam"],
         rencana=["kontrol 1 bulan lagi", "lanjut obat rutin", "edukasi pola hidup sehat", "periksa laboratorium berkala"]),
    dict(dx="E11.9", tindakan="89.03", nama="Diabetes melitus tipe 2", inacbg="E-4-10-I", nilai=500_000,
         los=(0, 0), bobot=10, usia=(35, 85), jk=None,
         gejala=["sering haus", "sering buang air kecil", "lemas", "tidak ada keluhan", "kesemutan di kaki", "kontrol rutin"],
         periksa=["tekanan darah {td}", "berat badan stabil", "tidak ada luka kaki", "nadi {nadi} per menit", "refleks normal"],
         penunjang=["gula darah sewaktu {gds} mg/dl", "HbA1c dievaluasi", "gula darah puasa {gds} mg/dl"],
         terapi=["metformin", "glimepirid", "diet diabetes", "olahraga teratur", "insulin basal sesuai dosis"],
         rencana=["kontrol 1 bulan lagi", "lanjut obat rutin", "edukasi diet dan olahraga", "periksa HbA1c 3 bulan"]),
    dict(dx="K35.8", tindakan="47.09", nama="Apendisitis akut", inacbg="K-1-14-II", nilai=6_500_000,
         los=(2, 4), bobot=4, usia=(10, 60), jk=None,
         gejala=["nyeri perut kanan bawah", "mual dan muntah", "demam", "nafsu makan menurun", "nyeri berpindah dari ulu hati"],
         periksa=["nyeri tekan titik McBurney", "nyeri lepas positif", "Rovsing sign positif", "suhu {suhu} C", "defans muskular ringan"],
         penunjang=["leukosit {leu}/uL", "USG tampak apendiks membesar", "CRP meningkat"],
         terapi=["puasa dan infus", "antibiotik profilaksis", "apendektomi terbuka", "analgetik pasca operasi", "mobilisasi dini"],
         rencana=["observasi luka operasi", "pulang hari ke-{hari} bila luka baik", "kontrol poli bedah 1 minggu", "angkat jahitan 7 hari"]),
    dict(dx="O80", tindakan="73.59", nama="Persalinan spontan", inacbg="O-6-10-I", nilai=3_200_000,
         los=(1, 3), bobot=6, usia=(18, 40), jk="perempuan",
         gejala=["mules teratur", "keluar lendir darah", "pembukaan lengkap", "ketuban pecah spontan", "kontraksi makin sering"],
         periksa=["tekanan darah {td}", "denyut jantung janin {nadi} per menit", "pembukaan {hari} cm", "presentasi kepala", "tidak ada tanda gawat janin"],
         penunjang=["hemoglobin {hb} g/dl", "golongan darah dicatat", "tidak ada kelainan pada USG"],
         terapi=["pimpinan persalinan normal", "oksitosin 10 IU setelah bayi lahir", "episiotomi bila perlu", "perawatan nifas", "inisiasi menyusu dini"],
         rencana=["observasi perdarahan 2 jam", "pulang hari ke-{hari} bila stabil", "kontrol nifas 1 minggu", "edukasi ASI eksklusif"]),
    dict(dx="S72.0", tindakan="79.35", nama="Fraktur leher femur", inacbg="S-1-20-III", nilai=14_000_000,
         los=(4, 8), bobot=2, usia=(50, 90), jk=None,
         gejala=["nyeri pinggul setelah jatuh", "tidak dapat berjalan", "tungkai tampak memendek", "bengkak di pangkal paha", "rotasi eksterna tungkai"],
         periksa=["nyeri tekan regio panggul", "deformitas tungkai kanan", "deformitas tungkai kiri", "nadi distal teraba", "tekanan darah {td}"],
         penunjang=["foto polos panggul tampak fraktur", "hemoglobin {hb} g/dl", "leukosit {leu}/uL"],
         terapi=["imobilisasi traksi kulit", "analgetik", "fiksasi interna terbuka", "antibiotik profilaksis", "profilaksis tromboemboli"],
         rencana=["fisioterapi bertahap", "rawat inap {hari} hari", "kontrol poli ortopedi 2 minggu", "foto kontrol pasca operasi"]),
    dict(dx="I21.9", tindakan="36.06", nama="Infark miokard akut", inacbg="I-1-12-III", nilai=24_000_000,
         los=(3, 7), bobot=2, usia=(40, 85), jk=None,
         gejala=["nyeri dada seperti tertekan", "nyeri menjalar ke lengan kiri", "keringat dingin", "sesak napas", "mual"],
         periksa=["tekanan darah {td}", "nadi {nadi} per menit", "saturasi oksigen {sat}%", "bunyi jantung reguler", "ronki basah basal ringan"],
         penunjang=["EKG elevasi segmen ST", "troponin meningkat", "angiografi koroner stenosis", "kreatinin {krea} mg/dl"],
         terapi=["aspirin dan klopidogrel", "heparin", "pemasangan stent koroner", "nitrat", "statin dosis tinggi", "beta blocker"],
         rencana=["perawatan ICCU", "rawat inap {hari} hari", "rehabilitasi jantung", "kontrol poli jantung 1 minggu"]),
    dict(dx="J45.9", tindakan="93.94", nama="Asma", inacbg="J-4-16-I", nilai=1_200_000,
         los=(0, 2), bobot=8, usia=(4, 70), jk=None,
         gejala=["sesak napas", "mengi", "batuk malam hari", "dada terasa berat", "sering kambuh saat cuaca dingin"],
         periksa=["wheezing ekspirasi", "frekuensi napas {rr} per menit", "saturasi oksigen {sat}%", "retraksi interkostal ringan", "suhu {suhu} C"],
         penunjang=["foto toraks tidak ada infiltrat", "arus puncak ekspirasi menurun", "eosinofil meningkat ringan"],
         terapi=["nebulisasi salbutamol", "nebulisasi ipratropium", "kortikosteroid oral", "oksigen bila perlu", "inhaler pelega"],
         rencana=["pulang bila sesak teratasi", "kontrol 1 minggu", "edukasi pencetus asma", "observasi {hari} jam"]),
    dict(dx="N39.0", tindakan="99.21", nama="Infeksi saluran kemih", inacbg="N-4-12-I", nilai=1_500_000,
         los=(1, 3), bobot=8, usia=(15, 80), jk=None,
         gejala=["nyeri saat buang air kecil", "sering buang air kecil", "nyeri pinggang", "demam", "urin keruh", "anyang-anyangan"],
         periksa=["nyeri ketok sudut kostovertebra", "nyeri tekan suprapubik", "suhu {suhu} C", "tekanan darah {td}", "tidak ada massa teraba"],
         penunjang=["leukosit urin meningkat", "nitrit urin positif", "kultur urin dikirim", "leukosit {leu}/uL"],
         terapi=["antibiotik sesuai kultur", "hidrasi cukup", "analgetik", "antipiretik", "infus kristaloid"],
         rencana=["observasi {hari} hari rawat", "kontrol urin ulang", "edukasi kebersihan", "pulang bila demam turun"]),
    dict(dx="I63.9", tindakan="87.03", nama="Stroke iskemik", inacbg="G-1-10-III", nilai=7_500_000,
         los=(4, 9), bobot=3, usia=(45, 90), jk=None,
         gejala=["kelemahan sisi tubuh kanan", "kelemahan sisi tubuh kiri", "bicara pelo", "mulut mencong", "pusing berputar", "penurunan kesadaran ringan"],
         periksa=["tekanan darah {td}", "kekuatan otot menurun sisi lumpuh", "parese nervus VII", "GCS 14", "refleks patologis positif"],
         penunjang=["CT scan kepala infark", "gula darah sewaktu {gds} mg/dl", "profil lipid meningkat", "EKG fibrilasi atrium"],
         terapi=["antiplatelet", "statin", "neuroprotektor", "kontrol tekanan darah", "fisioterapi dini", "heparin sesuai indikasi"],
         rencana=["rawat inap {hari} hari", "rehabilitasi medik", "kontrol poli saraf 1 minggu", "edukasi pencegahan stroke ulang"]),
    dict(dx="L02.9", tindakan="86.04", nama="Abses kulit", inacbg="L-4-10-I", nilai=1_800_000,
         los=(0, 2), bobot=5, usia=(10, 70), jk=None,
         gejala=["benjolan nyeri di kulit", "bengkak kemerahan", "terasa panas", "keluar nanah", "demam ringan"],
         periksa=["massa fluktuatif {hari} cm", "kemerahan sekitar lesi", "nyeri tekan", "suhu {suhu} C", "tidak ada krepitasi"],
         penunjang=["leukosit {leu}/uL", "gula darah sewaktu {gds} mg/dl", "kultur pus dikirim"],
         terapi=["insisi dan drainase", "irigasi luka", "antibiotik oral", "analgetik", "perawatan luka"],
         rencana=["kontrol luka 3 hari", "ganti balutan tiap hari", "edukasi kebersihan luka", "pulang hari yang sama"]),
]
DIAG_BY_DX = {d["dx"]: d for d in DIAGNOSIS}

# Layanan rutin SAH (pengecualian): resume template baku, hanya angka yang berubah
DIAGNOSIS_RUTIN = {
    "hemodialisis": dict(dx="N18.6", tindakan="39.95", inacbg="N-1-40-II", nilai=1_050_000,
                         resume="Pasien {jk} usia {usia} tahun penyakit ginjal kronik stadium 5 menjalani hemodialisis rutin sesi ke-{sesi}. "
                                "Akses vaskular AV shunt lancar. Durasi 4 jam, UF {uf} ml. Tekanan darah pre {td}. "
                                "Tidak ada keluhan berarti. Lanjut jadwal hemodialisis berikutnya."),
    "kemoterapi": dict(dx="Z51.1", tindakan="99.25", inacbg="C-4-10-II", nilai=3_400_000,
                       resume="Pasien {jk} usia {usia} tahun dengan keganasan menjalani kemoterapi terjadwal siklus ke-{sesi}. "
                              "Premedikasi antiemetik diberikan. Tidak ada reaksi infus. Tekanan darah {td}. "
                              "Jadwal siklus berikutnya sesuai protokol."),
    "kontrol_dm": dict(dx="E11.9", tindakan="89.03", inacbg="E-4-10-I", nilai=500_000,
                       resume="Pasien {jk} usia {usia} tahun kontrol rutin diabetes melitus tipe 2. Gula darah sewaktu {gds} mg/dl. "
                              "Tekanan darah {td}. Obat dilanjutkan, edukasi diet dan olahraga. Kontrol ulang bulan depan."),
    "kontrol_ht": dict(dx="I10", tindakan="89.03", inacbg="I-4-15-I", nilai=450_000,
                       resume="Pasien {jk} usia {usia} tahun kontrol rutin hipertensi. Tekanan darah {td}. "
                              "Tidak ada keluhan. Obat antihipertensi dilanjutkan, edukasi diet rendah garam. Kontrol ulang bulan depan."),
}

# Template baku untuk klaim SAH pasien berbeda dengan resume nyaris identik (kasus sulit)
TEMPLATE_BAKU = dict(dx="J45.9", tindakan="93.94", inacbg="J-4-16-I", nilai=1_200_000,
                     resume="Pasien datang dengan keluhan sesak napas dan mengi. Saturasi oksigen {sat}%. "
                            "Dilakukan nebulisasi salbutamol. Keluhan membaik, pasien pulang dan kontrol bila kambuh.")

# Kamus sinonim untuk memodifikasi resume (cloning ringan) dan memparafrasekan (kasus sulit)
SINONIM = {
    "demam": "panas badan", "batuk": "batuk-batuk", "sesak napas": "sesak", "lemas": "lesu",
    "nyeri": "sakit", "mual": "enek", "muntah": "emesis", "datang dengan keluhan": "datang disertai keluhan",
    "Pasien": "Penderita", "pasien": "penderita", "Pemeriksaan fisik": "Pada pemeriksaan",
    "Penunjang": "Hasil pendukung", "Terapi": "Penatalaksanaan", "Rencana": "Tindak lanjut",
    "observasi": "pemantauan", "pulang": "dipulangkan", "meningkat": "naik", "menurun": "turun",
    "antibiotik": "obat antibakteri", "infus": "cairan infus", "kontrol": "pemeriksaan ulang",
    "edukasi": "penyuluhan", "rawat inap": "dirawat", "dilanjutkan": "diteruskan", "tampak": "terlihat",
}
KALIMAT_TAMBAHAN = [
    "Kondisi pasien stabil.", "Tidak ada alergi obat yang diketahui.", "Keluarga pasien sudah diberi penjelasan.",
    "Pasien kooperatif selama perawatan.", "Tanda vital dalam pemantauan.",
]

KODE_PENGECUALIAN = {(x[0], x[1]) for x in C.DAFTAR_PENGECUALIAN}


# ======================================================================
# Fungsi bantu
# ======================================================================
def bulatkan(nilai, rng):
    """Variasi +-12% lalu dibulatkan ke puluhan ribu rupiah."""
    return int(round(nilai * rng.uniform(0.88, 1.12) / 10_000) * 10_000)


def isi_slot(teks, rng):
    """Isi slot angka {suhu}, {td}, dst. dengan nilai acak yang wajar."""
    slot = {
        "suhu": f"{rng.uniform(37.5, 39.8):.1f}", "rr": rng.randint(20, 36),
        "sat": rng.randint(88, 99), "leu": rng.randint(4000, 22000),
        "hari": rng.randint(2, 7), "td": f"{rng.randint(100, 175)}/{rng.randint(60, 105)}",
        "trombosit": rng.randint(20000, 150000), "nadi": rng.randint(60, 120),
        "krea": f"{rng.uniform(0.6, 2.4):.1f}", "gds": rng.randint(90, 360),
        "hb": f"{rng.uniform(8.0, 15.0):.1f}", "uf": rng.randint(1500, 3500),
        "jk": "laki-laki", "usia": 50, "sesi": 1,
    }
    return teks.format_map(slot)


def bulan_berikut(periode):
    """'2026-09' -> '2026-10'."""
    t, b = map(int, periode.split("-"))
    t, b = (t + 1, 1) if b == 12 else (t, b + 1)
    return f"{t}-{b:02d}"


def periode_dari(tgl_keluar, rng):
    """Periode pengajuan = bulan (tanggal keluar + jeda 3-25 hari)."""
    return (tgl_keluar + timedelta(days=rng.randint(3, 25))).strftime("%Y-%m")


def buat_resume(d, rng, jk, usia):
    """Rakit resume medis dari frasa-frasa diagnosis (bukan teks acak murni)."""
    gejala = ", ".join(rng.sample(d["gejala"], rng.randint(2, 4)))
    periksa = "; ".join(rng.sample(d["periksa"], rng.randint(2, 3)))
    penunjang = "; ".join(rng.sample(d["penunjang"], rng.randint(1, 2)))
    terapi = ", ".join(rng.sample(d["terapi"], rng.randint(2, 3)))
    rencana = rng.choice(d["rencana"])
    teks = (f"Pasien {jk} usia {usia} tahun datang dengan keluhan {gejala}. "
            f"Pemeriksaan fisik: {periksa}. Tanda vital: TD {{td}}, nadi {{nadi}}, RR {{rr}}, suhu {{suhu}} C. "
            f"Penunjang: {penunjang}. Lab: Hb {{hb}}, leukosit {{leu}}, GDS {{gds}}. "
            f"Terapi: {terapi}. Rencana: {rencana}.")
    return isi_slot(teks, rng)


def terapkan_sinonim(teks, rng, jumlah=None):
    """Ganti kata dengan sinonim. jumlah=None -> ganti SEMUA (parafrase berat)."""
    kunci = [k for k in SINONIM if re.search(rf"\b{re.escape(k)}\b", teks)]
    if jumlah is not None:
        rng.shuffle(kunci)
        kunci = kunci[:jumlah]
    for k in kunci:
        teks = re.sub(rf"\b{re.escape(k)}\b", SINONIM[k], teks, count=1 if jumlah else 0)
    return teks


def ubah_resume_ringan(teks, rng):
    """
    Salinan 'dengan sedikit perubahan'. Pilih 1-3 operasi acak:
    ganti satu kata dengan sinonim, ubah satu angka, buang kalimat terakhir, tambah kalimat.
    """
    for _ in range(rng.choice([1, 1, 2, 2, 3])):
        op = rng.choices(["sinonim", "angka", "buang", "tambah"], weights=[35, 25, 15, 25])[0]
        if op == "sinonim":
            teks = terapkan_sinonim(teks, rng, jumlah=1)
        elif op == "angka":
            angka = list(re.finditer(r"\b\d{2,3}\b", teks))
            if angka:
                m = rng.choice(angka)
                teks = teks[:m.start()] + str(int(m.group()) + rng.choice([-2, -1, 1, 2])) + teks[m.end():]
        elif op == "buang":
            kalimat = re.split(r"(?<=\.)\s+", teks)
            if len(kalimat) > 3:
                teks = " ".join(kalimat[:-1])
        else:
            teks = teks + " " + rng.choice(KALIMAT_TAMBAHAN)
    return teks


def parafrase_berat(teks, rng):
    """Parafrase berat: semua sinonim diganti, urutan kalimat diacak, sebagian kalimat dibuang."""
    teks = terapkan_sinonim(teks, rng)
    kalimat = [k.strip() for k in re.split(r"(?<=\.)\s+", teks) if k.strip()]
    rng.shuffle(kalimat)
    if len(kalimat) > 3:
        kalimat.pop(rng.randrange(len(kalimat)))
    return " ".join(kalimat)


# ======================================================================
# Pembangunan data
# ======================================================================
def buat_master(fake, n_peserta):
    faskes = pd.DataFrame(C.DAFTAR_FASKES, columns=["id_faskes", "nama_faskes", "jenis_faskes", "kota"])
    nama_dipakai, baris = set(), []
    for i in range(1, n_peserta + 1):
        for _ in range(20):                       # hindari nama kembar persis
            nama = f"{fake.first_name()} {fake.last_name()}"
            if nama not in nama_dipakai:
                break
        nama_dipakai.add(nama)
        baris.append((f"P-{i:04d}", nama))
    peserta = pd.DataFrame(baris, columns=["id_peserta_samaran", "nama_peserta"])
    return faskes, peserta


def klaim_baru(rng, pid, fid, d, tgl_masuk, resume, nilai=None, tgl_keluar=None):
    """Bangun satu baris klaim (dict). id_klaim diisi belakangan."""
    if tgl_keluar is None:
        tgl_keluar = tgl_masuk + timedelta(days=rng.randint(*d.get("los", (0, 0))))
    return {
        "_tmp": None, "no_episode": f"EP-{rng.randint(10_000_000, 99_999_999)}",
        "id_peserta_samaran": pid, "id_faskes": fid,
        "tanggal_masuk": tgl_masuk, "tanggal_keluar": tgl_keluar,
        "periode_pengajuan": periode_dari(tgl_keluar, rng),
        "kode_diagnosis": d["dx"], "kode_tindakan": d["tindakan"], "kode_inacbg": d["inacbg"],
        "nilai_klaim": nilai if nilai is not None else bulatkan(d["nilai"], rng),
        "teks_resume_medis": resume,
        "_fraud": False, "_jenis": None, "_asal": None,
    }


def bangun(rng, fake):
    tgl0, tgl1 = date.fromisoformat(C.TANGGAL_MULAI), date.fromisoformat(C.TANGGAL_AKHIR)
    rentang = (tgl1 - tgl0).days
    n_total = C.JUMLAH_KLAIM
    n_peserta = max(C.JUMLAH_PESERTA, int(n_total * 0.64))
    faskes, peserta = buat_master(fake, n_peserta)
    id_faskes = faskes["id_faskes"].tolist()
    id_rs = faskes.loc[faskes["jenis_faskes"] == "Rumah Sakit", "id_faskes"].tolist()
    semua_pid = peserta["id_peserta_samaran"].tolist()
    rng.shuffle(semua_pid)
    kolam = iter(semua_pid)   # tiap peserta rutin diambil sekali (tidak bertabrakan)

    jk_pid = {p: rng.choice(["laki-laki", "perempuan"]) for p in semua_pid}
    usia_pid = {p: rng.randint(20, 85) for p in semua_pid}

    klaim = []

    # --- 1. Layanan rutin SAH (hemodialisis, kemoterapi, kontrol kronis) ---
    def tambah_rutin(kunci, n_pasien, n_sesi, jeda_pilihan, hanya_rs=False):
        d = DIAGNOSIS_RUTIN[kunci]
        for _ in range(n_pasien):
            pid = next(kolam)
            fid = rng.choice(id_rs if hanya_rs else id_faskes)
            jk, usia = jk_pid[pid], usia_pid[pid]
            nilai = bulatkan(d["nilai"], rng)          # tarif tetap per pasien
            jeda = [rng.choice(jeda_pilihan) for _ in range(n_sesi - 1)]
            span = sum(max(jeda_pilihan) for _ in range(n_sesi - 1)) + 1
            tgl = tgl0 + timedelta(days=rng.randint(0, max(0, rentang - span)))
            for sesi in range(1, n_sesi + 1):
                no_sesi = sesi + rng.randint(5, 40) if kunci == "hemodialisis" else sesi
                resume = isi_slot(d["resume"].replace("{jk}", jk).replace("{usia}", str(usia))
                                  .replace("{sesi}", str(no_sesi)), rng)
                klaim.append(klaim_baru(rng, pid, fid, {**d, "los": (0, 0)}, tgl, resume, nilai=nilai))
                if sesi < n_sesi:
                    tgl += timedelta(days=jeda[sesi - 1])

    tambah_rutin("hemodialisis", C.JUMLAH_PASIEN_HD, C.SESI_HD_PER_PASIEN, [2, 3], hanya_rs=True)
    tambah_rutin("kemoterapi", C.JUMLAH_PASIEN_KEMO, C.SESI_KEMO_PER_PASIEN, [7, 14], hanya_rs=True)
    n_dm = C.JUMLAH_PASIEN_KONTROL // 2
    tambah_rutin("kontrol_dm", n_dm, C.SESI_KONTROL_PER_PASIEN, [28, 29, 30, 31])
    tambah_rutin("kontrol_ht", C.JUMLAH_PASIEN_KONTROL - n_dm, C.SESI_KONTROL_PER_PASIEN, [28, 29, 30, 31])

    # --- 2. Template baku SAH: pasien berbeda, resume nyaris identik ---
    d = TEMPLATE_BAKU
    jendela_baku = 45                                   # tanggal dirapatkan agar jatuh dalam blocking
    mulai_baku = tgl0 + timedelta(days=rng.randint(0, max(0, rentang - jendela_baku)))
    for _ in range(C.JUMLAH_TEMPLATE_BAKU):
        pid = rng.choice(semua_pid)
        tgl = mulai_baku + timedelta(days=rng.randint(0, jendela_baku))
        klaim.append(klaim_baru(rng, pid, rng.choice(id_faskes), {**d, "los": (0, 1)}, tgl, isi_slot(d["resume"], rng)))

    # --- 3. Klaim normal ---
    n_kembar = round(n_total * C.PERSEN_KEMBAR)
    n_normal = n_total - n_kembar - len(klaim)
    if n_normal <= 0:
        raise SystemExit("JUMLAH_KLAIM terlalu kecil untuk kasus sulit; naikkan di config.py")
    bobot = [d["bobot"] for d in DIAGNOSIS]
    normal = []
    for _ in range(n_normal):
        d = rng.choices(DIAGNOSIS, weights=bobot)[0]
        pid = rng.choice(semua_pid)
        jk = d["jk"] or jk_pid[pid]
        resume = buat_resume(d, rng, jk, rng.randint(*d["usia"]))
        tgl = tgl0 + timedelta(days=rng.randint(0, rentang))
        normal.append(klaim_baru(rng, pid, rng.choice(id_faskes), d, tgl, resume))
    klaim.extend(normal)

    # --- 4. Klaim kembar (diberi label) ---
    # Asal hanya dari klaim normal, bukan layanan pengecualian, dan tanggalnya tidak terlalu akhir
    batas_asal = tgl1 - timedelta(days=C.JEDA_SALIN_MAX + 1)
    calon = [k for k in normal
             if (k["kode_diagnosis"], k["kode_tindakan"]) not in KODE_PENGECUALIAN
             and k["tanggal_masuk"] <= batas_asal]
    rng.shuffle(calon)
    jumlah = {j: int(round(n_kembar * p)) for j, p in C.PROPORSI_KEMBAR.items()}
    jumlah["duplikat_persis"] += n_kembar - sum(jumlah.values())   # koreksi pembulatan
    if sum(jumlah.values()) > len(calon):
        raise SystemExit("Terlalu sedikit klaim asal untuk klaim kembar")
    idx = 0
    for jenis, n in jumlah.items():
        for _ in range(n):
            a = calon[idx]
            idx += 1
            d = DIAG_BY_DX[a["kode_diagnosis"]]
            durasi = a["tanggal_keluar"] - a["tanggal_masuk"]
            if jenis == "duplikat_persis":          # (a) kirim ulang persis, periode berbeda
                k = dict(a)
                k["periode_pengajuan"] = bulan_berikut(a["periode_pengajuan"])
                lab = "duplikat_persis"
            elif jenis == "duplikat_tanggal_geser":  # (b) tanggal geser 1-7 hari + episode beda
                g = rng.randint(C.GESER_HARI_MIN, C.GESER_HARI_MAX)
                tm = a["tanggal_masuk"] + timedelta(days=g)
                k = klaim_baru(rng, a["id_peserta_samaran"], a["id_faskes"], d, tm,
                               a["teks_resume_medis"], nilai=a["nilai_klaim"], tgl_keluar=tm + durasi)
                lab = "duplikat_tanggal_geser"
            elif jenis == "resume_disalin":          # (c) resume disalin ke pasien lain
                pid = rng.choice([p for p in rng.sample(semua_pid, 5) if p != a["id_peserta_samaran"]])
                fid = a["id_faskes"]
                if rng.random() < C.PROB_SALIN_FASKES_BEDA:
                    fid = rng.choice([f for f in id_faskes if f != fid])
                tm = a["tanggal_masuk"] + timedelta(days=rng.randint(C.JEDA_SALIN_MIN, C.JEDA_SALIN_MAX))
                k = klaim_baru(rng, pid, fid, d, tm, ubah_resume_ringan(a["teks_resume_medis"], rng),
                               nilai=bulatkan(a["nilai_klaim"], rng) if rng.random() < 0.5 else a["nilai_klaim"],
                               tgl_keluar=tm + durasi)
                lab = "resume_disalin"
            else:                                    # (d) kasus sulit: geser 8-10 hari + parafrase berat
                g = rng.randint(C.GESER_SULIT_MIN, C.GESER_SULIT_MAX)
                tm = a["tanggal_masuk"] + timedelta(days=g)
                k = klaim_baru(rng, a["id_peserta_samaran"], a["id_faskes"], d, tm,
                               parafrase_berat(a["teks_resume_medis"], rng),
                               nilai=a["nilai_klaim"], tgl_keluar=tm + durasi)
                lab = "duplikat_tanggal_geser"
            k["_fraud"], k["_jenis"], k["_asal"] = True, lab, id(a)
            klaim.append(k)

    # --- 5. Beri ID urut menurut waktu, lalu petakan id_klaim_asal ---
    for i, k in enumerate(klaim):
        k["_tmp"] = i
    klaim.sort(key=lambda k: (k["tanggal_masuk"], k["periode_pengajuan"], k["_tmp"]))
    peta = {}
    for i, k in enumerate(klaim, start=1):
        k["id_klaim"] = f"KK-{i:04d}"
        peta[id(k)] = k["id_klaim"]
    for k in klaim:
        k["id_klaim_asal"] = peta[k["_asal"]] if k["_asal"] is not None else None
    return faskes, peserta, klaim


def simpan(faskes, peserta, klaim):
    C.CSV_DIR.mkdir(parents=True, exist_ok=True)
    kol_klaim = ["id_klaim", "no_episode", "id_peserta_samaran", "id_faskes", "tanggal_masuk",
                 "tanggal_keluar", "periode_pengajuan", "kode_diagnosis", "kode_tindakan",
                 "kode_inacbg", "nilai_klaim", "teks_resume_medis"]
    df = pd.DataFrame(klaim)
    df[kol_klaim].to_csv(C.CSV_DIR / "klaim.csv", index=False)
    df[["id_klaim", "_fraud", "_jenis", "id_klaim_asal"]].rename(
        columns={"_fraud": "is_fraud", "_jenis": "jenis_fraud"}).to_csv(C.CSV_DIR / "label_sintetis.csv", index=False)
    faskes.to_csv(C.CSV_DIR / "faskes.csv", index=False)
    peserta.to_csv(C.CSV_DIR / "peserta.csv", index=False)


# ======================================================================
# Ringkasan + uji konsistensi (membaca ulang CSV yang baru ditulis)
# ======================================================================
def periksa():
    gagal = []

    def cek(kondisi, pesan):
        print(("  [OK]    " if kondisi else "  [GAGAL] ") + pesan)
        if not kondisi:
            gagal.append(pesan)

    klaim = pd.read_csv(C.CSV_DIR / "klaim.csv", parse_dates=["tanggal_masuk", "tanggal_keluar"])
    label = pd.read_csv(C.CSV_DIR / "label_sintetis.csv")
    faskes = pd.read_csv(C.CSV_DIR / "faskes.csv")
    peserta = pd.read_csv(C.CSV_DIR / "peserta.csv")

    print("\n=== JUMLAH BARIS ===")
    for nama, df in [("faskes", faskes), ("peserta", peserta), ("klaim", klaim), ("label_sintetis", label)]:
        print(f"  {nama:<16} {len(df):>7}")

    kembar = label[label["is_fraud"]]
    print("\n=== KLAIM KEMBAR PER JENIS ===")
    print(f"  total: {len(kembar)} dari {len(klaim)} klaim ({len(kembar) / len(klaim):.1%})")
    print(kembar["jenis_fraud"].value_counts().to_string())

    print("\n=== DISTRIBUSI DIAGNOSIS / TINDAKAN ===")
    print(klaim.groupby(["kode_diagnosis", "kode_tindakan"]).size().sort_values(ascending=False).to_string())

    print("\n=== RENTANG & NILAI ===")
    print(f"  tanggal_masuk: {klaim['tanggal_masuk'].min().date()} s.d. {klaim['tanggal_masuk'].max().date()}")
    print(f"  periode_pengajuan: {sorted(klaim['periode_pengajuan'].unique())}")
    print(f"  nilai_klaim: min Rp{klaim['nilai_klaim'].min():,} | median Rp{int(klaim['nilai_klaim'].median()):,} | max Rp{klaim['nilai_klaim'].max():,}")

    print("\n=== UJI KONSISTENSI ===")
    cek(klaim["id_klaim"].is_unique, "id_klaim unik")
    cek(set(klaim["id_peserta_samaran"]) <= set(peserta["id_peserta_samaran"]), "semua id_peserta_samaran ada di tabel peserta")
    cek(set(klaim["id_faskes"]) <= set(faskes["id_faskes"]), "semua id_faskes ada di tabel faskes")
    cek(set(label["id_klaim"]) == set(klaim["id_klaim"]), "label_sintetis ada untuk setiap klaim")
    cek((klaim["tanggal_keluar"] >= klaim["tanggal_masuk"]).all(), "tanggal_keluar >= tanggal_masuk")
    cek((klaim["nilai_klaim"] > 0).all(), "nilai_klaim > 0")
    cek(not klaim.isna().any().any(), "tidak ada nilai kosong di tabel klaim")

    m = kembar.merge(klaim, on="id_klaim").merge(
        klaim.add_suffix("_asal"), left_on="id_klaim_asal", right_on="id_klaim_asal")
    cek(len(m) == len(kembar), "setiap klaim kembar punya id_klaim_asal yang valid")
    selisih = (m["tanggal_masuk"] - m["tanggal_masuk_asal"]).dt.days
    p = m["jenis_fraud"] == "duplikat_persis"
    cek((m[p]["no_episode"] == m[p]["no_episode_asal"]).all() and (selisih[p] == 0).all(),
        "duplikat_persis: no_episode dan tanggal sama dengan asal")
    g = m["jenis_fraud"] == "duplikat_tanggal_geser"
    cek(selisih[g].between(C.GESER_HARI_MIN, C.GESER_SULIT_MAX).all() and (m[g]["no_episode"] != m[g]["no_episode_asal"]).all(),
        f"duplikat_tanggal_geser: selisih {C.GESER_HARI_MIN}-{C.GESER_SULIT_MAX} hari dan no_episode berbeda")
    c = m["jenis_fraud"] == "resume_disalin"
    cek((m[c]["id_peserta_samaran"] != m[c]["id_peserta_samaran_asal"]).all(), "resume_disalin: peserta berbeda dengan asal")
    cek((m[c]["kode_diagnosis"] == m[c]["kode_diagnosis_asal"]).all() and (m[c]["kode_tindakan"] == m[c]["kode_tindakan_asal"]).all(),
        "resume_disalin: diagnosis dan tindakan sama dengan asal")

    print("\nRINGKASAN:", "SEMUA PEMERIKSAAN LULUS" if not gagal else f"{len(gagal)} PEMERIKSAAN GAGAL")
    return not gagal


def main():
    rng = random.Random(C.SEED)
    Faker.seed(C.SEED)
    fake = Faker("id_ID")
    faskes, peserta, klaim = bangun(rng, fake)
    simpan(faskes, peserta, klaim)
    print(f"Selesai. {len(klaim)} klaim ditulis ke {C.CSV_DIR}")
    ok = periksa()
    print("Langkah berikut: python -m data.load_to_supabase" if ok else "Perbaiki dulu pemeriksaan yang GAGAL.")


if __name__ == "__main__":
    main()