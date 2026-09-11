"""
find_emails.py — Deteksi & bersihkan alamat email.
"""

import re

EMAIL_RE = re.compile(r"[\w\.\-]+@[\w\.\-]+\.\w+")
EMAIL_BRACKET_RE = re.compile(r"\[EMAIL\](?:\s*\[EMAIL\])+")


def detect(line: str) -> list[str] | None:
    """Cari semua email dalam baris. Return None jika tidak ada."""
    found = list(EMAIL_RE.findall(line))
    return found or None


def replace(line: str, items: list[str]) -> str:
    """Ganti email dengan [EMAIL]."""
    stripped = line.rstrip("\n")
    for email in sorted(set(items), key=len, reverse=True):
        stripped = stripped.replace(email, "[EMAIL]", 1)
    stripped = EMAIL_BRACKET_RE.sub("[EMAIL]", stripped)
    return stripped + "\n"
