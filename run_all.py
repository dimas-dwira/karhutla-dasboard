"""
run_all.py — menjalankan seluruh pipeline secara berurutan.

    python run_all.py

Script 03 (validasi) akan menghentikan pipeline bila ada aturan blocker yang
gagal. Pada dataset ini V-07 memang gagal, dan temuan itu diterima secara
eksplisit dengan alasan yang ikut tercatat di output/log_validasi.csv.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parent
SRC = AKAR / "src"

ALASAN_V07 = (
    "Selisih 2023 dilaporkan ke walidata sebagai permintaan klarifikasi tertulis. "
    "Sampai klarifikasi diterima, analisis memakai penjumlahan baris kabupaten "
    "dan tahun 2023 diberi penanda kualitas data di dim_tahun."
)

LANGKAH = [
    (["01_kumpulkan.py"], "Mengumpulkan data"),
    (["02_telaah.py"], "Menelaah data"),
    (["03_validasi.py", "--terima-temuan", "V-07", "--alasan", ALASAN_V07], "Memvalidasi data"),
    (["04_bersihkan.py"], "Membersihkan data"),
    (["05_ekspor_bi.py"], "Mengekspor untuk BI"),
]


def main() -> None:
    for i, (perintah, judul) in enumerate(LANGKAH, 1):
        print(f"\n{'#' * 72}\n# LANGKAH {i}/{len(LANGKAH)} — {judul}\n{'#' * 72}")
        hasil = subprocess.run([sys.executable, str(SRC / perintah[0]), *perintah[1:]])
        if hasil.returncode != 0:
            print(f"\nPipeline berhenti di langkah {i} ({judul}). "
                  f"Periksa output/log_validasi.csv.")
            sys.exit(hasil.returncode)
    print(f"\n{'#' * 72}\n# PIPELINE SELESAI\n{'#' * 72}")
    print("Keluaran model bintang : output/")
    print("Keluaran untuk Power BI: bi/")


if __name__ == "__main__":
    main()
