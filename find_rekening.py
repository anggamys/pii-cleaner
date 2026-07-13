"""
find_rekening.py — Deteksi & bersihkan nomor rekening Indonesia (keyword-based).
"""

import re

REK_BRACKET_RE = re.compile(r"\[REKENING\](?:\s*\[REKENING\])+")

# Keyword pemicu rekening — pecah jadi beberapa alternatif biar rapi
KEYWORDS = (
    r"no\s*\.?\s*rek|norek|rekening|rek\."
    r"|a\.?\s*n\.?\s*|atas\s*nama|an\."
    r"|bca|mandiri|bni|bri|btn|muamalat|syariah"
    r"|transfer\s*(?:ke|rek)?"
    r"|npwp"
)

# Nomor rekening: 8-20 digit setelah keyword
REKENING_KEYWORD = re.compile(
    rf"(?:(?:{KEYWORDS})\s*[:=]?\s*)(\d[\d\s]{{7,19}})",
    re.IGNORECASE,
)

# Fallback: baris yg isinya cuma angka 8-20 digit dan tidak memenuhi syarat phone
STANDALONE_DIGITS = re.compile(r"^\s*(\d{8,20})\s*$")


def _bersihkan_digit(angka: str) -> str:
    """Hapus spasi dari string angka."""
    return re.sub(r"\s+", "", angka)


def _terlihat_seperti_rekening(angka: str) -> bool:
    """Cek apakah angka layak disebut nomor rekening (bukan phone)."""
    clean = _bersihkan_digit(angka)
    # Kalau diawali prefix HP Indonesia, skip
    if re.match(r"^(0\d{2,4}|62\d{2,4})", clean):
        return False
    return 8 <= len(clean) <= 20


def detect(line: str) -> list[str] | None:
    """Cari nomor rekening dalam baris. Return None jika tidak ada."""
    found = []

    # Pass 1: keyword-based (akurasi tinggi)
    for m in REKENING_KEYWORD.finditer(line):
        candidate = m.group(1).strip()
        if _terlihat_seperti_rekening(candidate):
            found.append(candidate)

    # Pass 2: standalone digits (hati-hati, false positive tinggi)
    # Hanya jika di baris sendiri dan tidak terdeteksi sebagai HP
    m = STANDALONE_DIGITS.match(line)
    if m and not found:
        candidate = m.group(1)
        if _terlihat_seperti_rekening(candidate):
            found.append(candidate)

    return found or None


def replace(line: str, items: list[str]) -> str:
    """Ganti nomor rekening dengan [REKENING]."""
    stripped = line.rstrip("\n")
    for rek in sorted(set(items), key=len, reverse=True):
        stripped = stripped.replace(rek, "[REKENING]", 1)
    stripped = REK_BRACKET_RE.sub("[REKENING]", stripped)
    return stripped + "\n"
