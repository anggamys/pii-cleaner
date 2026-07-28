#!/usr/bin/env python3
"""
Statistik Pseudo Label - Menghitung statistik dari folder data pseudo label CSV.
Cara pakai:  python statistik_pseudo_label.py [--dir path/to/folder]
             atau jalankan langsung, akan meminta input folder.
"""

import os
import sys
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def kategorikan_sekolah(filename):
    """Kategorikan file berdasarkan pola nama untuk menentukan asal sekolah."""
    name = filename.lower()
    if "data_atma_luhur" in name:
        return "Atma Luhur"
    elif "data_sman_1_pangkal_pinang" in name:
        return "SMAN 1 Pangkal Pinang"
    elif "sman_1_manggar" in name:
        return "SMAN 1 Manggar"
    elif "data_sman_" in name:
        # tangkap nama sekolah dari pola data_sman_{N}_{KOTA}
        parts = name.replace(".csv", "").split("_")
        if len(parts) >= 5:
            return f"SMAN {' '.join(parts[2:5]).title()}"
        return "SMAN Lainnya"
    elif "data_" in name:
        return "Institusi Lainnya"
    return "Tidak Diketahui"


def hitung_statistik(folder_path):
    """Hitung statistik dari semua file CSV dalam folder."""
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ Error: Folder '{folder_path}' tidak ditemukan.")
        sys.exit(1)

    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        print(f"❌ Error: Tidak ada file CSV di folder '{folder_path}'.")
        sys.exit(1)

    print(f"📂 Memproses {len(csv_files)} file CSV dari: {folder_path}")
    print("⏳ Mohon tunggu, sedang menghitung...\n")

    # Statistik global
    total_baris = 0
    total_file = len(csv_files)
    total_koreksi = 0
    total_pred = 0

    # Per-sekolah
    sekolah_files = defaultdict(int)
    sekolah_rows = defaultdict(int)
    sekolah_sentences = defaultdict(set)
    sekolah_koreksi = defaultdict(int)

    # Distribusi POS tag
    pos_pred_counter = Counter()
    pos_koreksi_counter = Counter()

    # Tracking unik file_id dan sentence_id global
    unik_file_id = set()

    for i, csv_path in enumerate(csv_files, 1):
        filename = csv_path.name
        sekolah = kategorikan_sekolah(filename)
        sekolah_files[sekolah] += 1

        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                header = next(f)
                col_map = {h.strip().lower(): idx for idx, h in enumerate(header.strip().split(","))}

                file_id_idx = col_map.get("file_id", -1)
                sent_id_idx = col_map.get("sentence_id", -1)
                pos_pred_idx = col_map.get("pos_tag_pred", -1)
                pos_koreksi_idx = col_map.get("pos_tag_koreksi", -1)

                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    cols = line.split(",")
                    total_baris += 1
                    sekolah_rows[sekolah] += 1

                    # file_id
                    if file_id_idx >= 0 and file_id_idx < len(cols):
                        fid = cols[file_id_idx].strip()
                        if fid:
                            unik_file_id.add(fid)

                    # sentence_id
                    if sent_id_idx >= 0 and sent_id_idx < len(cols):
                        sid = cols[sent_id_idx].strip()
                        if sid and file_id_idx >= 0 and file_id_idx < len(cols):
                            sekolah_sentences[sekolah].add(f"{cols[file_id_idx].strip()}_{sid}")

                    # pos_tag_pred
                    if pos_pred_idx >= 0 and pos_pred_idx < len(cols):
                        tag_pred = cols[pos_pred_idx].strip()
                        if tag_pred:
                            pos_pred_counter[tag_pred] += 1
                            total_pred += 1

                    # pos_tag_koreksi
                    if pos_koreksi_idx >= 0 and pos_koreksi_idx < len(cols):
                        tag_koreksi = cols[pos_koreksi_idx].strip()
                        if tag_koreksi:
                            pos_koreksi_counter[tag_koreksi] += 1
                            sekolah_koreksi[sekolah] += 1
                            total_koreksi += 1

        except Exception as e:
            print(f"⚠️  Gagal membaca {filename}: {e}")

    return {
        "folder": str(folder),
        "total_file": total_file,
        "total_baris": total_baris,
        "total_unik_file_id": len(unik_file_id),
        "total_koreksi": total_koreksi,
        "total_pred": total_pred,
        "sekolah_files": dict(sekolah_files),
        "sekolah_rows": dict(sekolah_rows),
        "sekolah_sentences": {k: len(v) for k, v in sekolah_sentences.items()},
        "sekolah_koreksi": dict(sekolah_koreksi),
        "pos_pred": pos_pred_counter,
        "pos_koreksi": pos_koreksi_counter,
    }


