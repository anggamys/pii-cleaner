"""
find_wa_template.py — Deteksi & bersihkan template otomatis dari export WhatsApp.

Yang ditangani:
  1. Timestamp di awal baris → di-strip, teks chat tetap
  2. Baris <Media tidak disertakan> / <Media omitted> → baris dihapus (return None)
  3. Baris pesan enkripsi WA (ID & EN) → baris dihapus (return None)

Kontrak fungsi (sama dengan modul find_*.py lainnya):
  detect(line) -> list[str] | None
    - None  : baris harus dihapus seluruhnya
    - list  : daftar pola yang ditemukan (untuk statistik), tapi baris tetap ada
              Khusus modul ini: kembalikan ["TIMESTAMP"] jika timestamp di-strip
  replace(line, items) -> str
    - Return baris yang sudah dibersihkan (timestamp di-strip)
    - Jika items berisi "MEDIA" atau "ENKRIPSI" → return "" (baris kosong/dihapus)
"""

import re

# ── Pola timestamp WA di awal baris ──────────────────────────────────────────
# Format yang ditangani:
#   DD/MM/YY HH.MM - ...         (export ID, 2-digit year)
#   DD/MM/YYYY HH.MM - ...       (export ID, 4-digit year)
#   DD/MM/YY, HH:MM am/pm - ...  (export EN, 2-digit year)
#   M/D/YY, HH:MM - ...          (export EN singkat)
WA_TIMESTAMP = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4}"   # tanggal: D/M/YY atau DD/MM/YYYY
    r"(?:,\s*|\s+)"                # pemisah: koma+spasi atau spasi langsung
    r"\d{1,2}[.:]\d{2}"           # jam: HH.MM atau HH:MM
    r"(?:\s*(?:am|pm))?"          # opsional am/pm (export EN)
    r"\s+-\s+"                    # " - " pemisah ke pengirim/konten
)

# ── Pola baris yang harus dihapus seluruhnya ─────────────────────────────────
_REMOVE = [
    # Media placeholder
    (re.compile(r"<Media tidak disertakan>\s*$", re.IGNORECASE), "MEDIA"),
    (re.compile(r"<Media omitted>\s*$",          re.IGNORECASE), "MEDIA"),
    # Pesan enkripsi WA (ID)
    (re.compile(r"terenkripsi secara end-to-end", re.IGNORECASE), "ENKRIPSI"),
    # Pesan enkripsi WA (EN)
    (re.compile(r"end-to-end encrypted",          re.IGNORECASE), "ENKRIPSI"),
]


def detect(line: str) -> list[str] | None:
    """
    Cek apakah baris mengandung template WA.

    Return:
      None          → baris tidak mengandung template WA apapun (biarkan apa adanya)
      ["MEDIA"]     → baris harus dihapus (media placeholder)
      ["ENKRIPSI"]  → baris harus dihapus (pesan enkripsi)
      ["TIMESTAMP"] → timestamp ditemukan, replace() akan men-strip-nya
    """
    # Cek pola yang mewajibkan baris dihapus
    for pattern, cat in _REMOVE:
        if pattern.search(line):
            return [cat]

    # Cek timestamp di awal baris
    if WA_TIMESTAMP.match(line):
        return ["TIMESTAMP"]

    return None


def replace(line: str, items: list[str]) -> str:
    """
    Bersihkan baris dari template WA.

    - items == ["TIMESTAMP"] → strip timestamp, kembalikan sisa baris
    - items == ["MEDIA"] / ["ENKRIPSI"] → tidak dipanggil (baris sudah dibuang di clean_pii)
    """
    if "TIMESTAMP" in items:
        return WA_TIMESTAMP.sub("", line)
    return line


def label(item: str) -> str:
    """Kembalikan label kategori untuk keperluan statistik."""
    return item  # sudah berupa "TIMESTAMP", "MEDIA", "ENKRIPSI"
