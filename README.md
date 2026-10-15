# Analisis Luas Karhutla Indonesia 2018–2026

Portofolio asesmen kompetensi BNSP — skema **Analis Data (Data Analyst)**,
nomor **DSS.06.09.25**, jenis Okupasi. Delapan unit kompetensi dibuktikan lewat
satu kasus nyata: luas kebakaran hutan dan lahan di 514 kabupaten/kota,
tahun 2018 sampai 2026.

**Dashboard langsung:** https://USERNAME.github.io/karhutla-dashboard/
*(ganti `USERNAME` setelah repositori dipublikasikan — lihat `PANDUAN-PUBLISH.md`)*

---

## Isi repositori

```
index.html        dashboard interaktif (satu berkas, tanpa server)
raw/              berkas sumber asli, tidak pernah diubah
referensi/        kode_provinsi.csv — 38 kode provinsi BPS + pengelompokan pulau
src/              lima script pipeline, 01 sampai 05
data/             keluaran pipeline: model bintang, log validasi, berkas BI
dokumen/          dokumen portofolio (PDF), paparan (PPTX), panduan Power BI
run_all.py        menjalankan seluruh pipeline berurutan
```

## Cara menjalankan pipeline

```bash
pip install -r requirements.txt
python run_all.py
```

Atau satu per satu:

```bash
python src/01_kumpulkan.py
python src/02_telaah.py
python src/03_validasi.py          # berhenti dengan kode keluar 1 — ini disengaja
python src/03_validasi.py --terima-temuan V-07 --alasan "..."
python src/04_bersihkan.py
python src/05_ekspor_bi.py
```

Script 03 sengaja menghentikan pipeline ketika aturan blocker gagal. Pada
berkas ini aturan V-07 (rekonsiliasi) memang gagal, dan temuan itu hanya bisa
dilewati dengan penerimaan tertulis yang ikut tercatat di log.

## Pemetaan script ke unit kompetensi

| Script | Unit | Kode |
|---|---|---|
| `01_kumpulkan.py` | Mengumpulkan data | J.62DMI00.004.1 |
| `02_telaah.py` | Menelaah data | J.62DMI00.005.1 |
| `03_validasi.py` | Memvalidasi data | J.62DMI00.006.1 |
| `04_bersihkan.py` | Menentukan objek data · Membersihkan data | J.62DMI00.007.1 · J.62DMI00.008.1 |
| `05_ekspor_bi.py` + `index.html` | Membuat business intelligence | J.62DMS00.015.1 |

Unit J.62DMS00.001.1 (kebutuhan pengelolaan data) dan J.62DMS00.004.1
(rencana integrasi data) dibuktikan oleh dokumen portofolio di `dokumen/`,
bukan oleh kode.

## Model data

| Tabel | Granularitas | Kunci | Baris |
|---|---|---|---|
| `fakta_karhutla` | kabupaten × tahun | `(kode_kab, tahun)` | 4.626 |
| `dim_wilayah` | kabupaten/kota | `kode_kab` | 514 |
| `dim_tahun` | tahun | `tahun` | 9 |
| `audit_agregat` | tahun | `tahun` | 9 |

`audit_agregat` sengaja berada di luar relasi model bintang. Isinya baris
`Total` dari berkas sumber yang berada pada granularitas nasional, disimpan
sebagai pembanding rekonsiliasi, bukan sebagai bagian dari fakta.

## Tiga keputusan yang perlu dijelaskan saat asesmen

**Mengapa baris `Total` tidak dibuang.** Baris itu berada pada granularitas
nasional, bukan kabupaten, sehingga tidak boleh masuk tabel fakta. Tetapi
membuangnya menghilangkan pembanding untuk aturan rekonsiliasi V-07, jadi
baris itu dipindahkan ke `audit_agregat`.

**Mengapa outlier tidak dihapus.** Pada data kebakaran, nilai ekstrem adalah
peristiwa nyata dan justru menjadi objek analisis. 758 dari 4.626 nilai berada
di atas batas IQR; seluruhnya dipertahankan.

**Mengapa selisih 2023 tidak dikoreksi sendiri.** Baris agregat menunjukkan
1.161.156,91 ha sementara penjumlahan 514 baris kabupaten menghasilkan
1.006.499,86 ha — selisih 154.657,05 ha atau 13,32%. Delapan tahun lainnya
cocok persis. Memaksa angka agar cocok akan menghapus jejak masalah tanpa
menyelesaikannya, jadi temuan diteruskan ke walidata dan tahun 2023 diberi
penanda kualitas data di `dim_tahun`.

## Angka kunci untuk pengecekan silang

| Ukuran | Nilai |
|---|---|
| Baris sumber | 515 (514 kabupaten + 1 agregat) |
| Baris tabel fakta | 4.626 |
| Sel gagal konversi | 0 |
| Total nasional 2025, sebelum = sesudah | 359.619,35 ha |
| Selisih rekonsiliasi 2023 | 154.657,05 ha (13,32%) |
| Konsentrasi 20 daerah teratas | 53,8% |
| Median daerah terdampak 2025 | 208,38 ha |

## Batasan data

- Tahun 2026 masih berjalan dan belum lengkap; tidak dibandingkan langsung
  dengan tahun penuh.
- Nilai `0` tidak dapat dibedakan antara "tidak ada kejadian" dan "tidak
  dilaporkan". Diperlakukan sebagai nol sahih dan ditandai sebagai asumsi.
- Angka 2023 memakai penjumlahan baris kabupaten, bukan baris agregat sumber.

## Sumber data

Luas kebakaran hutan dan lahan per kabupaten/kota, berkas
`raw/luas-karhutla-kota.xlsx`. Data publik. Hak atas data ada pada
penerbit aslinya; kode dalam repositori ini dilisensikan MIT (lihat `LICENSE`).
