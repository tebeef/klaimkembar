-- =====================================================================
-- KlaimKembar - Skema database (Supabase / PostgreSQL)
-- Semua data di sini adalah DATA SINTETIS, bukan data peserta JKN riil.
-- Aman dijalankan ulang (memakai IF NOT EXISTS).
-- =====================================================================

-- ---------------------------------------------------------------------
-- Tabel referensi

create table if not exists faskes (
    id_faskes     text primary key,
    nama_faskes   text not null,
    jenis_faskes  text not null,
    kota          text         
);

create table if not exists peserta (
    id_peserta_samaran text primary key,   
    nama_peserta       text not null       
);

create table if not exists verifikator (
    id_verifikator    text primary key,
    nama_verifikator  text not null,
    peran             text not null default 'verifikator'
                      check (peran in ('verifikator', 'admin'))
);

-- Klaim (masukan mesin deteksi)

create table if not exists klaim (
    id_klaim            text primary key,   
    no_episode          text not null,      
    id_peserta_samaran  text not null references peserta (id_peserta_samaran),
    id_faskes           text not null references faskes (id_faskes),
    tanggal_masuk       date not null,
    tanggal_keluar      date not null,
    periode_pengajuan   text not null
                        check (periode_pengajuan ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    kode_diagnosis      text not null,      -- ICD-10
    kode_tindakan       text,               -- ICD-9-CM
    kode_inacbg         text,
    nilai_klaim         bigint not null check (nilai_klaim >= 0),   -- rupiah
    teks_resume_medis   text,               
    sumber              text not null default 'sintetis',          
    dibuat_pada         timestamptz not null default now(),
    constraint ck_klaim_tanggal check (tanggal_keluar >= tanggal_masuk)
);


-- Label kebenaran data sintetis.

create table if not exists label_sintetis (
    id_klaim       text primary key references klaim (id_klaim) on delete cascade,
    is_fraud       boolean not null,
    jenis_fraud    text
                   check (jenis_fraud in ('duplikat_persis', 'duplikat_tanggal_geser', 'resume_disalin')),
    id_klaim_asal  text references klaim (id_klaim) on delete set null,
    constraint ck_label_konsisten
        check ((is_fraud and jenis_fraud is not null)
            or (not is_fraud and jenis_fraud is null))
);

-- Keluaran mesin deteksi

create table if not exists hasil_deteksi (
    id_klaim           text primary key references klaim (id_klaim) on delete cascade,
    skor_risiko        numeric(5, 2) not null check (skor_risiko between 0 and 100),
    jenis_indikasi     text
                       check (jenis_indikasi in ('Berulang', 'Jiplakan', 'Berulang + Jiplakan')),
    kode_aturan        text check (kode_aturan in ('R1', 'R2', 'R3', 'R4')),
    kemiripan_teks     numeric(5, 4) check (kemiripan_teks between 0 and 1),
    kemiripan_kode     numeric(5, 4) check (kemiripan_kode between 0 and 1),
    id_klaim_pasangan  text references klaim (id_klaim) on delete set null,  
    alasan             text,
    dihitung_pada      timestamptz not null default now()
);

-- Keputusan verifikator dan jejak audit

create table if not exists keputusan (
    id              bigint generated always as identity primary key,
    id_klaim        text not null references klaim (id_klaim) on delete cascade,
    id_verifikator  text not null references verifikator (id_verifikator),
    keputusan       text not null check (keputusan in ('disetujui', 'ditunda', 'ditolak')),
    catatan         text,
    waktu           timestamptz not null default now(),
    constraint ck_catatan_wajib
        check (keputusan = 'disetujui' or length(btrim(coalesce(catatan, ''))) > 0)
);

create table if not exists audit_log (
    id              bigint generated always as identity primary key,
    waktu           timestamptz not null default now(),
    id_verifikator  text references verifikator (id_verifikator),
    aksi            text not null,
    id_klaim        text references klaim (id_klaim) on delete set null,
    detail          jsonb not null default '{}'::jsonb
);

-- Pengaturan dan daftar pengecualian
create table if not exists pengaturan (
    kunci   text primary key,
    nilai   text not null
);

create table if not exists pengecualian_layanan (
    id              bigint generated always as identity primary key,
    kode_diagnosis  text not null,
    kode_tindakan   text,              
    keterangan      text,
    aktif           boolean not null default true
);

-- Keamanan: mengaktifkan Row Level Security pada semua tabel.
alter table faskes               enable row level security;
alter table peserta              enable row level security;
alter table verifikator          enable row level security;
alter table klaim                enable row level security;
alter table label_sintetis       enable row level security;
alter table hasil_deteksi        enable row level security;
alter table keputusan            enable row level security;
alter table audit_log            enable row level security;
alter table pengaturan           enable row level security;
alter table pengecualian_layanan enable row level security;