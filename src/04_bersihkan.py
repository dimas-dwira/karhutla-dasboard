"""
04_bersihkan.py  —  Unit J.62DMI00.008.1 Membersihkan Data
                    Unit J.62DMI00.007.1 Menentukan objek data

Membentuk model bintang pada granularitas satu kabupaten/kota dalam satu tahun,
kunci utama gabungan (kode_kab, tahun).

Enam keputusan pembersihan
--------------------------
1. Baris agregat 'Total' dipindahkan ke audit_agregat, tidak dibuang, supaya
   aturan rekonsiliasi V-07 tetap punya pembanding pada setiap muat.
2. Angka berformat Indonesia dikonversi ke float.
3. Nama kolom tahun dinormalisasi ke string.
4. Spasi ganda pada nama daerah dirapatkan (mis. 'KOTA BANDA  ACEH').
5. Nama daerah dibakukan ke Title Case untuk label dashboard.
6. Struktur wide di-unpivot menjadi long.

Yang sengaja TIDAK diubah: nilai 0 (nol sahih), nilai ekstrem di atas batas IQR
(peristiwa nyata, justru objek analisis), selisih 2023, dan nilai 2026 parsial.

Keluaran
--------
output/fakta_karhutla.csv  output/dim_wilayah.csv
output/dim_tahun.csv       output/audit_agregat.csv
output/ringkasan_pembersihan.csv
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parent.parent
INTERIM = AKAR / "interim"
OUTPUT = AKAR / "output"
REFERENSI = AKAR / "referensi"
TAHUN_PARSIAL = {2026}  # tahun berjalan saat data ditarik


def angka_id(x: float) -> str:
    """1234567.89 -> '1.234.567,89' (format Indonesia)."""
    return f"{x:,.2f}".replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")


def ke_angka(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def rapikan_nama(s: pd.Series) -> pd.Series:
    return s.str.strip().str.replace(r"\s+", " ", regex=True).str.title()


def kolom_tahun(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if re.fullmatch(r"\d{4}", str(c))]


def bersihkan(mentah: pd.DataFrame):
    df = mentah.copy()
    df.columns = [str(c).strip() for c in df.columns]
    tahun = kolom_tahun(df)

    # 1 · pisahkan granularitas
    agregat = df[df["Kode Wilayah"].isna()].copy()
    rinci = df[df["Kode Wilayah"].notna()].copy()

    # 2 · konversi angka
    for t in tahun:
        rinci[t] = ke_angka(rinci[t])
        agregat[t] = ke_angka(agregat[t])

    # 4 & 5 · bakukan nama, 3 · kunci 4 digit
    rinci["kode_kab"] = rinci["Kode Wilayah"].astype(str).str.strip().str.zfill(4)
    rinci["nama_kab"] = rapikan_nama(rinci["Kabupaten"])

    # dimensi wilayah, provinsi diturunkan dari kode (tidak bisa tidak konsisten)
    ref = pd.read_csv(REFERENSI / "kode_provinsi.csv", dtype={"kode_prov": str})
    dim_wilayah = rinci[["kode_kab", "nama_kab"]].copy()
    dim_wilayah["kode_prov"] = dim_wilayah["kode_kab"].str[:2]
    dim_wilayah = dim_wilayah.merge(ref, on="kode_prov", how="left")
    dim_wilayah["tipe_wilayah"] = dim_wilayah["nama_kab"].str.startswith("Kota ").map(
        {True: "Kota", False: "Kabupaten"}
    )

    # 6 · unpivot wide -> long
    fakta = (
        rinci.melt(id_vars=["kode_kab"], value_vars=tahun, var_name="tahun", value_name="luas_ha")
        .astype({"tahun": int})
        .sort_values(["kode_kab", "tahun"])
        .reset_index(drop=True)
    )
    fakta["luas_ha"] = fakta["luas_ha"].round(2)
    fakta["sumber_berkas"] = "luas-karhutla-kota.xlsx"
    fakta["tanggal_muat"] = date.today().isoformat()

    dim_tahun = pd.DataFrame({"tahun": [int(t) for t in tahun]})
    dim_tahun["status_kelengkapan"] = dim_tahun["tahun"].map(
        lambda t: "parsial" if t in TAHUN_PARSIAL else "lengkap"
    )
    dim_tahun["catatan_kualitas"] = ""

    # tandai tahun yang rekonsiliasinya tidak cocok
    for t in tahun:
        a = float(agregat[t].iloc[0]) if len(agregat) else float("nan")
        r = float(rinci[t].sum())
        if abs(a - r) >= 0.01:
            dim_tahun.loc[dim_tahun["tahun"] == int(t), "catatan_kualitas"] = (
                f"Selisih agregat {angka_id(a - r)} ha belum terjelaskan. "
                f"Angka memakai penjumlahan baris kabupaten."
            )

    audit = agregat.melt(
        id_vars=["Kabupaten"], value_vars=tahun, var_name="tahun", value_name="agregat_ha"
    ).astype({"tahun": int})[["tahun", "agregat_ha"]].sort_values("tahun").reset_index(drop=True)

    return fakta, dim_wilayah, dim_tahun, audit, rinci, tahun


def ringkasan(mentah: pd.DataFrame, fakta, dim_wilayah, dim_tahun, rinci, tahun) -> pd.DataFrame:
    nama_asli = mentah["Kabupaten"].dropna()
    tak_baku = int(((nama_asli.str.strip() != nama_asli) | nama_asli.str.contains(r"\s{2,}")).sum())
    baris = [
        ("Bentuk tabel", f"Wide, {mentah.shape[0]} x {mentah.shape[1]}",
         f"Long, {fakta.shape[0]} x {fakta.shape[1]}"),
        ("Baris kabupaten/kota", f"{mentah.shape[0]} termasuk agregat", f"{len(dim_wilayah)}"),
        ("Tipe kolom luas", "object (teks)", str(fakta["luas_ha"].dtype)),
        ("Nilai kosong", str(int(mentah.isna().sum().sum())), str(int(fakta["luas_ha"].isna().sum()))),
        ("Nama daerah tidak baku", str(tak_baku), "0"),
        ("Kolom provinsi", "Tidak ada", f"Ada — {dim_wilayah['nama_prov'].nunique()} provinsi"),
        ("Penanda kelengkapan tahun", "Tidak ada",
         f"{(dim_tahun.status_kelengkapan == 'lengkap').sum()} lengkap + "
         f"{(dim_tahun.status_kelengkapan == 'parsial').sum()} parsial"),
        ("Total nasional 2025 (uji silang)", f"{rinci['2025'].sum():,.2f}",
         f"{fakta.loc[fakta.tahun == 2025, 'luas_ha'].sum():,.2f}"),
    ]
    return pd.DataFrame(baris, columns=["ukuran", "sebelum", "sesudah"])


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    berkas = INTERIM / "mentah.csv"
    if not berkas.exists():
        raise FileNotFoundError("Jalankan 01_kumpulkan.py lebih dulu.")
    mentah = pd.read_csv(berkas, dtype=str)

    fakta, dim_wilayah, dim_tahun, audit, rinci, tahun = bersihkan(mentah)
    rk = ringkasan(mentah, fakta, dim_wilayah, dim_tahun, rinci, tahun)

    fakta.to_csv(OUTPUT / "fakta_karhutla.csv", index=False)
    dim_wilayah.to_csv(OUTPUT / "dim_wilayah.csv", index=False)
    dim_tahun.to_csv(OUTPUT / "dim_tahun.csv", index=False)
    audit.to_csv(OUTPUT / "audit_agregat.csv", index=False)
    rk.to_csv(OUTPUT / "ringkasan_pembersihan.csv", index=False)

    print("=" * 72)
    print("04 · MEMBERSIHKAN DATA")
    print("=" * 72)
    print(rk.to_string(index=False))
    print()
    # uji penutup: tidak boleh ada nilai yang hilang atau berubah
    for t in tahun:
        sebelum = round(float(rinci[t].sum()), 2)
        sesudah = round(float(fakta.loc[fakta.tahun == int(t), "luas_ha"].sum()), 2)
        assert abs(sebelum - sesudah) < 0.01, f"Total {t} berubah: {sebelum} -> {sesudah}"
    print(f"Uji penutup LULUS — total {len(tahun)} tahun identik sebelum dan sesudah.")
    print()
    print("Tersimpan: fakta_karhutla.csv, dim_wilayah.csv, dim_tahun.csv,")
    print("           audit_agregat.csv, ringkasan_pembersihan.csv")


if __name__ == "__main__":
    main()
