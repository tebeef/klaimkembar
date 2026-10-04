import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from engine.preprocess import normalisasi_teks
import config as C

def kunci_blok(dx):
    return str(dx)[:C.BLOCKING_DIAGNOSIS_KARAKTER]

def jaccard(set1, set2):
    if not set1 and not set2: return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def jalankan_kemiripan(df, params):
    hasil = []
    df['diag_block'] = df['kode_diagnosis'].apply(kunci_blok)
    df['teks_bersih'] = df['teks_resume_medis'].apply(normalisasi_teks)
    
    for diag, group in df.groupby('diag_block'):
        if len(group) < 2: continue
        group = group.reset_index()
        teks_list = group['teks_bersih'].tolist()
        
        vek = TfidfVectorizer(ngram_range=C.TFIDF_NGRAM)
        try:
            tfidf_matrix = vek.fit_transform(teks_list)
            cosine_sim = cosine_similarity(tfidf_matrix)
        except ValueError:
            continue 
            
        for i in range(len(group)):
            for j in range(i):
                if group.loc[i, 'id_peserta_samaran'] == group.loc[j, 'id_peserta_samaran']:
                    continue
                    
                sim = cosine_sim[i, j]
                if sim >= float(params['ambang_cosine_tinjau']):
                    skor = 95 if sim >= float(params['ambang_cosine_kuat']) else 80
                    hasil.append({
                        'id_klaim': group.loc[i, 'id_klaim'],
                        'id_klaim_pasangan': group.loc[j, 'id_klaim'],
                        'kode_aturan': None,
                        'skor_risiko': skor,
                        'kemiripan_teks': round(sim, 2),
                        'kemiripan_kode': jaccard({group.loc[i, 'kode_diagnosis'], group.loc[i, 'kode_tindakan']}, {group.loc[j, 'kode_diagnosis'], group.loc[j, 'kode_tindakan']}),
                        'jenis_indikasi': 'Jiplakan',
                        'alasan': f"Kemiripan resume medis {sim:.0%} dengan klaim pasien berbeda di faskes lain."
                    })
    return pd.DataFrame(hasil)