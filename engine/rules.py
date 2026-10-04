import pandas as pd
import config as C

def jalankan_rules(df, pengecualian, params):
    hasil = []
    df = df.sort_values("tanggal_masuk")
    pengecualian_set = set(zip(pengecualian['kode_diagnosis'], pengecualian['kode_tindakan']))
    pengecualian_dx_only = set(pengecualian.loc[pengecualian['kode_tindakan'] == '', 'kode_diagnosis'])

    grup = df.groupby(['id_peserta_samaran', 'kode_diagnosis', 'kode_tindakan'])
    for _, group in grup:
        if len(group) < 2: continue
        klaim_urut = group.to_dict('records')
        
        for i in range(1, len(klaim_urut)):
            baru = klaim_urut[i]
            dx, tx = baru['kode_diagnosis'], baru['kode_tindakan']
            
            # Pengecualian kronis
            if (dx, tx) in pengecualian_set or dx in pengecualian_dx_only:
                continue

            for j in range(i):
                lama = klaim_urut[j]
                selisih = (baru['tanggal_masuk'] - lama['tanggal_masuk']).days
                
                if str(baru['no_episode']).strip() == str(lama['no_episode']).strip() and baru['no_episode'] and baru['no_episode'] != '-':
                    hasil.append({'id_klaim': baru['id_klaim'], 'id_klaim_pasangan': lama['id_klaim'], 'kode_aturan': 'R1', 'skor_risiko': C.BOBOT_ATURAN['R1'], 'jenis_indikasi': 'Berulang', 'alasan': 'Nomor episode yang sama sudah pernah ditagihkan.'})
                    break
                elif selisih == 0:
                    hasil.append({'id_klaim': baru['id_klaim'], 'id_klaim_pasangan': lama['id_klaim'], 'kode_aturan': 'R2', 'skor_risiko': C.BOBOT_ATURAN['R2'], 'jenis_indikasi': 'Berulang', 'alasan': 'Peserta, diagnosis, dan tindakan identik dengan klaim pada hari yang sama.'})
                    break
                elif selisih <= int(params['jendela_r3_hari']):
                    hasil.append({'id_klaim': baru['id_klaim'], 'id_klaim_pasangan': lama['id_klaim'], 'kode_aturan': 'R3', 'skor_risiko': C.BOBOT_ATURAN['R3'], 'jenis_indikasi': 'Berulang', 'alasan': f"Peserta, diagnosis, dan tindakan identik dengan klaim {selisih} hari sebelumnya."})
                    break
    return pd.DataFrame(hasil)