import re
import config as C

def normalisasi_teks(teks):
    if not isinstance(teks, str) or not teks: 
        return ""
    t = teks.lower()
    t = re.sub(r'[^\w\s]', ' ', t) # Hapus tanda baca
    kata = t.split()
    kata = [C.SINGKATAN.get(k, k) for k in kata]
    return " ".join(kata)