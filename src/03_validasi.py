"""
03_validasi.py  —  Unit J.62DMI00.006.1 Memvalidasi data

Menjalankan tujuh aturan validasi terhadap data mentah. Aturan bertingkat
"blocker" menghentikan pipeline: angka ini dipakai untuk publikasi resmi,
sehingga lebih baik berhenti daripada memuat data yang salah.

Aturan
------
V-01 Kode Wilayah tidak kosong pada baris rinci        blocker
V-02 Kode Wilayah unik                                 blocker
V-03 Kode Wilayah 4 digit numerik                      blocker
V-04 Seluruh nilai luas dapat dikonversi ke numerik    blocker
V-05 Luas tidak negatif                                blocker
V-06 Dua digit awal adalah kode provinsi sah           peringatan
V-07 Baris agregat sama dengan jumlah baris rinci      blocker

Penerimaan temuan
-----------------
V-07 GAGAL pada berkas ini (tahun 2023, selisih 154.657,05 ha). Temuan itu
tidak diperbaiki diam-diam. Untuk melanjutkan pipeline, operator harus
menerimanya secara eksplisit:

    python src/03_validasi.py --terima-temuan V-07 --alasan "..."

Penerimaan itu ikut tercatat di log validasi sebagai jejak audit.

Keluaran
--------
output/log_validasi.csv       hasil tiap aturan
output/log_rekonsiliasi.csv   selisih agregat vs rinci per tahun
Kode keluar 1 bila ada blocker yang gagal dan tidak diterima.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parent.parent
INTERIM = AKAR / "interim"
OUTPUT = AKAR / "output"
REFERENSI = AKAR / "referensi"
TOLERANSI = 0.01  # hektare


def ke_angka(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def kolom_tahun(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if re.fullmatch(r"\d{4}", str(c))]


def rekonsiliasi(agregat: pd.DataFrame, rinci: pd.DataFrame, tahun: list[str]) -> pd.DataFrame:
    baris = []
    for t in tahun:
        a = float(agregat[t].iloc[0]) if len(agregat) else float("nan")
        r = float(rinci[t].sum())
        baris.append({
            "tahun": int(t),
            "agregat_total": round(a, 2),
            "jumlah_baris_rinci": round(r, 2),
            "selisih_ha": round(a - r, 2),
            "selisih_persen": round((a - r) / a * 100, 2) if a else 0.0,
            "status": "cocok" if abs(a - r) < TOLERANSI else "TIDAK COCOK",
        })
    return pd.DataFrame(baris)


def validasi(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    tahun = kolom_tahun(df)
    kerja = df.copy()
    for t in tahun:
        kerja[t] = ke_angka(kerja[t])

    agregat = kerja[kerja["Kode Wilayah"].isna()]
    rinci = kerja[kerja["Kode Wilayah"].notna()].copy()
    kode = rinci["Kode Wilayah"].astype(str).str.strip()

    prov_sah = set(
        pd.read_csv(REFERENSI / "kode_provinsi.csv", dtype=str)["kode_prov"]
    )
    prov_data = kode.str.zfill(4).str[:2]
    tak_dikenal = sorted(set(prov_data) - prov_sah)

    kode_sah = kode.str.fullmatch(r"\d{4}")
    gagal_konversi = int(rinci[tahun].isna().sum().sum())
    negatif = int((rinci[tahun] < 0).sum().sum())

    rek = rekonsiliasi(agregat, rinci, tahun)
    tak_cocok = rek[rek["status"] == "TIDAK COCOK"]

    hasil = [
        ("V-01", "Kode Wilayah tidak kosong pada baris rinci", "blocker",
         int(kode.isna().sum()) == 0,
         f"{len(agregat)} baris tanpa kode teridentifikasi sebagai baris agregat"),
        ("V-02", "Kode Wilayah unik", "blocker",
         int(kode.duplicated().sum()) == 0,
         f"{int(kode.duplicated().sum())} duplikat dari {len(kode)} kode"),
        ("V-03", "Kode Wilayah 4 digit numerik", "blocker",
         bool(kode_sah.all()),
         f"{int(kode_sah.sum())} dari {len(kode)} sesuai "
         f"(rentang {kode.min()}–{kode.max()})"),
        ("V-04", "Seluruh nilai luas dapat dikonversi ke numerik", "blocker",
         gagal_konversi == 0,
         f"{gagal_konversi} gagal konversi dari {rinci[tahun].size} sel"),
        ("V-05", "Luas tidak negatif", "blocker",
         negatif == 0,
         f"{negatif} nilai negatif"),
        ("V-06", "Dua digit awal adalah kode provinsi sah", "peringatan",
         len(tak_dikenal) == 0,
         f"{len(set(prov_data))} kode provinsi terpakai; tak dikenal: {tak_dikenal or 'tidak ada'}"),
        ("V-07", "Baris agregat sama dengan jumlah baris rinci", "blocker",
         len(tak_cocok) == 0,
         "seluruh tahun cocok" if len(tak_cocok) == 0 else
         "; ".join(f"{int(r.tahun)} selisih {r.selisih_ha:,.2f} ha ({r.selisih_persen}%)"
                   for r in tak_cocok.itertuples())),
    ]

    log = pd.DataFrame(hasil, columns=["kode", "aturan", "tingkat", "lulus", "keterangan"])
    log.insert(0, "waktu", datetime.now().isoformat(timespec="seconds"))
    return log, rek


def main() -> None:
    ap = argparse.ArgumentParser(description="Validasi data karhutla")
    ap.add_argument("--terima-temuan", nargs="*", default=[], metavar="KODE",
                    help="Kode aturan blocker yang temuannya diterima secara sadar, mis. V-07")
    ap.add_argument("--alasan", default="", help="Alasan penerimaan, ikut dicatat di log")
    arg = ap.parse_args()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    berkas = INTERIM / "mentah.csv"
    if not berkas.exists():
        raise FileNotFoundError("Jalankan 01_kumpulkan.py lebih dulu.")
    df = pd.read_csv(berkas, dtype=str)

    log, rek = validasi(df)
    diterima = {k.upper() for k in arg.terima_temuan}
    log["diterima_operator"] = log["kode"].isin(diterima) & ~log["lulus"]
    log["alasan_penerimaan"] = log["diterima_operator"].map(lambda v: arg.alasan if v else "")

    log.to_csv(OUTPUT / "log_validasi.csv", index=False)
    rek.to_csv(OUTPUT / "log_rekonsiliasi.csv", index=False)

    print("=" * 72)
    print("03 · MEMVALIDASI DATA")
    print("=" * 72)
    for r in log.itertuples():
        tanda = "LULUS" if r.lulus else ("DITERIMA" if r.diterima_operator else "GAGAL")
        print(f"  [{tanda:^8}] {r.kode}  {r.aturan}")
        print(f"             {r.keterangan}")
    print()
    print("Rekonsiliasi agregat vs jumlah baris rinci:")
    print(rek.to_string(index=False))
    print()

    blocker_gagal = log[(log["tingkat"] == "blocker") & (~log["lulus"]) & (~log["diterima_operator"])]
    if len(blocker_gagal):
        print("PIPELINE DIHENTIKAN — aturan blocker gagal dan belum diterima:")
        for r in blocker_gagal.itertuples():
            print(f"  {r.kode}  {r.aturan}")
        print()
        print("Laporkan temuan ke walidata. Bila keputusan sudah diambil untuk")
        print("melanjutkan dengan penanda kualitas data, jalankan ulang dengan:")
        print('  python src/03_validasi.py --terima-temuan V-07 --alasan "<alasan>"')
        sys.exit(1)

    if (log["diterima_operator"]).any():
        print("Pipeline dilanjutkan dengan penerimaan temuan yang tercatat di log.")
    print("Tersimpan: output/log_validasi.csv, output/log_rekonsiliasi.csv")


if __name__ == "__main__":
    main()
