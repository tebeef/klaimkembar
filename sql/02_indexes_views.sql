-- Index
create index if not exists idx_peserta_nama_lower
    on peserta (lower(nama_peserta) text_pattern_ops);

create index if not exists idx_klaim_peserta     on klaim (id_peserta_samaran);
create index if not exists idx_klaim_diagnosis   on klaim (kode_diagnosis);
create index if not exists idx_klaim_tgl_masuk   on klaim (tanggal_masuk);
create index if not exists idx_klaim_faskes      on klaim (id_faskes);
create index if not exists idx_klaim_no_episode  on klaim (no_episode);

-- Untuk aturan R2 dan R3 (peserta + diagnosis + tindakan sama)
create index if not exists idx_klaim_peserta_dx_tindakan
    on klaim (id_peserta_samaran, kode_diagnosis, kode_tindakan);

create index if not exists idx_hasil_skor        on hasil_deteksi (skor_risiko desc);
create index if not exists idx_keputusan_klaim   on keputusan (id_klaim, waktu desc);
create index if not exists idx_audit_waktu       on audit_log (waktu desc);

-- View gabungan untuk daftar dan detail klaim.

create or replace view v_klaim_lengkap as
select
    k.id_klaim,
    k.no_episode,
    k.id_peserta_samaran,
    p.nama_peserta,
    k.id_faskes,
    f.nama_faskes,
    f.jenis_faskes,
    f.kota,
    k.tanggal_masuk,
    k.tanggal_keluar,
    k.periode_pengajuan,
    k.kode_diagnosis,
    k.kode_tindakan,
    k.kode_inacbg,
    k.nilai_klaim,
    k.teks_resume_medis,
    k.sumber,
    h.skor_risiko,
    h.jenis_indikasi,
    h.kode_aturan,
    h.kemiripan_teks,
    h.kemiripan_kode,
    h.id_klaim_pasangan,
    h.alasan,
    h.dihitung_pada,
    case kt.keputusan
        when 'disetujui' then 'Disetujui'
        when 'ditunda'   then 'Ditunda'
        when 'ditolak'   then 'Ditolak'
        else 'Belum ditinjau'
    end as status_tinjauan,
    kt.waktu as waktu_keputusan
from klaim k
join peserta p on p.id_peserta_samaran = k.id_peserta_samaran
join faskes  f on f.id_faskes = k.id_faskes
left join hasil_deteksi h on h.id_klaim = k.id_klaim
left join lateral (
    select kp.keputusan, kp.waktu
    from keputusan kp
    where kp.id_klaim = k.id_klaim
    order by kp.waktu desc, kp.id desc
    limit 1
) kt on true;

-- View mengikuti hak akses pemanggil (bukan pemilik), supaya RLS tetap berlaku
alter view v_klaim_lengkap set (security_invoker = true);

-- Tutup akses API publik Supabase (role anon dan authenticated).
revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;