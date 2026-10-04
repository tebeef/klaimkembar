import pandas as pd

from engine.preprocess import siapkan_klaim
from engine.rules import jalankan_rules
from engine.exceptions import tandai_pengecualian


def klaim(id_klaim, peserta="P-1", faskes="F-001", masuk="2026-09-01", dx="J18.9", tind="99.21",
          nilai=2_000_000, episode=None, periode="2026-09"):
    return dict(id_klaim=id_klaim, no_episode=episode or f"EP-{id_klaim}", id_peserta_samaran=peserta,
                id_faskes=faskes, tanggal_masuk=masuk, tanggal_keluar=masuk, periode_pengajuan=periode,
                kode_diagnosis=dx, kode_tindakan=tind, kode_inacbg="X-1", nilai_klaim=nilai,
                teks_resume_medis="demam batuk")


def jalankan(baris, daftar=None):
    df = siapkan_klaim(pd.DataFrame(baris))
    mask = tandai_pengecualian(df, daftar or set())
    return jalankan_rules(df, mask, 7, 14)


def test_r1_episode_sama():
    h = jalankan([klaim("A", episode="EP-1"), klaim("B", peserta="P-2", masuk="2026-09-20", dx="A09", tind="99.18",
                                                    nilai=1_000_000, episode="EP-1")])
    assert "R1" in set(h["kode_aturan"])
    assert h[h["kode_aturan"] == "R1"].iloc[0]["id_klaim"] == "B"      # yang masuk belakangan


def test_r2_tanggal_sama():
    h = jalankan([klaim("A"), klaim("B", nilai=2_100_000)])
    assert "R2" in set(h["kode_aturan"])


def test_r3_dalam_dan_luar_jendela():
    dalam = jalankan([klaim("A"), klaim("B", masuk="2026-09-06", nilai=2_100_000)])
    assert "R3" in set(dalam["kode_aturan"])
    assert "5 hari sebelumnya" in dalam[dalam["kode_aturan"] == "R3"].iloc[0]["alasan"]
    luar = jalankan([klaim("A"), klaim("B", masuk="2026-09-09", nilai=2_100_000)])   # 8 hari
    assert "R3" not in set(luar["kode_aturan"])


def test_r4_faskes_peserta_nilai_sama():
    h = jalankan([klaim("A"), klaim("B", masuk="2026-09-11", dx="A09", tind="99.18")])
    assert set(h["kode_aturan"]) == {"R4"}


def test_pengecualian_meredam_r3_r4():
    baris = [klaim("A", dx="N18.6", tind="39.95"), klaim("B", masuk="2026-09-03", dx="N18.6", tind="39.95")]
    assert len(jalankan(baris, {("N18.6", "39.95")})) == 0      # layanan rutin sah
    assert "R3" in set(jalankan(baris)["kode_aturan"])           # tanpa pengecualian -> terdeteksi