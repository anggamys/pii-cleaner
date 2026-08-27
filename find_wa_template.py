"""
find_wa_template.py — Deteksi & bersihkan template otomatis dari export WhatsApp.

Yang ditangani:
  1. Timestamp di awal baris → di-strip, teks chat tetap
  2. Media placeholder (semua jenis) → baris dihapus
  3. Baris pesan enkripsi WA (ID & EN) → baris dihapus
  4. Pesan sistem otomatis WA (pesan dihapus, log telepon, dsb) → baris dihapus
"""

import re

# ── Timestamp WA ─────────────────────────────────────────────────────────────
# Grup 1: tanpa kurung siku (format lama / export dari HP)
#   DD/MM/YY HH.MM - ...
#   DD/MM/YYYY HH.MM - ...
#   DD/MM/YY, HH:MM am/pm - ...
_TS_NO_BRACKET = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4}"   # tanggal
    r"(?:,\s*|\s+)"                # pemisah
    r"\d{1,2}[.:]\d{2}"           # jam
    r"(?:\s*(?:am|pm))?"          # opsional am/pm
    r"\s+-\s+"                    # " - "
)

# Grup 2: dengan kurung siku (format iOS/Android baru, atau export zip)
#   [DD/MM/YY, HH.MM.SS] Nama: ...   (dengan detik)
#   [D/M HH.MM] Nama: ...            (tanpa tahun)
#   [D/M, HH:MM] Nama: ...           (EN tanpa tahun)
#   ‎[...] ... (dengan zero-width char di depan)
_TS_BRACKET = re.compile(
    r"^[‎‏‪-‮]*"   # opsional zero-width chars
    r"\["                               # kurung buka
    r"\d{1,2}/\d{1,2}"                 # D/M atau DD/MM
    r"(?:/\d{2,4})?"                   # opsional /YY atau /YYYY
    r"[,\s]+"                          # pemisah
    r"\d{1,2}[.:]\d{2}"               # jam
    r"(?:[.:]\d{2})?"                  # opsional detik
    r"(?:\s*(?:am|pm))?"              # opsional am/pm
    r"\]\s*"                           # kurung tutup + spasi
)

# Gabungan
WA_TIMESTAMP = re.compile(
    r"(?:" + _TS_NO_BRACKET.pattern + r"|" + _TS_BRACKET.pattern + r")"
)

# ── Call Logs Regex ──────────────────────────────────────────────────────────
_CALL_LOG_ALWAYS = re.compile(
    r"(?:panggilan gagal|call failed|missed voice call|missed video call|silenced voice call|silenced video call)",
    re.IGNORECASE
)

_CALL_LOG_CONDITIONAL = re.compile(
    r"(?:telepon suara|telepon video|telepon grup|voice call|video call|group call|panggilan suara|panggilan video|panggilan grup)",
    re.IGNORECASE
)

_CALL_LOG_DETAILS = re.compile(
    r"(?:tak terjawab|tidak dijawab|no answer|missed|silenced|diheningkan|ended|berakhir|"
    r"tap to call back|ketuk untuk menelepon balik|answered on other device|focus mode|mode fokus|"
    r"\d+\s*(?:dtk|mnt|jam|sec|min|hr|s|m|h|diundang|invited))",
    re.IGNORECASE
)


def _is_call_log(msg_lower: str) -> bool:
    if _CALL_LOG_ALWAYS.search(msg_lower):
        return True
    if _CALL_LOG_CONDITIONAL.search(msg_lower) and _CALL_LOG_DETAILS.search(msg_lower):
        return True
    return False


def detect(line: str) -> list[str] | None:
    """
    Cek apakah baris mengandung template WA.

    Return:
      None          → tidak ada template WA (biarkan apa adanya)
      ["MEDIA"]     → baris harus dihapus (media placeholder)
      ["ENKRIPSI"]  → baris harus dihapus (pesan enkripsi)
      ["SYSTEM"]    → baris harus dihapus (pesan otomatis/sistem lainnya)
      ["TIMESTAMP"] → timestamp ditemukan, replace() akan men-strip-nya
    """
    # 1. Cek apakah ada timestamp di awal baris
    match = WA_TIMESTAMP.match(line)
    if not match:
        # Jika tidak ada timestamp, kita hanya deteksi media/enkripsi yang barangkali terbungkus
        line_lower = line.lower()
        if any(x in line_lower for x in ["tidak disertakan", "omitted"]):
            return ["MEDIA"]
        if any(x in line_lower for x in ["terenkripsi secara end-to-end", "end-to-end encrypted"]):
            return ["ENKRIPSI"]
        return None

    # Ada timestamp! Mari potong timestamp untuk memeriksa bagian pesannya
    msg_part = line[match.end():]
    msg_lower = msg_part.lower()

    # 2. Cek Media placeholder
    if any(x in msg_lower for x in ["tidak disertakan", "omitted"]):
        return ["MEDIA"]

    # 3. Cek Enkripsi
    if any(x in msg_lower for x in ["terenkripsi secara end-to-end", "end-to-end encrypted"]):
        return ["ENKRIPSI"]

    # 4. Cek Pesan Dihapus
    if any(x in msg_lower for x in [
        "pesan ini dihapus",
        "pesan ini telah dihapus",
        "this message was deleted",
        "you deleted this message",
        "anda menghapus pesan ini",
    ]):
        return ["SYSTEM"]

    # 5. Cek Call Logs
    if _is_call_log(msg_lower):
        return ["SYSTEM"]

    # 6. Cek Group/Contact System Events
    # Ciri utama: tidak ada pengirim chat (tidak mengandung ": " setelah timestamp di-strip)
    if ": " not in msg_part:
        if any(x in msg_lower for x in [
            "kini menjadi kontak",
            "is now a contact",
            "membuat grup",
            "created group",
            "menambahkan",
            "added",
            "menyematkan pesan",
            "pinned a message",
            "mengubah setelan grup",
            "changed group settings",
            "mengubah deskripsi grup",
            "changed the group description",
            "mengubah subjek grup",
            "changed the group subject",
            "mengubah ikon grup",
            "changed the group icon",
            "mengeluarkan",
            "removed",
            "keluar",
            "left",
            "bergabung menggunakan tautan",
            "joined using a link",
            "mengganti nomor teleponnya ke nomor baru",
            "changed their phone number to a new number",
            "anda membuat grup ini",
            "you created this group"
        ]):
            return ["SYSTEM"]

    # 7. Jika hanya mengandung timestamp biasa (pesan chat normal)
    return ["TIMESTAMP"]


def replace(line: str, items: list[str]) -> str:
    """Strip timestamp dari awal baris."""
    if "TIMESTAMP" in items:
        return WA_TIMESTAMP.sub("", line)
    return line


def label(item: str) -> str:
    """Kembalikan label kategori untuk statistik."""
    return item
