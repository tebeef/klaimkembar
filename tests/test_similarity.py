import pandas as pd

from engine.preprocess import siapkan_klaim, normalisasi_teks
from engine.similarity import cari_kemiripan, jaccard

TEKS_A = ("pasien laki laki usia 45 tahun datang dengan keluhan demam batuk berdahak sesak napas pemeriksaan "
          "ronki basah paru kanan saturasi oksigen 91 terapi antibiotik intravena oksigen nasal kanul "
          "nebulisasi rencana observasi tiga hari rawat")
TEKS_B = TEKS_A.replace("antibiotik", "antimikroba")            # salinan dengan satu kata diganti
TEKS_C = ("pasien perempuan usia 70 tahun jatuh nyeri pinggul tidak dapat berjalan foto panggul tampak "
          "fraktur leher femur dilakukan fiksasi interna rencana fisioterapi bertahap")


def klaim(id_klaim, peserta, masuk, dx, tind, teks):
    return dict(id_klaim=id_klaim, no_episode=f"EP-{id_klaim}", id_peserta_samaran=peserta, id_faskes="F-001",
                tanggal_masuk=masuk, tanggal_keluar=masuk, periode_pengajuan="2026-09", kode_diagnosis=dx,
                kode_tindakan=tind, kode_inacbg="X-1", nilai_klaim=1_000_000, teks_resume_medis=teks)


def test_normalisasi_teks():
    assert normalisasi_teks("Pasien, TD 130/80!") == "pasien tekanan darah 130 80"


def test_jaccard():
    assert jaccard({"J18.9", "99.21"}, {"J18.9", "99.21"}) == 1.0
    assert abs(jaccard({"J18.9", "99.21"}, {"J18.9", "99.15"}) - 1 / 3) < 1e-9
    assert jaccard(set(), set()) == 0.0


def test_cosine_salinan_terdeteksi_dan_blocking():
    df = siapkan_klaim(pd.DataFrame([
        klaim("A", "P-1", "2026-09-01", "J18.9", "99.21", TEKS_A),
        klaim("B", "P-2", "2026-09-05", "J18.9", "99.21", TEKS_B),
        klaim("C", "P-3", "2026-09-05", "S72.0", "79.35", TEKS_C),     # diagnosis lain -> tidak dibandingkan
    ]))
    h = cari_kemiripan(df, 0.80, 30)
    assert len(h) == 1
    r = h.iloc[0]
    assert r["id_klaim"] == "B" and r["id_klaim_pasangan"] == "A"
    assert r["kemiripan_teks"] >= 0.80 and r["kemiripan_kode"] == 1.0


def test_peserta_sama_tidak_dibandingkan():
    df = siapkan_klaim(pd.DataFrame([
        klaim("A", "P-1", "2026-09-01", "J18.9", "99.21", TEKS_A),
        klaim("B", "P-1", "2026-09-05", "J18.9", "99.21", TEKS_B),
    ]))
    assert len(cari_kemiripan(df, 0.80, 30)) == 0


def test_di_luar_jendela_waktu():
    df = siapkan_klaim(pd.DataFrame([
        klaim("A", "P-1", "2026-06-01", "J18.9", "99.21", TEKS_A),
        klaim("B", "P-2", "2026-09-05", "J18.9", "99.21", TEKS_B),
    ]))
    assert len(cari_kemiripan(df, 0.80, 30)) == 0