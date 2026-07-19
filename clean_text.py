"""
clean_text.py — Menghapus baris yang mengandung kalimat/pola spesifik
dari seluruh file txt di folder source/. Hasil disimpan ke result/.
"""

import os
import re

# Pola kalimat exact match atau awalan
TEXT_TO_REMOVE = [
    "SCROLL TO CONTINUE WITH CONTENT",
    "Tonton juga video",
    "[Gambas:Video 20detik]",
    "Lihat juga Video",
    "Simak juga Video",
]

# Pola regex (misal: tanggal format (DD/MM/YYYY))
# Akan menangkap (21/11/2025), (01/01/2014), dll.
DATE_PATTERN = re.compile(r"\(\d{1,2}/\d{1,2}/\d{4}\)")

def should_remove_line(line: str) -> bool:
    """Cek apakah baris ini harus dihapus."""
    line_clean = line.strip()
    if not line_clean:
        return False  # Jangan hapus baris kosong sembarangan, biarkan sesuai aslinya

    # 1. Cek exact phrase atau prefix (case insensitive lebih aman, tapi kita buat exact match dulu)
    for text in TEXT_TO_REMOVE:
        if text in line_clean:
            return True

    # 2. Cek pattern tanggal (DD/MM/YYYY)
    if DATE_PATTERN.search(line_clean):
        return True

    return False

def process_file(src_path: str, dst_path: str):
    """Proses 1 file: hapus baris yang tidak diinginkan."""
    with open(src_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    removed_count = 0

    for line in lines:
        if should_remove_line(line):
            removed_count += 1
            # Jangan append ke output_lines (baris dihapus)
        else:
            output_lines.append(line)

    # Simpan jika ada file (walaupun tidak ada yang dihapus, copy saja agar konsisten)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    return removed_count

def run_all():
    source_dir = "source"
    output_dir = "result"

    if not os.path.exists(source_dir):
        print(f"Folder '{source_dir}' tidak ditemukan!")
        return

    print("Memproses penghapusan teks...")
    total_files = 0
    total_removed = 0

    # Looping rekursif ke seluruh file txt
    for root, _, files in os.walk(source_dir):
        for file in files:
            if not file.lower().endswith(".txt"):
                continue

            src = os.path.join(root, file)
            # Buat path tujuan (pertahankan struktur sub-folder jika ada)
            rel_path = os.path.relpath(src, source_dir)
            dst = os.path.join(output_dir, rel_path)

            removed = process_file(src, dst)

            total_removed += removed
            total_files += 1

    print("Selesai")
    print(f"Total file diproses : {total_files}")
    print(f"Total baris dihapus : {total_removed}")
    print(f"Output tersimpan di : {output_dir}/")

if __name__ == "__main__":
    run_all()
