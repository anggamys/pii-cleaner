"""
clean_pii.py — Bersihkan PII dan template WA dari file chat.

Yang dibersihkan:
  1. Template WA (via find_wa_template.py):
     - Timestamp di awal baris → di-strip, teks chat tetap
     - Baris <Media tidak disertakan> / <Media omitted> → dihapus
     - Baris pesan enkripsi WA (ID & EN) → dihapus
  2. PII (via find_phones / find_emails / find_rekening):
     - Nomor telepon → [PHONE]
     - Email         → [EMAIL]
     - Nomor rekening → [REKENING]

Cara pakai:
  python3 clean_pii.py                          # pakai folder source/ (default)
  python3 clean_pii.py source-babel             # pakai folder lain
  python3 clean_pii.py /path/absolut/ke/folder  # path absolut
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from find_emails import detect as detect_email, replace as replace_email
from find_phones import detect as detect_phone, replace as replace_phone
from find_rekening import detect as detect_rekening, replace as replace_rekening
from find_wa_template import detect as detect_wa, replace as replace_wa
from tools import BASE_DIR, normalize_filename
from tools import SOURCE_DIR as DEFAULT_SOURCE_DIR
from tools import OUTPUT_DIR as DEFAULT_OUTPUT_DIR

# ── Urutan pemrosesan ─────────────────────────────────────────────────────────
# WA template diproses duluan karena:
#   - detect() bisa return None → baris dihapus, skip PII
#   - timestamp di-strip dulu agar regex PII tidak terganggu prefix tanggal

PII_STEPS = [
    (detect_phone,    replace_phone),
    (detect_email,    replace_email),
    (detect_rekening, replace_rekening),
]


# ── Path resolution ───────────────────────────────────────────────────────────

def resolve_paths(arg_path: str | None):
    if not arg_path:
        return DEFAULT_SOURCE_DIR, DEFAULT_OUTPUT_DIR

    source = os.path.normpath(
        arg_path if os.path.isabs(arg_path) else os.path.join(BASE_DIR, arg_path)
    )

    if not os.path.isdir(source):
        print(f"[ERROR] Folder tidak ditemukan: {source}")
        sys.exit(1)

    folder_name = os.path.basename(source)
    output = os.path.join(BASE_DIR, f"result-{folder_name}")

    if os.path.normpath(output) == source:
        print("[ERROR] Output DIR sama dengan Source DIR — proses dibatalkan.")
        sys.exit(1)

    return source, output


def get_folders(source_dir: str) -> list[str]:
    return [
        d for d in os.listdir(source_dir)
        if os.path.isdir(os.path.join(source_dir, d)) and not d.startswith(".")
    ]


# ── Core processing ───────────────────────────────────────────────────────────

def process_file_wa(src: str, dst: str) -> dict:
    """Proses satu file: strip template WA lalu ganti PII."""
    with open(src, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    out_lines = []
    stat = {"media": 0, "enkripsi": 0, "system": 0, "timestamp": 0,
            "phone": 0, "email": 0, "rekening": 0}

    for line in lines:
        # Step 1: WA template
        wa_items = detect_wa(line)

        if wa_items is None:
            # Tidak ada template WA → lanjut proses PII seperti biasa
            pass
        elif wa_items[0] in ("MEDIA", "ENKRIPSI", "SYSTEM"):
            # Baris harus dihapus seluruhnya
            if wa_items[0] == "MEDIA":
                stat["media"] += 1
            elif wa_items[0] == "ENKRIPSI":
                stat["enkripsi"] += 1
            else:
                stat["system"] += 1
            continue
        else:
            # TIMESTAMP — strip prefix, lanjut ke PII
            line = replace_wa(line, wa_items)
            stat["timestamp"] += 1

        # Step 2: PII
        for detect_fn, replace_fn in PII_STEPS:
            items = detect_fn(line)
            if items:
                if detect_fn is detect_phone:
                    stat["phone"] += len(items)
                elif detect_fn is detect_email:
                    stat["email"] += len(items)
                elif detect_fn is detect_rekening:
                    stat["rekening"] += len(items)
                line = replace_fn(line, items)

        out_lines.append(line)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.writelines(out_lines)

    return stat


# ── Main runner ───────────────────────────────────────────────────────────────

def run_all(source_dir: str, output_dir: str):
    folders = get_folders(source_dir)

    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)

    print(f"Sumber  : {source_dir}")
    print(f"Output  : {output_dir}")
    print()

    folders_to_process = (
        [(".", source_dir)] if not folders
        else [(f, os.path.join(source_dir, f)) for f in sorted(folders)]
    )

    total = {"file": 0, "media": 0, "enkripsi": 0, "system": 0,
             "timestamp": 0, "phone": 0, "email": 0, "rekening": 0}

    for label, fpath in folders_to_process:
        if not os.path.isdir(fpath):
            continue

        sub = {"file": 0, "media": 0, "enkripsi": 0, "system": 0,
               "timestamp": 0, "phone": 0, "email": 0, "rekening": 0}

        for root, _, files in os.walk(fpath):
            for fname in files:
                if not fname.lower().endswith(".txt"):
                    continue
                src = os.path.join(root, fname)
                rel = os.path.relpath(src, source_dir)
                parts = rel.split(os.sep)
                normalized = [normalize_filename(p) for p in parts]
                dst = os.path.join(output_dir, *normalized)

                stat = process_file_wa(src, dst)
                sub["file"] += 1
                for k in stat:
                    sub[k] += stat[k]

        if label != ".":
            print(
                f"  {label:<35} {sub['file']:>4} file  "
                f"media={sub['media']}  enkripsi={sub['enkripsi']}  system={sub['system']}  "
                f"ts={sub['timestamp']}  "
                f"phone={sub['phone']}  email={sub['email']}  rekening={sub['rekening']}"
            )

        for k in total:
            total[k] += sub[k]

    total_pii = total["phone"] + total["email"] + total["rekening"]
    print()
    print("  Selesai!")
    print(f"  File diproses   : {total['file']}")
    print(f"  Baris dihapus   :")
    print(f"    Media         : {total['media']}")
    print(f"    Enkripsi      : {total['enkripsi']}")
    print(f"    System        : {total['system']}")
    print(f"  Timestamp strip : {total['timestamp']}")
    print(f"  PII diganti     :")
    print(f"    Phone         : {total['phone']}")
    print(f"    Email         : {total['email']}")
    print(f"    Rekening      : {total['rekening']}")
    print(f"    Total PII     : {total_pii}")
    print(f"  Output          : {output_dir}/")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    src, out = resolve_paths(arg)
    run_all(src, out)
