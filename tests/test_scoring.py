import pandas as pd

from engine.scoring import skor_dari_cosine, gabungkan, tingkat_risiko


def hit_rule(id_klaim, pasangan, kode="R3", skor=60):
    return pd.DataFrame([{"id_klaim": id_klaim, "id_klaim_pasangan": pasangan, "kode_aturan": kode,
                          "selisih_hari": 3, "skor_dasar": skor, "alasan": "Alasan aturan."}])


def hit_sim(id_klaim, pasangan, cos):
    return pd.DataFrame([{"id_klaim": id_klaim, "id_klaim_pasangan": pasangan, "kemiripan_teks": cos,
                          "kemiripan_kode": 1.0, "faskes_beda": True}])


KOSONG_R = hit_rule("X", "Y").iloc[0:0]
KOSONG_S = hit_sim("X", "Y", 0.9).iloc[0:0]


def test_pemetaan_cosine():
    assert skor_dari_cosine(0.80) == 50
    assert skor_dari_cosine(0.90) == 80
    assert skor_dari_cosine(1.00) == 95
    assert abs(skor_dari_cosine(0.85) - 57.5) < 1e-9
    assert skor_dari_cosine(0.79) == 0


def test_hanya_berulang():
    h = gabungkan(["K2"], hit_rule("K2", "K1"), KOSONG_S).iloc[0]
    assert h["skor_risiko"] == 60 and h["jenis_indikasi"] == "Berulang" and h["id_klaim_pasangan"] == "K1"


def test_hanya_jiplakan():
    h = gabungkan(["K2"], KOSONG_R, hit_sim("K2", "K1", 0.84)).iloc[0]
    assert h["skor_risiko"] == 56 and h["jenis_indikasi"] == "Jiplakan"
    assert "84%" in h["alasan"] and "K1" in h["alasan"]


def test_gabungan_dapat_bonus_dan_dibatasi_100():
    h = gabungkan(["K2"], hit_rule("K2", "K1"), hit_sim("K2", "K3", 0.96)).iloc[0]
    assert h["jenis_indikasi"] == "Berulang + Jiplakan" and h["skor_risiko"] == 94
    h2 = gabungkan(["K2"], hit_rule("K2", "K1", "R1", 95), hit_sim("K2", "K3", 0.99)).iloc[0]
    assert h2["skor_risiko"] == 100


def test_tanpa_indikasi_tetap_punya_baris():
    h = gabungkan(["K9"], KOSONG_R, KOSONG_S).iloc[0]
    assert h["skor_risiko"] == 0 and h["jenis_indikasi"] is None


def test_tingkat_risiko():
    assert tingkat_risiko(90) == "tinggi" and tingkat_risiko(60) == "sedang" and tingkat_risiko(10) == "rendah"