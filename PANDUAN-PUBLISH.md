# Panduan Publikasi ke GitHub Pages

Dashboard di repositori ini adalah satu berkas HTML tanpa server, jadi cukup
diunggah ke GitHub dan dinyalakan Pages-nya. Tidak perlu membeli domain,
tidak perlu hosting berbayar. Setelah selesai, alamatnya berbentuk:

```
https://USERNAME.github.io/karhutla-dashboard/
```

Ada dua jalur. Pilih **Jalur A** kalau Anda ingin lewat tampilan web saja
(paling mudah), atau **Jalur B** kalau Anda sudah terbiasa dengan Git.

---

## Persiapan: akun GitHub

Kalau belum punya, daftar gratis di https://github.com/signup. Catat
**username** Anda — nama itu akan muncul di alamat dashboard.

---

## Jalur A — lewat tampilan web (tanpa perintah apa pun)

### 1. Buat repositori baru

1. Buka https://github.com/new
2. **Repository name:** `karhutla-dashboard`
3. **Description:** `Dashboard analisis luas karhutla Indonesia 2018-2026`
4. Pilih **Public** — GitHub Pages gratis hanya untuk repositori publik.
5. **Jangan** centang "Add a README file" (repositori ini sudah punya).
6. Klik **Create repository**.

### 2. Unggah isi folder

1. Di halaman repositori yang baru dibuat, klik tautan
   **uploading an existing file**.
2. Ekstrak dulu `karhutla-dashboard.zip` di komputer Anda.
3. Buka folder hasil ekstrak, **blok seluruh isinya** (Ctrl+A), lalu
   seret ke area unggah di browser. Yang diseret adalah **isi** folder,
   bukan foldernya.
4. Tunggu sampai semua berkas terbaca (sekitar 25 berkas, 2,5 MB).
5. Pada kotak **Commit changes**, tulis `Unggah dashboard dan pipeline`.
6. Klik **Commit changes**.

> **Catatan berkas tersembunyi.** Berkas `.nojekyll` kadang tidak ikut
> terseret karena namanya diawali titik. Kalau tidak ikut, buat manual:
> klik **Add file → Create new file**, isi nama berkas dengan `.nojekyll`,
> biarkan isinya kosong, lalu **Commit changes**. Berkas ini memberi tahu
> GitHub agar tidak memproses situs dengan Jekyll.

### 3. Nyalakan GitHub Pages

1. Di repositori, klik tab **Settings**.
2. Pada menu kiri, klik **Pages**.
3. Bagian **Build and deployment → Source**, pilih **Deploy from a branch**.
4. Bagian **Branch**, pilih `main` dan folder `/ (root)`.
5. Klik **Save**.

### 4. Tunggu dan buka

Proses penerbitan berjalan 1–3 menit. Segarkan halaman **Settings → Pages**;
begitu selesai akan muncul kotak hijau berisi alamat:

```
Your site is live at https://USERNAME.github.io/karhutla-dashboard/
```

Klik alamat itu. Dashboard akan terbuka.

---

## Jalur B — lewat Git di terminal

Prasyarat: Git sudah terpasang dan sudah login (`gh auth login` atau SSH key).

```bash
# ekstrak dan masuk ke foldernya
unzip karhutla-dashboard.zip -d karhutla-dashboard
cd karhutla-dashboard

git init
git add -A
git commit -m "Dashboard dan pipeline analisis karhutla 2018-2026"
git branch -M main
```

Dengan GitHub CLI (`gh`), satu perintah sudah membuat repositori sekaligus
mengunggah:

```bash
gh repo create karhutla-dashboard --public --source=. --remote=origin --push
gh api -X POST repos/:owner/karhutla-dashboard/pages \
  -f "source[branch]=main" -f "source[path]=/"
```

Tanpa `gh`, buat dulu repositori kosong di https://github.com/new
(nama `karhutla-dashboard`, Public, tanpa README), lalu:

```bash
git remote add origin https://github.com/USERNAME/karhutla-dashboard.git
git push -u origin main
```

Kemudian nyalakan Pages lewat **Settings → Pages** seperti langkah 3 di
Jalur A.

---

## Setelah terbit

### Perbarui tautan di README

Buka `README.md` di GitHub, klik ikon pensil, ganti `USERNAME` pada baris
**Dashboard langsung** dengan username Anda, lalu commit. Alamat itu yang
Anda cantumkan di berkas portofolio asesmen.

### Memperbarui data nanti

Jalankan ulang pipeline, lalu ganti `index.html` dan isi `data/` di
repositori. Lewat web: buka berkasnya, klik ikon pensil atau
**Add file → Upload files** untuk menimpa. Lewat Git:

```bash
git add -A && git commit -m "Perbarui data" && git push
```

Pages akan menerbitkan ulang otomatis dalam satu sampai dua menit.

---

## Kalau ada masalah

| Gejala | Penyebab biasanya | Perbaikan |
|---|---|---|
| Halaman 404 | Pages belum selesai terbit, atau `index.html` tidak di akar | Tunggu 3 menit; pastikan `index.html` terlihat di halaman depan repositori, bukan di dalam subfolder |
| Halaman tampil polos tanpa gaya | Berkas `.nojekyll` tidak ikut terunggah | Buat `.nojekyll` kosong di akar repositori |
| Isi seluruh folder masuk ke subfolder | Yang diseret foldernya, bukan isinya | Hapus subfolder itu, unggah ulang isinya |
| Menu **Pages** tidak ada | Repositori dibuat Private | **Settings → General → Danger Zone → Change visibility → Public** |
| Dashboard kosong di ponsel lama | Peramban terlalu tua | Buka dengan Chrome atau Safari versi terbaru |

### Catatan privasi

Repositori publik berarti seluruh isinya — termasuk `raw/` dan `dokumen/` —
dapat diakses siapa saja. Data karhutla ini memang data publik. Kalau
nanti ada berkas yang tidak boleh terbuka, keluarkan dulu dari folder
sebelum diunggah.
