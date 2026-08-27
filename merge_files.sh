#!/usr/bin/env bash
# =============================================================================
# merge_files.sh — Merge semua file .txt dari sub-folder ke satu folder datar
#
# Cara pakai:
#   bash merge_files.sh                              # default: result-source-babel → merged/
#   bash merge_files.sh result-source-babel          # custom source
#   bash merge_files.sh result-source-babel merged-babel  # custom source + output
#
# Penamaan output:
#   bangka-belitung-1.txt, bangka-belitung-2.txt, ...
#
# Opsi (env var):
#   PREFIX=bangka-belitung   # prefix nama file (default: bangka-belitung)
#   PAD=4                    # zero-padding digit (default: otomatis dari total file)
# =============================================================================

set -euo pipefail

# ── Argumen & default ────────────────────────────────────────────────────────
SOURCE_DIR="${1:-result-source-babel}"
OUTPUT_DIR="${2:-merged}"
PREFIX="${PREFIX:-bangka-belitung}"

# Resolve ke path absolut relatif terhadap lokasi script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(realpath --canonicalize-missing "$SCRIPT_DIR/$SOURCE_DIR" 2>/dev/null || echo "$SOURCE_DIR")"
OUTPUT_DIR="$(realpath --canonicalize-missing "$SCRIPT_DIR/$OUTPUT_DIR" 2>/dev/null || echo "$OUTPUT_DIR")"

# ── Validasi ─────────────────────────────────────────────────────────────────
if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "[ERROR] Folder sumber tidak ditemukan: $SOURCE_DIR"
  exit 1
fi

if [[ "$(realpath "$OUTPUT_DIR" 2>/dev/null)" == "$(realpath "$SOURCE_DIR")" ]]; then
  echo "[ERROR] Output DIR sama dengan Source DIR — proses dibatalkan."
  exit 1
fi

# ── Kumpulkan semua file .txt (rekursif, diurutkan) ──────────────────────────
mapfile -t FILES < <(find "$SOURCE_DIR" -name "*.txt" | sort)
TOTAL=${#FILES[@]}

if [[ $TOTAL -eq 0 ]]; then
  echo "[INFO] Tidak ada file .txt ditemukan di: $SOURCE_DIR"
  exit 0
fi

# ── Tentukan zero-padding ────────────────────────────────────────────────────
PAD="${PAD:-${#TOTAL}}"   # otomatis: jumlah digit dari total file
[[ $PAD -lt 1 ]] && PAD=1

# ── Buat folder output (bersihkan jika sudah ada) ───────────────────────────
if [[ -d "$OUTPUT_DIR" ]]; then
  echo "[INFO] Folder output sudah ada, isi lama akan dihapus: $OUTPUT_DIR"
  rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

# ── Proses ───────────────────────────────────────────────────────────────────
echo "Sumber  : $SOURCE_DIR"
echo "Output  : $OUTPUT_DIR"
echo "Prefix  : $PREFIX"
echo "Total   : $TOTAL file"
echo "Padding : $PAD digit"
echo ""

COUNT=0
for SRC in "${FILES[@]}"; do
  COUNT=$((COUNT + 1))
  NUM=$(printf "%0${PAD}d" "$COUNT")
  DST="$OUTPUT_DIR/${PREFIX}-${NUM}.txt"
  cp "$SRC" "$DST"
done

echo "Selesai!"
echo "  File diproses : $TOTAL"
echo "  Output        : $OUTPUT_DIR/"
echo ""
echo "Contoh file:"
ls "$OUTPUT_DIR" | head -5