def format_angka(n):
    """Format angka dengan separator ribuan."""
    return f"{n:,}".replace(",", ".")


def tampilkan_statistik(stats):
    """Tampilkan statistik dalam format tabel yang rapi."""
    total = stats["total_baris"]
    total_koreksi = stats["total_koreksi"]
    pct_koreksi = (total_koreksi / total * 100) if total > 0 else 0

    # ── HEADER ──
    print("=" * 65)
    print("   📊  STATISTIK DATA PSEUDO LABEL")
    print("=" * 65)

    # ── RINGKASAN UMUM ──
    print("\n📋  RINGKASAN UMUM")
    print("-" * 65)
    print(f"  {'Folder':32s}: {stats['folder']}")
    print(f"  {'Total file CSV':32s}: {format_angka(stats['total_file'])} file")
    print(f"  {'Total baris data (token)':32s}: {format_angka(total)} baris")
    print(f"  {'Total unik file_id (chat)':32s}: {format_angka(stats['total_unik_file_id'])} chat")
    print(f"  {'Total ukuran folder':32s}: ", end="")
    # hitung ukuran folder
    folder_path = stats["folder"]
    total_size = 0
    for f in Path(folder_path).glob("*.csv"):
        total_size += f.stat().st_size
    if total_size > 1e9:
        print(f"{total_size / 1e9:.2f} GB")
    elif total_size > 1e6:
        print(f"{total_size / 1e6:.2f} MB")
    else:
        print(f"{total_size / 1e3:.2f} KB")

    # ── STATUS KOREKSI ──
    print("\n✅  STATUS KOREKSI POS TAG")
    print("-" * 65)
    print(f"  {'Memiliki pos_tag_koreksi':32s}: {format_angka(total_koreksi):>12} token  ({pct_koreksi:.2f}%)")
    print(f"  {'Belum dikoreksi (kosong)':32s}: {format_angka(total - total_koreksi):>12} token  ({100 - pct_koreksi:.2f}%)")
    print(f"  {'Memiliki pos_tag_pred':32s}: {format_angka(stats['total_pred']):>12} token")

    # ── DISTRIBUSI PER SEKOLAH ──
    print("\n🏫  DISTRIBUSI PER SEKOLAH / INSTITUSI")
    print("-" * 65)
    print(f"  {'Sekolah':30s} {'File':>6s} {'Token':>14s} {'%':>7s} {'Kalimat':>10s}")
    print(f"  {'─' * 29} {'─' * 5} {'─' * 13} {'─' * 6} {'─' * 9}")

    sekolah_list = sorted(stats["sekolah_rows"].items(), key=lambda x: -x[1])
    for nama, rows in sekolah_list:
        fcount = stats["sekolah_files"].get(nama, 0)
        sents = stats["sekolah_sentences"].get(nama, 0)
        pct = (rows / total * 100) if total > 0 else 0
        print(f"  {nama:30s} {fcount:>5d} {format_angka(rows):>13s} {pct:>6.1f}% {format_angka(sents):>9s}")

    print(f"  {'─' * 29} {'─' * 5} {'─' * 13} {'─' * 6} {'─' * 9}")
    print(f"  {'TOTAL':30s} {stats['total_file']:>5d} {format_angka(total):>13s} {'100.0%':>6s} {'':>9s}")

    # Koreksi per sekolah
    print(f"\n  ✏️  Koreksi per sekolah:")
    for nama in sorted(stats["sekolah_koreksi"].keys()):
        k = stats["sekolah_koreksi"].get(nama, 0)
        r = stats["sekolah_rows"].get(nama, 0)
        p = (k / r * 100) if r > 0 else 0
        print(f"     {nama:30s}: {format_angka(k):>10s} token dikoreksi ({p:.1f}%)")

    # ── TOP POS TAG PREDIKSI ──
    print(f"\n🔮  TOP 20 POS TAG PREDIKSI (pos_tag_pred)")
    print("-" * 65)
    print(f"  {'POS Tag':25s} {'Jumlah':>14s} {'%':>8s}")
    print(f"  {'─' * 24} {'─' * 13} {'─' * 7}")
    for tag, count in stats["pos_pred"].most_common(20):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {tag:25s} {format_angka(count):>13s} {pct:>6.2f}%")

    # ── TOP POS TAG KOREKSI ──
    print(f"\n✅  TOP 20 POS TAG KOREKSI (pos_tag_koreksi)")
    print("-" * 65)
    if stats["pos_koreksi"]:
        print(f"  {'POS Tag':25s} {'Jumlah':>14s} {'%':>8s}")
        print(f"  {'─' * 24} {'─' * 13} {'─' * 7}")
        for tag, count in stats["pos_koreksi"].most_common(20):
            pct = (count / total_koreksi * 100) if total_koreksi > 0 else 0
            print(f"  {tag:25s} {format_angka(count):>13s} {pct:>6.2f}%")
    else:
        print("  (Belum ada data koreksi)")

    # ── INSIGHT ──
    print("\n💡  INSIGHT CEPAT")
    print("-" * 65)
    chat_terbanyak = max(sekolah_list, key=lambda x: x[1])[0] if sekolah_list else "-"
    print(f"  • Dataset: {format_angka(total)} token dari {stats['total_file']} file chat")
    print(f"  • Rata-rata token per chat: ~{total // max(stats['total_unik_file_id'], 1):,}".replace(",", "."))
    print(f"  • Koreksi masih minim: hanya {pct_koreksi:.1f}% token sudah dikoreksi")
    print(f"  • Kontributor terbesar: {chat_terbanyak}")
    print(f"  • {format_angka(total - total_koreksi)} token ({100-pct_koreksi:.1f}%) menunggu koreksi")

    print("\n" + "=" * 65)
    print("   Selesai ✅")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(
        description="Hitung statistik dari folder data pseudo label CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python statistik_pseudo_label.py
  python statistik_pseudo_label.py --dir archive/data_pseudo_label
  python statistik_pseudo_label.py --dir /path/ke/folder --output laporan.txt
        """,
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=None,
        help="Path ke folder yang berisi file CSV pseudo label (default: prompt input)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Simpan output ke file teks (opsional)",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=20,
        help="Jumlah top POS tag yang ditampilkan (default: 20)",
    )

    args = parser.parse_args()

    # Jika --dir tidak diberikan, minta input
    if args.dir is None:
        folder_input = input("Masukkan path folder data pseudo label: ").strip()
        if not folder_input:
            print("❌ Folder tidak boleh kosong.")
            sys.exit(1)
        args.dir = folder_input

    # Hitung statistik
    stats = hitung_statistik(args.dir)

    # Tampilkan
    if args.output:
        # Redirect stdout ke file
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        tampilkan_statistik(stats)
        output_text = sys.stdout.getvalue()
        sys.stdout = old_stdout
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"✅ Laporan disimpan ke: {args.output}")
    else:
        tampilkan_statistik(stats)


if __name__ == "__main__":
    main()