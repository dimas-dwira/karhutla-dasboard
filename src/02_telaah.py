"""
02_telaah.py  —  Unit J.62DMI00.005.1 Menelaah data

Memprofilkan data mentah sebelum satu nilai pun diubah: struktur, tipe, nilai
kosong, statistik deskriptif per tahun, jumlah nilai nol, jumlah daerah
terdampak, dan konsentrasi.

Keluaran
--------
output/laporan_telaah.txt     laporan profiling yang bisa dibaca asesor
output/statistik_tahunan.csv  statistik deskriptif per tahun
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parent.parent
INTERIM = AKAR / "interim"
OUTPUT = AKAR / "output"


def ke_angka(s: pd.Series) -> pd.Series:
    """'1.091,18' -> 1091.18  (titik = pemisah ribuan, koma = desimal)."""
    return pd.to_numeric(
        s.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def kolom_tahun(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if re.fullmatch(r"\d{4}", str(c))]


def muat_mentah() -> pd.DataFrame:
    berkas = INTERIM / "mentah.csv"
    if not berkas.exists():
        raise FileNotFoundError("Jalankan 01_kumpulkan.py lebih dulu.")
    return pd.read_csv(berkas, dtype=str)


def telaah(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    tahun = kolom_tahun(df)
    baris = []

    baris.append("=" * 72)
    baris.append("LAPORAN PENELAAHAN DATA  ·  luas-karhutla-kota.xlsx")
    baris.append("=" * 72)
    baris.append("")
    baris.append(f"Dimensi        : {df.shape[0]} baris x {df.shape[1]} kolom")
    baris.append(f"Kolom tahun    : {', '.join(tahun)}")
    baris.append("")

    baris.append("-- STRUKTUR DAN TIPE DATA " + "-" * 46)
    for k in df.columns:
        baris.append(
            f"  {k:<16} tipe={str(df[k].dtype):<8} unik={df[k].nunique():>4} "
            f"kosong={int(df[k].isna().sum()):>3}"
        )
    baris.append("")

    # Baris agregat dikenali dari Kode Wilayah yang kosong.
    agregat = df[df["Kode Wilayah"].isna()]
    rinci = df[df["Kode Wilayah"].notna()].copy()
    baris.append("-- GRANULARITAS " + "-" * 56)
    baris.append(f"  Baris rinci (kabupaten/kota) : {len(rinci)}")
    baris.append(f"  Baris agregat                : {len(agregat)}  "
                 f"{list(agregat['Kabupaten']) if len(agregat) else ''}")
    baris.append("  Catatan: baris agregat berada pada granularitas nasional,")
    baris.append("           bukan kabupaten. Mencampurnya menggandakan seluruh total.")
    baris.append("")

    for t in tahun:
        rinci[t] = ke_angka(rinci[t])

    stat = pd.DataFrame({
        "tahun": tahun,
        "total_ha": [rinci[t].sum() for t in tahun],
        "rata_rata": [rinci[t].mean() for t in tahun],
        "median": [rinci[t].median() for t in tahun],
        "maksimum": [rinci[t].max() for t in tahun],
        "p95": [rinci[t].quantile(0.95) for t in tahun],
        "jumlah_nol": [int((rinci[t] == 0).sum()) for t in tahun],
        "daerah_terdampak": [int((rinci[t] > 0).sum()) for t in tahun],
    }).round(2)

    baris.append("-- STATISTIK DESKRIPTIF PER TAHUN (hektare) " + "-" * 29)
    baris.append(stat.to_string(index=False))
    baris.append("")

    kumulatif = rinci.set_index("Kabupaten")[tahun].sum(axis=1).sort_values(ascending=False)
    baris.append("-- SEPULUH DAERAH DENGAN LUAS KUMULATIF TERBESAR " + "-" * 24)
    for i, (nama, nilai) in enumerate(kumulatif.head(10).items(), 1):
        baris.append(f"  {i:>2}. {nama:<28} {nilai:>12,.2f} ha")
    baris.append("")

    porsi20 = kumulatif.head(20).sum() / kumulatif.sum() * 100
    nol_selalu = int((rinci[tahun] == 0).all(axis=1).sum())
    baris.append("-- TEMUAN PENELAAHAN " + "-" * 51)
    baris.append(f"  1. Dua tahun puncak: 2019 ({rinci['2019'].sum():,.0f} ha) dan "
                 f"2023 ({rinci['2023'].sum():,.0f} ha).")
    baris.append(f"  2. Daerah terdampak naik dari {int((rinci[tahun[0]] > 0).sum())} "
                 f"({tahun[0]}) menjadi {int((rinci['2024'] > 0).sum())} (2024), "
                 f"sementara total luas turun.")
    baris.append(f"  3. Konsentrasi: 20 daerah teratas menanggung {porsi20:.1f}% "
                 f"dari seluruh luas terbakar.")
    baris.append(f"  4. Sebaran miring ke kanan: median 2025 "
                 f"{rinci.loc[rinci['2025'] > 0, '2025'].median():,.2f} ha "
                 f"vs maksimum {rinci['2025'].max():,.2f} ha.")
    baris.append(f"  5. {nol_selalu} kabupaten bernilai 0 sepanjang {len(tahun)} tahun "
                 f"(umumnya kota tanpa lahan terbuka).")
    baris.append("")
    baris.append("-- BATASAN " + "-" * 61)
    baris.append("  · 2026 adalah tahun berjalan dan belum lengkap.")
    baris.append("  · Nilai 0 tidak dapat dibedakan antara 'tidak ada kejadian'")
    baris.append("    dan 'tidak dilaporkan'. Diperlakukan sebagai nol sahih.")

    return stat, baris


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    df = muat_mentah()
    stat, baris = telaah(df)

    laporan = "\n".join(baris)
    (OUTPUT / "laporan_telaah.txt").write_text(laporan + "\n", encoding="utf-8")
    stat.to_csv(OUTPUT / "statistik_tahunan.csv", index=False)

    print(laporan)
    print()
    print("Tersimpan: output/laporan_telaah.txt, output/statistik_tahunan.csv")


if __name__ == "__main__":
    main()
