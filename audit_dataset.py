"""Audit dataset data_pseudo_label — menghasilkan laporan 35 item.

Cara pakai:
    python3 audit_dataset.py                        # folder data_pseudo_label (default)
    python3 audit_dataset.py /path/ke/folder        # folder lain
    python3 audit_dataset.py --out docs/laporan.md   # ubah path output

Hanya memakai standard library (csv, os, collections).
"""

import csv
import hashlib
import io
import os
import sys
import time
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "data_pseudo_label")
DEFAULT_OUT = os.path.join(BASE_DIR, "docs", "laporan_audit_dataset.md")

EXPECTED_HEADER = [
    "file_id",
    "sentence_id",
    "token_index",
    "token",
    "pos_tag_pred",
    "pos_tag_koreksi",
]
ENCODINGS = ("utf-8-sig", "utf-8", "latin-1")
MAX_EXAMPLES = 5
MAX_UNIQ_TRACK = 5000


def fmt_size(n):
    if n >= 1e9:
        return f"{n / 1e9:.2f} GB ({n:,} byte)"
    if n >= 1e6:
        return f"{n / 1e6:.2f} MB ({n:,} byte)"
    if n >= 1e3:
        return f"{n / 1e3:.2f} KB ({n:,} byte)"
    return f"{n} byte"


def fmt_num(n):
    return f"{n:,}".replace(",", ".")


def is_int(s):
    s = s.strip()
    if not s:
        return False
    if s[0] in ("+", "-"):
        return s[1:].isdigit()
    return s.isdigit()


