import pandas as pd
from engine.rules import jalankan_rules
from engine.similarity import jalankan_kemiripan
from engine.scoring import gabung_dan_skoring

def scan_claim(klaim_dict, df_klaim_lama, df_pengecualian, params):
    klaim_dict['id_klaim'] = 'KLAIM_BARU_TEMP'
    df_baru = pd.DataFrame([klaim_dict])
    df_gabung = pd.concat([df_klaim_lama, df_baru], ignore_index=True)
    
    # Jalankan ulang modul pada data yang sudah ditempel klaim baru
    hasil_r = jalankan_rules(df_gabung, df_pengecualian, params)
    hasil_c = jalankan_kemiripan(df_gabung, params)
    hasil_akhir = gabung_dan_skoring(hasil_r, hasil_c, params)
    
    # Ambil hasil spesifik milik klaim baru
    cek = hasil_akhir[hasil_akhir['id_klaim'] == 'KLAIM_BARU_TEMP']
    if not cek.empty:
        baris = cek.iloc[0].to_dict()
        baris['id_klaim'] = None 
        return baris
        
    return {
        'skor_risiko': 0, 'jenis_indikasi': None, 'kode_aturan': None,
        'kemiripan_teks': None, 'kemiripan_kode': None, 'id_klaim_pasangan': None, 'alasan': None
    }