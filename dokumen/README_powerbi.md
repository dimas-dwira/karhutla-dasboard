# Definisi KPI untuk Power BI

Model: `fakta_karhutla` (many-to-one) ke `dim_wilayah` lewat `kode_kab`,
dan ke `dim_tahun` lewat `tahun`. `audit_agregat` tanpa relasi, khusus
halaman kualitas data.

```dax
Total Luas =
SUM ( fakta_karhutla[luas_ha] )

Daerah Terdampak =
CALCULATE (
    DISTINCTCOUNT ( fakta_karhutla[kode_kab] ),
    fakta_karhutla[luas_ha] > 0
)

Median Terdampak =
MEDIANX (
    FILTER ( fakta_karhutla, fakta_karhutla[luas_ha] > 0 ),
    fakta_karhutla[luas_ha]
)

Perubahan Tahunan % =
VAR Sebelumnya =
    CALCULATE ( [Total Luas], DATEADD ( dim_tahun[tahun], -1, YEAR ) )
RETURN
    DIVIDE ( [Total Luas] - Sebelumnya, Sebelumnya )

Konsentrasi Top10 =
DIVIDE (
    CALCULATE (
        [Total Luas],
        TOPN ( 10, ALLSELECTED ( dim_wilayah[nama_kab] ), [Total Luas] )
    ),
    CALCULATE ( [Total Luas], ALLSELECTED ( dim_wilayah ) )
)

Daerah Terbakar Berulang =
COUNTROWS (
    FILTER (
        VALUES ( dim_wilayah[kode_kab] ),
        CALCULATE (
            COUNTROWS ( FILTER ( fakta_karhutla, fakta_karhutla[luas_ha] > 0 ) )
        ) >= 7
    )
)
```

## Aturan penyajian

- Tahun 2026 selalu berlabel **data berjalan** dan dikeluarkan dari rata-rata historis.
- Angka 2023 membawa ikon peringatan yang menautkan ke halaman Kualitas Data.
- Kartu KPI menampilkan median; rata-rata tidak ditampilkan sama sekali.
- Peta memakai skala warna kuantil, bukan linear, karena sebaran sangat miring.
