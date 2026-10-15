"""
05_ekspor_bi.py  —  Unit J.62DMS00.015.1 Membuat Business Intelligence

Menghitung enam KPI dari model bintang dan mengekspor berkas siap pakai untuk
Power BI / Looker Studio.

Mengapa median, bukan rata-rata
-------------------------------
Sebaran luas terbakar sangat miring ke kanan: median kabupaten terdampak 2025
hanya 208 ha sementara nilai tertinggi 48.164 ha. Rata-rata nasional akan
menyesatkan pengguna dashboard, jadi tidak ditampilkan sama sekali.

Keluaran
--------
bi/kpi_tahunan.csv       enam KPI per tahun
bi/peringkat_daerah.csv  peringkat kabupaten dengan share nasional
bi/ringkasan_provinsi.csv
bi/README_powerbi.md     definisi KPI dan formula DAX
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parent.parent
OUTPUT = AKAR / "output"
BI = AKAR / "bi"
AMBANG_BERULANG = 7  # terbakar pada minimal 7 dari 9 tahun


def muat():
    perlu = ["fakta_karhutla.csv", "dim_wilayah.csv", "dim_tahun.csv"]
    for n in perlu:
        if not (OUTPUT / n).exists():
            raise FileNotFoundError("Jalankan 04_bersihkan.py lebih dulu.")
    fakta = pd.read_csv(OUTPUT / "fakta_karhutla.csv", dtype={"kode_kab": str})
    wil = pd.read_csv(OUTPUT / "dim_wilayah.csv", dtype={"kode_kab": str, "kode_prov": str})
    thn = pd.read_csv(OUTPUT / "dim_tahun.csv")
    return fakta, wil, thn


def kpi_tahunan(fakta: pd.DataFrame, thn: pd.DataFrame) -> pd.DataFrame:
    g = fakta.groupby("tahun")
    out = pd.DataFrame({
        "tahun": g.size().index,
        "total_luas_ha": g["luas_ha"].sum().round(2).values,
        "daerah_terdampak": g.apply(lambda d: int((d.luas_ha > 0).sum()), include_groups=False).values,
        "median_daerah_terdampak": g.apply(
            lambda d: round(float(d.loc[d.luas_ha > 0, "luas_ha"].median()), 2), include_groups=False
        ).values,
    })
    out["perubahan_tahunan_persen"] = (out["total_luas_ha"].pct_change() * 100).round(1)
    # konsentrasi: porsi 10 kabupaten terbesar terhadap total tahun itu
    out["konsentrasi_10_besar_persen"] = [
        round(
            fakta[fakta.tahun == t].nlargest(10, "luas_ha")["luas_ha"].sum()
            / fakta[fakta.tahun == t]["luas_ha"].sum() * 100, 1
        )
        for t in out["tahun"]
    ]
    return out.merge(thn, on="tahun", how="left")


def peringkat(fakta: pd.DataFrame, wil: pd.DataFrame) -> pd.DataFrame:
    kum = fakta.groupby("kode_kab", as_index=False)["luas_ha"].sum().rename(
        columns={"luas_ha": "luas_kumulatif_ha"}
    )
    terakhir = fakta["tahun"].max()
    thn_penuh = fakta[fakta.tahun < terakhir] if terakhir == 2026 else fakta
    berulang = (
        thn_penuh[thn_penuh.luas_ha > 0]
        .groupby("kode_kab", as_index=False)
        .size()
        .rename(columns={"size": "tahun_terbakar"})
    )
    p = (
        wil.merge(kum, on="kode_kab", how="left")
        .merge(berulang, on="kode_kab", how="left")
        .fillna({"tahun_terbakar": 0})
    )
    p["tahun_terbakar"] = p["tahun_terbakar"].astype(int)
    p["share_nasional_persen"] = (
        p["luas_kumulatif_ha"] / p["luas_kumulatif_ha"].sum() * 100
    ).round(3)
    p["terbakar_berulang"] = p["tahun_terbakar"] >= AMBANG_BERULANG
    p = p.sort_values("luas_kumulatif_ha", ascending=False).reset_index(drop=True)
    p.insert(0, "peringkat", range(1, len(p) + 1))
    return p


def per_provinsi(fakta: pd.DataFrame, wil: pd.DataFrame) -> pd.DataFrame:
    g = fakta.merge(wil[["kode_kab", "nama_prov", "pulau"]], on="kode_kab", how="left")
    out = g.groupby(["pulau", "nama_prov"], as_index=False)["luas_ha"].sum()
    out["luas_ha"] = out["luas_ha"].round(2)
    return out.sort_values("luas_ha", ascending=False).reset_index(drop=True)


DAX = """# Definisi KPI untuk Power BI

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
"""


def main() -> None:
    BI.mkdir(parents=True, exist_ok=True)
    fakta, wil, thn = muat()

    kpi = kpi_tahunan(fakta, thn)
    rank = peringkat(fakta, wil)
    prov = per_provinsi(fakta, wil)

    kpi.to_csv(BI / "kpi_tahunan.csv", index=False)
    rank.to_csv(BI / "peringkat_daerah.csv", index=False)
    prov.to_csv(BI / "ringkasan_provinsi.csv", index=False)
    (BI / "README_powerbi.md").write_text(DAX, encoding="utf-8")

    print("=" * 72)
    print("05 · MEMBUAT BUSINESS INTELLIGENCE")
    print("=" * 72)
    print(kpi[["tahun", "total_luas_ha", "daerah_terdampak", "median_daerah_terdampak",
               "perubahan_tahunan_persen", "konsentrasi_10_besar_persen",
               "status_kelengkapan"]].to_string(index=False))
    print()
    print("Sepuluh daerah dengan luas kumulatif terbesar:")
    print(rank.head(10)[["peringkat", "nama_kab", "nama_prov", "luas_kumulatif_ha",
                         "share_nasional_persen", "tahun_terbakar"]].to_string(index=False))
    print()
    porsi20 = rank.head(20)["share_nasional_persen"].sum()
    print(f"Konsentrasi 20 daerah teratas : {porsi20:.1f}% dari seluruh luas terbakar")
    print(f"Daerah terbakar berulang      : {int(rank['terbakar_berulang'].sum())} kabupaten "
          f"(> 0 ha pada >= {AMBANG_BERULANG} dari 8 tahun penuh)")
    print()
    print("Tersimpan: bi/kpi_tahunan.csv, bi/peringkat_daerah.csv,")
    print("           bi/ringkasan_provinsi.csv, bi/README_powerbi.md")


if __name__ == "__main__":
    main()
