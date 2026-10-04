import pandas as pd
from sklearn.metrics import precision_score, recall_score, confusion_matrix
import sys
import os

# Menambahkan root folder ke sys.path agar modul db dan config dapat diakses
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import db
import config

def run_evaluation(ambang_batas=80):
    """
    Menjalankan evaluasi hasil deteksi terhadap label sintetis.
    Hanya fungsi ini yang boleh mengakses tabel label_sintetis.
    """
    print(f"\n=== Memulai Evaluasi Model (Ambang Batas Skor: {ambang_batas}) ===")
    
    query_label = "SELECT id_klaim, is_fraud, jenis_fraud FROM label_sintetis;"
    query_hasil = "SELECT id_klaim, skor_risiko, jenis_indikasi FROM hasil_deteksi;"

    try:
        # PERBAIKAN: Memanggil fungsi get_engine() dari db.py
        mesin_db = db.get_engine()
        df_label = pd.read_sql(query_label, con=mesin_db)
        df_hasil = pd.read_sql(query_hasil, con=mesin_db)
    except Exception as e:
        print(f"Gagal mengambil data dari database Supabase: {e}")
        return

    if df_label.empty:
        print("Tabel label_sintetis kosong. Kamu harus menjalankan skrip Tahap 2 (Generate Data) terlebih dahulu.")
        return
        
    if df_hasil.empty:
        print("Tabel hasil_deteksi kosong. Kamu harus menjalankan skrip Tahap 3 (Mesin Deteksi / pipeline.py) terlebih dahulu.")
        return

    # Menggabungkan data prediksi dengan ground truth
    df_eval = pd.merge(df_label, df_hasil, on='id_klaim', how='left')

    # Klaim yang tidak ada di hasil_deteksi dianggap lolos (skor 0)
    df_eval['skor_risiko'] = df_eval['skor_risiko'].fillna(0)

    # Menentukan status prediksi berdasarkan ambang batas skor
    df_eval['prediksi_fraud'] = df_eval['skor_risiko'] >= ambang_batas
    df_eval['is_fraud'] = df_eval['is_fraud'].astype(bool)

    y_true = df_eval['is_fraud']
    y_pred = df_eval['prediksi_fraud']

    # Menghitung Metrik Kinerja
    presisi = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[False, True]).ravel()

    # Tingkat salah tanda (False Positive Rate)
    tingkat_salah_tanda = fp / (fp + tn) if (fp + tn) > 0 else 0

    print(f"[HASIL KESELURUHAN]")
    print(f"Total Klaim Dievaluasi : {len(df_eval)}")
    print(f"Ambang Batas Skor      : {ambang_batas}")
    print(f"Recall (Sensitivitas)  : {recall:.2%} (Target: >= 90% untuk duplikat persis)")
    print(f"Presisi                : {presisi:.2%}")
    print(f"Tingkat Salah Tanda    : {tingkat_salah_tanda:.2%} (FPR - klaim normal yang keliru ditandai)")

    print(f"\n[DETAIL MATRIKS KEBINGUNGAN]")
    print(f"Benar Terdeteksi (TP)  : {tp} (Berhasil ditahan)")
    print(f"Lolos (Salah/FN)       : {fn} (Fraud yang gagal terdeteksi)")
    print(f"Salah Tanda (FP)       : {fp} (Beban kerja tambahan verifikator)")
    print(f"Benar Lolos (TN)       : {tn} (Klaim normal tidak terganggu)")

    print(f"\n[EVALUASI PER JENIS KLAIM KEMBAR]")
    jenis_fraud_list = df_eval[df_eval['is_fraud'] == True]['jenis_fraud'].unique()
    
    for jenis in jenis_fraud_list:
        if pd.isna(jenis):
            continue
        df_subset = df_eval[df_eval['jenis_fraud'] == jenis]
        y_true_sub = df_subset['is_fraud']
        y_pred_sub = df_subset['prediksi_fraud']
        recall_sub = recall_score(y_true_sub, y_pred_sub, zero_division=0)
        print(f"- {jenis:<25}: Recall = {recall_sub:.2%} (dari {len(df_subset)} kasus)")

if __name__ == "__main__":
    # Menguji dengan beberapa skenario ambang batas dari config
    ambang_uji = [70, 80, 90]
    for ambang in ambang_uji:
        run_evaluation(ambang)