"""
01_kumpulkan.py  —  Unit J.62DMI00.004.1 Mengumpulkan data

Menarik berkas sumber sekali jalan, membaca SELURUH kolom sebagai teks, lalu
mencatat jejak akuisisi (hash, jumlah baris, jumlah kolom, sel kosong).

Mengapa dtype=str
-----------------
pandas menebak tipe tiap kolom. Angka berformat Indonesia seperti "1.091,18"
bisa ditafsirkan sebagai 1091 (titik dianggap pemisah desimal) atau menjadi NaN.
Dengan membaca apa adanya, keputusan konversi menjadi eksplisit dan
terdokumentasi di 04_bersihkan.py, bukan terjadi diam-diam di sini.

Keluaran
--------
interim/mentah.csv        salinan data mentah apa adanya (semua kolom teks)
interim/log_akuisisi.json catatan akuisisi untuk jejak audit
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parent.parent
SUMBER = AKAR / "raw" / "luas-karhutla-kota.xlsx"
INTERIM = AKAR / "interim"
NAMA_SHEET = "data"


def sidik_jari(path: Path) -> str:
    """SHA-256 berkas sumber, supaya perubahan berkas dapat dibuktikan."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def kumpulkan(sumber: Path = SUMBER) -> pd.DataFrame:
    """Baca berkas sumber sebagai teks murni dan rapikan nama kolomnya saja."""
    if not sumber.exists():
        raise FileNotFoundError(f"Berkas sumber tidak ditemukan: {sumber}")
    df = pd.read_excel(sumber, sheet_name=NAMA_SHEET, dtype=str)
    # Header kolom tahun tidak seragam tipenya pada berkas ini:
    # '2018' terbaca teks, 2019-2026 terbaca bilangan bulat. Samakan ke string
    # supaya perulangan atas kolom tahun tidak gagal di script berikutnya.
    df.columns = [str(c).strip() for c in df.columns]
    return df


def tulis_log(df: pd.DataFrame, sumber: Path, tujuan: Path) -> dict:
    log = {
        "waktu_tarik": datetime.now().isoformat(timespec="seconds"),
        "berkas": sumber.name,
        "sheet": NAMA_SHEET,
        "sha256": sidik_jari(sumber),
        "jumlah_baris": int(df.shape[0]),
        "jumlah_kolom": int(df.shape[1]),
        "nama_kolom": list(df.columns),
        "sel_kosong": int(df.isna().sum().sum()),
        "kolom_dengan_kosong": {
            k: int(v) for k, v in df.isna().sum().items() if v > 0
        },
    }
    tujuan.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    return log


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    df = kumpulkan()
    df.to_csv(INTERIM / "mentah.csv", index=False, encoding="utf-8")
    log = tulis_log(df, SUMBER, INTERIM / "log_akuisisi.json")

    print("=" * 64)
    print("01 · MENGUMPULKAN DATA")
    print("=" * 64)
    print(f"Berkas        : {log['berkas']} (sheet '{log['sheet']}')")
    print(f"SHA-256       : {log['sha256'][:32]}...")
    print(f"Dimensi       : {log['jumlah_baris']} baris x {log['jumlah_kolom']} kolom")
    print(f"Sel kosong    : {log['sel_kosong']}  {log['kolom_dengan_kosong'] or ''}")
    print(f"Tersimpan     : interim/mentah.csv, interim/log_akuisisi.json")


if __name__ == "__main__":
    main()