def sniff_delimiter(sample_text):
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_arg = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--out=")]
    data_dir = args[0] if args else DEFAULT_DATA_DIR
    out_path = out_arg[0] if out_arg else DEFAULT_OUT

    if not os.path.isdir(data_dir):
        print(f"[ERROR] Folder tidak ditemukan: {data_dir}")
        sys.exit(1)

    files = sorted(f for f in os.listdir(data_dir) if f.lower().endswith(".csv"))
    if not files:
        print(f"[ERROR] Tidak ada file CSV di: {data_dir}")
        sys.exit(1)

    print(f"Memproses {len(files)} file CSV ...")

    # Akumulator global
    file_sizes = []
    header_map = defaultdict(list)  # tuple(header) -> [filenames]
    encoding_counter = Counter()
    encoding_failures = []
    delimiter_counter = Counter()
    delimiter_odd = []

    total_rows = 0
    skipped_empty_lines = 0
    sentence_hashes = set()  # digest 8-byte dari "fid\0sid"
    token_values = set()  # tanpa batas — token pendek, distinct terbatas
    file_id_values = set()
    pos_pred = Counter()
    pos_kor = Counter()
    missing = Counter()
    empty_token = 0
    seen_row_hash = set()  # digest 8-byte baris kanonis (identik penuh)
    dup_count = 0
    dup_examples = []

    def digest(s):
        return hashlib.blake2b(s.encode("utf-8", "replace"), digest_size=8).digest()

    bad_sid = 0
    bad_sid_ex = []
    bad_tidx = 0
    bad_tidx_ex = []
    dup_tidx_sentences = 0
    dup_tidx_ex = []
    gap_tidx_sentences = 0
    gap_tidx_ex = []
    not_start_1_sentences = 0
    not_start_1_ex = []

    col_examples = defaultdict(list)  # col -> contoh unik (max 3)
    col_seen_ex = defaultdict(set)
    col_all_int = {c: True for c in EXPECTED_HEADER}
    col_nonempty = Counter()
    col_uniq = defaultdict(set)
    col_uniq_capped = defaultdict(bool)

    t0 = time.time()
    for fi, fname in enumerate(files, 1):
        fpath = os.path.join(data_dir, fname)
        file_sizes.append((fname, os.path.getsize(fpath)))

        # Baca dengan encoding fallback
        text = None
        used_enc = None
        for enc in ENCODINGS:
            try:
                with open(fpath, "r", encoding=enc) as fh:
                    text = fh.read()
                used_enc = enc
                break
            except (UnicodeError, UnicodeDecodeError):
                continue
        if text is None:
            encoding_failures.append(fname)
            continue
        encoding_counter[used_enc] += 1

        delim = sniff_delimiter(text[:8192])
        delimiter_counter[delim] += 1
        if delim != ",":
            delimiter_odd.append((fname, repr(delim)))

        try:
            reader = csv.reader(io.StringIO(text), delimiter=delim)
            header = None
            for raw in reader:
                if any(c.strip() for c in raw):
                    header = [h.strip() for h in raw]
                    break
                skipped_empty_lines += 1
            if header is None:
                continue
        except csv.Error:
            encoding_failures.append(fname + " (parse)")
            continue
        header_map[tuple(header)] += [fname]
        idx = {name.lower(): pos for pos, name in enumerate(header)}
        ncols = len(header)

        # Struktur kalimat dalam file ini saja (hemat memori)
        sent_idx = defaultdict(set)  # (fid, sid) -> set token_index

        for raw in reader:
            if not any(c.strip() for c in raw):
                skipped_empty_lines += 1
                continue
            if len(raw) < ncols:
                raw = raw + [""] * (ncols - len(raw))
            row = [c.strip() for c in raw[:ncols]]
            total_rows += 1

            # Duplikat baris penuh (digest baris kanonis)
            dkey = digest("\x1f".join(row))
            if dkey in seen_row_hash:
                dup_count += 1
                if len(dup_examples) < MAX_EXAMPLES:
                    dup_examples.append((fname, list(row)))
            else:
                seen_row_hash.add(dkey)

            get = lambda col, row=row, idx=idx: row[idx[col]] if col in idx else ""

            fid = get("file_id")
            sid = get("sentence_id")
            tidx = get("token_index")
            tok = get("token")
            pred = get("pos_tag_pred")
            kor = get("pos_tag_koreksi")

            # Missing per kolom
            for col in EXPECTED_HEADER:
                v = get(col)
                if not v:
                    missing[col] += 1

            if not tok:
                empty_token += 1

            if fid:
                file_id_values.add(fid)
            if tok:
                token_values.add(tok)
            if fid and sid:
                sentence_hashes.add(digest(fid + "\x00" + sid))

            if pred:
                pos_pred[pred] += 1
            if kor:
                pos_kor[kor] += 1

            # Profil kolom: contoh + format
            for col in EXPECTED_HEADER:
                v = get(col)
                if v:
                    col_nonempty[col] += 1
                if v and v not in col_seen_ex[col] and len(col_examples[col]) < 3:
                    col_seen_ex[col].add(v)
                    col_examples[col].append(v)
                if v and col_all_int[col] and not is_int(v):
                    col_all_int[col] = False
                if not col_uniq_capped[col]:
                    col_uniq[col].add(v)
                    if len(col_uniq[col]) > MAX_UNIQ_TRACK:
                        col_uniq_capped[col] = True
                        col_uniq[col] = set()

            # Anomali sentence_id / token_index
            if sid and not is_int(sid):
                bad_sid += 1
                if len(bad_sid_ex) < MAX_EXAMPLES:
                    bad_sid_ex.append((fname, fid, sid))
            tidx_ok = bool(tidx) and is_int(tidx)
            if not tidx_ok:
                bad_tidx += 1
                if len(bad_tidx_ex) < MAX_EXAMPLES:
                    bad_tidx_ex.append((fname, fid, sid, tidx))
            if fid and sid and tidx_ok:
                skey = (fid, sid)
                t = int(tidx)
                if t in sent_idx[skey]:
                    dup_tidx_sentences += 1
                    if len(dup_tidx_ex) < MAX_EXAMPLES:
                        dup_tidx_ex.append((fname, fid, sid, t))
                else:
                    sent_idx[skey].add(t)

        # Evaluasi gap & start per kalimat dalam file ini
        for (fid, sid), idxs in sent_idx.items():
            if not idxs:
                continue
            if min(idxs) != 1:
                not_start_1_sentences += 1
                if len(not_start_1_ex) < MAX_EXAMPLES:
                    not_start_1_ex.append((fname, fid, sid, sorted(idxs)[:8]))
            if set(idxs) != set(range(1, max(idxs) + 1)):
                gap_tidx_sentences += 1
                if len(gap_tidx_ex) < MAX_EXAMPLES:
                    missing_idx = sorted(set(range(1, max(idxs) + 1)) - idxs)[:8]
                    gap_tidx_ex.append((fname, fid, sid, missing_idx))

        if fi % 100 == 0 or fi == len(files):
            el = time.time() - t0
            print(
                f"  ... {fi}/{len(files)} file ({el:.0f}s, {fmt_num(total_rows)} baris)",
                flush=True,
            )

    # Ringkasan turunan
    total_size = sum(s for _, s in file_sizes)
    header_variants = len(header_map)
    main_header, main_files = max(header_map.items(), key=lambda kv: len(kv[1]))
    header_consistent = header_variants == 1
    odd_header_files = [
        (list(h), fs[:MAX_EXAMPLES])
        for h, fs in header_map.items()
        if list(h) != list(main_header)
    ]
    top_sizes = sorted(file_sizes, key=lambda x: -x[1])[:10]

    all_pos = sorted(set(pos_pred) | set(pos_kor))
    tot_pred = sum(pos_pred.values())
    tot_kor = sum(pos_kor.values())

    def top_bottom(counter):
        if not counter:
            return ("-", 0), ("-", 0)
        most = counter.most_common(1)[0]
        least = min(counter.items(), key=lambda kv: kv[1])
        return most, least

    pred_most, pred_least = top_bottom(pos_pred)
    kor_most, kor_least = top_bottom(pos_kor)

    def col_format(col):
        if col_nonempty[col] == 0:
            return "kosong — tidak ada nilai terisi"
        if col_all_int[col]:
            return "integer"
        if not col_uniq_capped[col] and len(col_uniq[col]) <= 50:
            return f"categorical ({len(col_uniq[col])} nilai unik terpantau)"
        if col_uniq_capped[col]:
            return "string (unik > 5000)"
        return "string"

    # ── Tulis laporan Markdown ──
    L = []
    A = L.append
    A("# Laporan Audit Dataset `data_pseudo_label`")
    A("")
    A(
        "> Item 1–8 bersifat manual (ditandai ☐ / [PERLU KONFIRMASI]). "
        "Item 9–35 dihitung otomatis oleh `audit_dataset.py` dari seluruh file CSV."
    )
    A("")
    A("## Tabel 35 Item")
    A("")
    A("| No. | Informasi yang Dicek | Status | Hasil yang Perlu Dicatat |")
    A("|---|---|---|---|")
    A("| 1 | Nama dataset | ☐ | `data_pseudo_label` [PERLU KONFIRMASI: nama resmi] |")
    A("| 2 | Judul dataset | ☐ | [BELUM DIISI: judul untuk PDF] |")
    A("| 3 | Tujuan dataset | ☐ | [BELUM DIISI: tujuan penggunaan/pembuatan] |")
    A(
        "| 4 | Jenis dataset | ☐ | Annotated corpus (token-level POS, pseudo label + koreksi manual) [PERLU KONFIRMASI] |"
    )
    A("| 5 | Bahasa | ☐ | Indonesia (percakapan informal) [PERLU KONFIRMASI] |")
    A("| 6 | Domain data | ☐ | Percakapan WhatsApp [PERLU KONFIRMASI] |")
    A(
        "| 7 | Karakteristik data | ☐ | Informal, noisy, slang, typo, emoji/sticker text, singkatan [PERLU KONFIRMASI] |"
    )
    A(
        "| 8 | Pengembangan dari dataset lain | ☐ | [BELUM DIISI: nama dataset/sumber sebelumnya, jika ada] |"
    )
    A(f"| 9 | Jumlah file CSV | ✅ | {fmt_num(len(files))} file |")
    A(
        f"| 10 | Nama seluruh file CSV | ✅ | Terlampir di lampiran (total {fmt_num(len(files))} nama) |"
    )
    A(
        "| 11 | Ukuran setiap file | ✅ | Terlampir di lampiran; 10 terbesar dirinci di bawah |"
    )
    A(f"| 12 | Total ukuran dataset | ✅ | {fmt_size(total_size)} |")
    A(
        f"| 13 | Struktur kolom | ✅ | {', '.join(main_header)} ({len(main_header)} kolom, dipakai {fmt_num(len(main_files))} file) |"
    )
    A(
        f"| 14 | Konsistensi kolom antarfile | ✅ | {'SAMA di semua file' if header_consistent else f'TIDAK SAMA: {header_variants} varian header'} |"
    )
    A(
        f"| 15 | Jumlah total baris | ✅ | {fmt_num(total_rows)} record data (baris kosong dilewati: {fmt_num(skipped_empty_lines)}) |"
    )
    A(
        f"| 16 | Jumlah total kalimat | ✅ | {fmt_num(len(sentence_hashes))} pasangan unik (file_id, sentence_id) |"
    )
    A(
        f"| 17 | Jumlah total token | ✅ | {fmt_num(total_rows)} token (1 baris = 1 token) |"
    )
    A(
        f"| 18 | Jumlah token unik | ✅ | {fmt_num(len(token_values))} nilai unik (eksak, case-sensitive, setelah strip) |"
    )
    A(
        f"| 19 | Jumlah file_id unik | ✅ | {fmt_num(len(file_id_values))} dokumen/sumber |"
    )
    A(
        f"| 20 | Jumlah label POS unik | ✅ | pred: {len(pos_pred)} label; koreksi: {len(pos_kor)} label; gabungan: {len(all_pos)} label |"
    )
    A(
        f"| 21 | Daftar seluruh label POS | ✅ | pred: {', '.join(sorted(pos_pred))}; koreksi: {', '.join(sorted(pos_kor))} |"
    )
    dist_pred = "; ".join(
        f"{t}={fmt_num(c)} ({c / tot_pred * 100:.2f}%)"
        for t, c in pos_pred.most_common()
    )
    dist_kor = "; ".join(
        f"{t}={fmt_num(c)} ({c / tot_kor * 100:.2f}%)" for t, c in pos_kor.most_common()
    )
    A(
        f"| 22 | Distribusi setiap label POS | ✅ | pred ({fmt_num(tot_pred)}): {dist_pred} ‖ koreksi ({fmt_num(tot_kor)}): {dist_kor} |"
    )
    A(
        f"| 23 | Label POS paling banyak | ✅ | pred: {pred_most[0]} ({fmt_num(pred_most[1])}); koreksi: {kor_most[0]} ({fmt_num(kor_most[1])}) |"
    )
    A(
        f"| 24 | Label POS paling sedikit | ✅ | pred: {pred_least[0]} ({fmt_num(pred_least[1])}); koreksi: {kor_least[0]} ({fmt_num(kor_least[1])}) |"
    )
    miss_str = "; ".join(f"{c}: {fmt_num(missing[c])}" for c in EXPECTED_HEADER)
    A(f"| 25 | Missing value | ✅ | {miss_str} (string kosong setelah strip) |")
    A(
        f"| 26 | Duplikasi data | ✅ | {fmt_num(dup_count)} baris identik penuh (contoh terlampir) |"
    )
    A(f"| 27 | Token kosong | ✅ | {fmt_num(empty_token)} baris |")
    A(
        f"| 28 | sentence_id bermasalah | ✅ | non-integer: {fmt_num(bad_sid)} (contoh terlampir) |"
    )
    A(
        f"| 29 | token_index bermasalah | ✅ | non-integer/kosong: {fmt_num(bad_tidx)}; duplikat index dalam kalimat: {fmt_num(dup_tidx_sentences)} kalimat; gap urutan: {fmt_num(gap_tidx_sentences)} kalimat; tidak mulai dari 1: {fmt_num(not_start_1_sentences)} kalimat |"
    )
    enc_str = "; ".join(
        f"{e}: {fmt_num(c)} file" for e, c in encoding_counter.most_common()
    )
    A(
        f"| 30 | Encoding file | ✅ | {enc_str}"
        + (
            f"; gagal semua encoding: {len(encoding_failures)} file"
            if encoding_failures
            else " |"
        )
    )
    del_str = "; ".join(
        f"{d!r}: {fmt_num(c)} file" for d, c in delimiter_counter.most_common()
    )
    A(f"| 31 | Delimiter CSV | ✅ | {del_str} |")
    A(
        f"| 32 | Header CSV | ✅ | Ada di semua file yang terbaca ({fmt_num(sum(len(v) for v in header_map.values()))} file); {header_variants} varian header |"
    )
    fmt_str = "; ".join(f"{c}: {col_format(c)}" for c in EXPECTED_HEADER)
    A(f"| 33 | Format nilai setiap kolom | ✅ | {fmt_str} |")
    ex_str = "; ".join(f"{c}: {col_examples[c]}" for c in EXPECTED_HEADER)
    A(f"| 34 | Contoh nilai setiap kolom | ✅ | {ex_str} |")
    A(
        "| 35 | Definisi setiap kolom | ✅ | file_id: ID dokumen/sumber chat; sentence_id: ID kalimat dalam file_id; token_index: urutan token dalam kalimat (mulai 1); token: satuan kata/tanda baca; pos_tag_pred: label POS prediksi model; pos_tag_koreksi: label POS koreksi manual (kosong = belum dikoreksi) |"
    )
    A("")
    A("## Lampiran")
    A("")
    A("### A. 10 file terbesar")
    A("")
    for fname, sz in top_sizes:
        A(f"- `{fname}` — {fmt_size(sz)}")
    A("")
    A("### B. File dengan header menyimpang")
    A("")
    if odd_header_files:
        for h, fs in odd_header_files:
            A(
                f"- Header `{','.join(h)}` — {len(fs)} contoh: "
                + ", ".join(f"`{f}`" for f in fs)
            )
    else:
        A("- Tidak ada. Semua file memakai header yang sama.")
    A("")
    A("### C. File dengan delimiter non-koma")
    A("")
    if delimiter_odd:
        for fname, d in delimiter_odd[:20]:
            A(f"- `{fname}` — delimiter {d}")
    else:
        A("- Tidak ada. Semua file memakai koma.")
    A("")
    A("### D. Contoh baris duplikat (max 5)")
    A("")
    if dup_examples:
        for fname, row in dup_examples:
            A(f"- `{fname}`: `{','.join(row)}`")
    else:
        A("- Tidak ada duplikat.")
    A("")
    A("### E. Contoh sentence_id bermasalah (max 5)")
    A("")
    if bad_sid_ex:
        for fname, fid, sid in bad_sid_ex:
            A(f"- `{fname}` — file_id=`{fid}`, sentence_id=`{sid}`")
    else:
        A("- Tidak ada.")
    A("")
    A("### F. Contoh token_index bermasalah (max 5 per jenis)")
    A("")
    A(f"- Non-integer/kosong: {bad_tidx_ex if bad_tidx_ex else 'tidak ada'}")
    A(f"- Duplikat index: {dup_tidx_ex if dup_tidx_ex else 'tidak ada'}")
    A(f"- Gap urutan (index hilang): {gap_tidx_ex if gap_tidx_ex else 'tidak ada'}")
    A(f"- Tidak mulai dari 1: {not_start_1_ex if not_start_1_ex else 'tidak ada'}")
    A("")
    A("### G. Daftar seluruh nama file CSV")
    A("")
    for fname in files:
        A(f"- `{fname}`")
    A("")
    A("### H. Ukuran setiap file CSV")
    A("")
    for fname, sz in sorted(file_sizes):
        A(f"- `{fname}` — {fmt_size(sz)}")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print()
    print("Selesai!")
    print(f"  File CSV        : {len(files)}")
    print(f"  Total baris     : {total_rows}")
    print(f"  Total kalimat   : {len(sentence_hashes)}")
    print(f"  Token unik      : {len(token_values)}")
    print(f"  Duplikat        : {dup_count}")
    print(f"  Laporan         : {out_path}")


if __name__ == "__main__":
    main()
