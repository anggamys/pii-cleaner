"""
clean_pii.py — Bersihkan PII (phone, email, rekening) dari file chat.
Hasil output ke folder result/ dengan struktur folder yg sama.

Cara pakai:
  python3 clean_pii.py
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from find_emails import detect as detect_email, replace as replace_email
from find_phones import detect as detect_phone, replace as replace_phone
from find_rekening import detect as detect_rekening, replace as replace_rekening
from tools import FOLDERS, MODE, OUTPUT_DIR, SOURCE_DIR, build_output_path, process_file

DETECTORS = [
    (detect_phone, replace_phone),
    (detect_email, replace_email),
    (detect_rekening, replace_rekening),
]


def run_all():
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    total_f = total_p = total_e = total_r = 0

    print("Proses semua file ke folder result/ ...\n")

    for folder in FOLDERS:
        fpath = os.path.join(SOURCE_DIR, folder)
        if not os.path.isdir(fpath):
            continue

        fc = pc = ec = rc = 0
        for root, _, files in os.walk(fpath):
            for fname in files:
                if not fname.lower().endswith(".txt"):
                    continue
                fc += 1
                src = os.path.join(root, fname)
                dst = build_output_path(src)
                process_file(src, dst, DETECTORS, mode=MODE, dry_run=False)

                with open(src, "r", encoding="utf-8") as fh:
                    for line in fh:
                        p = detect_phone(line)
                        e = detect_email(line)
                        r = detect_rekening(line)
                        if p:
                            pc += len(p)
                        if e:
                            ec += len(e)
                        if r:
                            rc += len(r)

        print(f"  {folder:<35} {fc:>4} file  phone={pc}  email={ec}  rekening={rc}")
        total_f += fc
        total_p += pc
        total_e += ec
        total_r += rc

    total_all = total_p + total_e + total_r
    print()
    print("  Selesai!")
    print(f"  File diproses : {total_f}")
    print(f"  Phone     : {total_p}")
    print(f"  Email     : {total_e}")
    print(f"  Rekening  : {total_r}")
    print(f"  Total     : {total_all}")
    print(f"  Output    : {OUTPUT_DIR}/")


if __name__ == "__main__":
    run_all()
