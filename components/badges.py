"""badges.py - badge jenis indikasi, status, tingkat risiko, dan bar skor berwarna (HTML aman)."""
import html
import pandas as pd
import config as C
from engine.scoring import tingkat_risiko

STATUS_WARNA = {
    "Disetujui": ("#D1FAE5", "#065F46"),
    "Ditunda": ("#FEF3C7", "#92400E"),
    "Ditolak": ("#FEE2E2", "#991B1B"),
    C.STATUS_BELUM: ("#E2E8F0", "#475569"),
}

TINGKAT_WARNA = {
    "tinggi": ("#FEE2E2", "#991B1B", C.WARNA["risiko_tinggi"]),
    "sedang": ("#FEF9C3", "#854D0E", C.WARNA["risiko_sedang"]),
    "rendah": ("#D1FAE5", "#065F46", C.WARNA["risiko_rendah"]),
}

def _badge(teks, latar, warna):
    return f"<span class='kk-badge' style='background:{latar};color:{warna}'>{html.escape(str(teks))}</span>"

def badge_jenis(jenis):
    if jenis is None or (isinstance(jenis, float) and pd.isna(jenis)) or not jenis:
        return _badge("Tidak ada indikasi", "#E2E8F0", "#475569")
    return _badge(jenis, C.WARNA_JENIS.get(jenis, C.WARNA["biru"]), "#FFFFFF")

def badge_status(status):
    latar, teks = STATUS_WARNA.get(status, STATUS_WARNA[C.STATUS_BELUM])
    return _badge(status, latar, teks)

def badge_tingkat(skor):
    t = tingkat_risiko(skor)
    latar, teks, _ = TINGKAT_WARNA[t]
    return _badge(f"Risiko {t}", latar, teks)

def bar_skor(skor):
    """Bar berwarna: tinggi merah lembut, sedang kuning, rendah hijau."""
    skor = int(max(0, min(100, skor)))
    warna = TINGKAT_WARNA[tingkat_risiko(skor)][2]
    return (f"<div class='kk-skor'><div class='kk-bar'><div class='kk-bar-fill' style='width:{skor}%;background:{warna}'></div></div>"
            f"<span class='kk-bar-num'>{skor}</span></div>")