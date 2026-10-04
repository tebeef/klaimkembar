"""
highlight.py - sorotan kuning bagian identik antara dua resume (difflib tingkat kata).
Semua teks asli di-ESCAPE HTML sebelum disisipi <mark>, supaya aman dari injeksi.
"""
import html
import re
import difflib
import config as C

_POLA_KATA = re.compile(r"\S+\s*")

def _kunci(token):
    return token.strip().lower().strip(".,;:!?()[]\"'")

def _render(token, tanda):
    """Gabungkan token berurutan dengan status sama; rangkaian identik dibungkus <mark>."""
    keluar, i = [], 0
    while i < len(token):
        j = i
        while j < len(token) and tanda[j] == tanda[i]:
            j += 1
        teks = "".join(token[i:j])
        if tanda[i]:
            inti = teks.rstrip()
            keluar.append(f"<mark>{html.escape(inti)}</mark>{html.escape(teks[len(inti):])}")
        else:
            keluar.append(html.escape(teks))
        i = j
    return "".join(keluar)

def sorot_identik(teks_a, teks_b, min_kata=None):
    """Mengembalikan (html_a, html_b) dengan bagian identik disorot kuning."""
    min_kata = C.MIN_KATA_SOROTAN if min_kata is None else min_kata
    ta, tb = _POLA_KATA.findall(teks_a or ""), _POLA_KATA.findall(teks_b or "")
    ka, kb = [_kunci(t) for t in ta], [_kunci(t) for t in tb]
    cocok = difflib.SequenceMatcher(None, ka, kb, autojunk=False).get_matching_blocks()
    tanda_a, tanda_b = [False] * len(ta), [False] * len(tb)
    for i, j, n in cocok:
        if n >= min_kata:
            for x in range(i, i + n):
                tanda_a[x] = True
            for y in range(j, j + n):
                tanda_b[y] = True
    return _render(ta, tanda_a), _render(tb, tanda_b)

def teks_aman(teks):
    """Resume tanpa sorotan, tetap di-escape."""
    return html.escape(teks or "")