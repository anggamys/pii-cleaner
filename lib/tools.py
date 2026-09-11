"""
tools.py — Utility bersama: konfigurasi, rename, process_file generic.
"""

import os
import re


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "source")
OUTPUT_DIR = os.path.join(BASE_DIR, "result")

FOLDERS = (
    [
        d
        for d in os.listdir(SOURCE_DIR)
        if os.path.isdir(os.path.join(SOURCE_DIR, d)) and not d.startswith(".")
    ]
    if os.path.isdir(SOURCE_DIR)
    else []
)

MODE = "replace"


def normalize_filename(name: str) -> str:
    name = name.lower()
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w\.\-]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name


def build_output_path(orig_path: str) -> str:
    rel = os.path.relpath(orig_path, SOURCE_DIR)
    parts = rel.split(os.sep)
    normalized = [normalize_filename(p) for p in parts]
    return os.path.join(OUTPUT_DIR, *normalized)


def process_file(src_path: str, dst_path: str, detectors: list, mode: str = "replace", dry_run: bool = True) -> dict:
    """
    Proses satu file dengan daftar detector.
    detectors: list of (detect_fn, replace_fn)
      - detect_fn(line) -> list[str] | None
      - replace_fn(line, items) -> str
    """
    if not os.path.isfile(src_path):
        return {"status": "error", "msg": "File tidak ditemukan"}

    with open(src_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total_found_lines = 0
    total_items = 0
    output_lines = []

    for line in lines:
        cleaned = line
        count = 0

        for detect_fn, replace_fn in detectors:
            items = detect_fn(cleaned)
            if items:
                count += len(items)
                cleaned = replace_fn(cleaned, items)

        if count:
            total_found_lines += 1
            total_items += count

        if mode == "removeline":
            output_lines.append("" if count else cleaned)
        else:
            output_lines.append(cleaned)

    if not dry_run:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with open(dst_path, "w", encoding="utf-8") as f:
            f.writelines(output_lines)

    return {
        "status": "ok",
        "src": src_path,
        "dst": dst_path if not dry_run else "(dry-run)",
        "total_baris": len(lines),
        "baris_bernomor": total_found_lines,
        "total_nomor": total_items,
    }
