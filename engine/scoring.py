import pandas as pd
import config as C

def tingkat_risiko(skor):
    skor = float(skor) if pd.notna(skor) else 0.0
    if skor >= C.BATAS_RISIKO_TINGGI: return "tinggi"
    if skor >= C.BATAS_RISIKO_SEDANG: return "sedang"
    return "rendah"

def gabung_dan_skoring(df_berulang, df_cloning, params):
    dfs = [df for df in [df_berulang, df_cloning] if not df.empty]
    if not dfs:
        return pd.DataFrame(columns=['id_klaim', 'skor_risiko', 'jenis_indikasi', 'kode_aturan', 'kemiripan_teks', 'kemiripan_kode', 'id_klaim_pasangan', 'alasan'])
        
    gabung = pd.concat(dfs, ignore_index=True)
    gabung = gabung.sort_values('skor_risiko', ascending=False)
    hasil = gabung.drop_duplicates(subset=['id_klaim']).copy()
    
    id_berulang = set(df_berulang['id_klaim']) if not df_berulang.empty else set()
    id_cloning = set(df_cloning['id_klaim']) if not df_cloning.empty else set()
    keduanya = id_berulang.intersection(id_cloning)
    
    def set_jenis(r):
        return 'Berulang + Jiplakan' if r['id_klaim'] in keduanya else r['jenis_indikasi']
        
    def set_skor(r):
        return min(100, r['skor_risiko'] + C.BONUS_GABUNGAN) if r['id_klaim'] in keduanya else r['skor_risiko']
        
    hasil['jenis_indikasi'] = hasil.apply(set_jenis, axis=1)
    hasil['skor_risiko'] = hasil.apply(set_skor, axis=1)
    
    return hasil