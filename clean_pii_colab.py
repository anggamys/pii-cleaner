# Cell 1 — Setup & Import
# RUN CELL INI TERLEBIH DAHULU.
# Tidak ada yang perlu diubah di cell ini.
import os
import re
import shutil
import zipfile
import tempfile
from google.colab import files

# Cell 2 — Deteksi Template WhatsApp
# Fungsi: mendeteksi timestamp, media, enkripsi, dan pesan sistem WhatsApp.
# Timestamp akan di-strip. Baris media/enkripsi/sistem akan dihapus.
#
# Penyesuaian:
# - Jika timestamp tidak terdeteksi, cek format tanggal di _TS_NO_BRACKET / _TS_BRACKET.
# - Untuk menambah kata kunci pesan sistem, tambahkan di list pada baris 84-98.
# - Format WhatsApp lain? Tambah regex baru di WA_TIMESTAMP.
_TS_NO_BRACKET = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4}"
    r"(?:,\s*|\s+)"
    r"\d{1,2}[.:]\d{2}"
    r"(?:\s*(?:am|pm))?"
    r"\s+-\s+"
)

_TS_BRACKET = re.compile(
    r"^[‎‏‪-‮]*"
    r"\["
    r"\d{1,2}/\d{1,2}"
    r"(?:/\d{2,4})?"
    r"[,\s]+"
    r"\d{1,2}[.:]\d{2}"
    r"(?:[.:]\d{2})?"
    r"(?:\s*(?:am|pm))?"
    r"\]\s*"
)

WA_TIMESTAMP = re.compile(
    r"(?:" + _TS_NO_BRACKET.pattern + r"|" + _TS_BRACKET.pattern + r")"
)

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

def _is_call_log(msg_lower):
    if _CALL_LOG_ALWAYS.search(msg_lower):
        return True
    if _CALL_LOG_CONDITIONAL.search(msg_lower) and _CALL_LOG_DETAILS.search(msg_lower):
        return True
    return False

def detect_wa(line):
    match = WA_TIMESTAMP.match(line)
    if not match:
        line_lower = line.lower()
        if any(x in line_lower for x in ["tidak disertakan", "omitted"]):
            return ["MEDIA"]
        if any(x in line_lower for x in ["terenkripsi secara end-to-end", "end-to-end encrypted"]):
            return ["ENKRIPSI"]
        return None
    msg_part = line[match.end():]
    msg_lower = msg_part.lower()
    if any(x in msg_lower for x in ["tidak disertakan", "omitted"]):
        return ["MEDIA"]
    if any(x in msg_lower for x in ["terenkripsi secara end-to-end", "end-to-end encrypted"]):
        return ["ENKRIPSI"]
    if any(x in msg_lower for x in [
        "pesan ini dihapus", "pesan ini telah dihapus",
        "this message was deleted", "you deleted this message",
        "anda menghapus pesan ini",
    ]):
        return ["SYSTEM"]
    if _is_call_log(msg_lower):
        return ["SYSTEM"]
    if ": " not in msg_part:
        if any(x in msg_lower for x in [
            "kini menjadi kontak", "is now a contact",
            "membuat grup", "created group",
            "menambahkan", "added",
            "menyematkan pesan", "pinned a message",
            "mengubah setelan grup", "changed group settings",
            "mengubah deskripsi grup", "changed the group description",
            "mengubah subjek grup", "changed the group subject",
            "mengubah ikon grup", "changed the group icon",
            "mengeluarkan", "removed",
            "keluar", "left",
            "bergabung menggunakan tautan", "joined using a link",
            "mengganti nomor teleponnya ke nomor baru",
            "changed their phone number to a new number",
            "anda membuat grup ini", "you created this group",
        ]):
            return ["SYSTEM"]
    return ["TIMESTAMP"]

def replace_wa(line, items):
    if "TIMESTAMP" in items:
        return WA_TIMESTAMP.sub("", line)
    return line

# Cell 3 — Deteksi PII (Phone, Email, Rekening)
# Fungsi: mendeteksi dan mengganti nomor telepon, email, dan nomor rekening.
# Hasil: [PHONE], [EMAIL], [REKENING]
#
# Penyesuaian:
# - Nomor telepon tidak terdeteksi? Tambah prefix di ID_PREFIXES (Cell 3 bagian Phone).
# - Email tidak terdeteksi? Cek regex EMAIL_RE.
# - Rekening tidak terdeteksi? Tambah keyword di REK_KEYWORDS.

# --- Phone ---
PHONE_BRACKET_RE = re.compile(r"\[PHONE\](?:\s*\[PHONE\])+")
RAW_PHONE = re.compile(
    r"(?:(?<=\s)|(?<=^)|(?<=: ))((?:0|\+62[\s-]?)\d{7,15})(?=\s|$|[.,;:!?)}\]]|‎)"
)
ID_PREFIXES = (
    "62811","62812","62813","62814","62815","62816","62817","62818","62819",
    "62821","62822","62823","62831","62832","62833",
    "62851","62852","62853","62855","62856","62857","62858",
    "62871","62872","62873","62877","62878","62879",
    "62881","62882","62883","62888","62889","62895","62896","62897","62898","62899",
    "0811","0812","0813","0814","0815","0816","0817","0818","0819",
    "0821","0822","0823","0831","0832","0833","0834","0835","0836","0837","0838","0839",
    "0851","0852","0853","0855","0856","0857","0858","0859",
    "0877","0878","0879","0881","0882","0883","0884","0885","0886","0887","0888","0889",
    "0895","0896","0897","0898","0899",
    "021","022","023","024","025","026","027","028","029",
    "031","032","033","034","035","036","037","038","039",
    "041","042","043","044","045","046","047","048","049",
    "051","052","053","054","055","056","057","058","059",
    "061","062","063","064","065","066","067","068","069",
    "071","072","073","074","075","076","077","078","079",
)

def _is_indonesian_phone(num):
    clean = re.sub(r"[\s-]", "", num)
    if clean.startswith("+62"):
        clean = "0" + clean[3:]
    for prefix in ID_PREFIXES:
        if clean.startswith(prefix):
            return True
    if re.match(r"^0\d{6,11}$", clean):
        area = ["021","022","071","072","073","074","075","0761","077","078",
                "031","032","0331","0341","0351","0361","0371","0411","0541","0551","0561","061","0627"]
        for ac in area:
            if clean.startswith(ac):
                return True
    return False

def detect_phone(line):
    found = []
    for m in RAW_PHONE.finditer(line):
        if _is_indonesian_phone(m.group(1)):
            found.append(m.group(1))
    for m in re.finditer(r"((?:\+62[\s-]?|0)\d{2,4}[\s-]?\d{3,8}[\s-]?\d{2,8})", line):
        c = m.group(1)
        if c not in found and _is_indonesian_phone(c):
            found.append(c)
    return found or None

def replace_phone(line, items):
    stripped = line.rstrip("\n")
    for phone in sorted(set(items), key=len, reverse=True):
        stripped = stripped.replace(phone, "[PHONE]", 1)
    stripped = PHONE_BRACKET_RE.sub("[PHONE]", stripped)
    return stripped + "\n"

# --- Email ---
EMAIL_RE = re.compile(r"[\w\.\-]+@[\w\.\-]+\.\w+")
EMAIL_BRACKET_RE = re.compile(r"\[EMAIL\](?:\s*\[EMAIL\])+")

def detect_email(line):
    found = list(EMAIL_RE.findall(line))
    return found or None

def replace_email(line, items):
    stripped = line.rstrip("\n")
    for email in sorted(set(items), key=len, reverse=True):
        stripped = stripped.replace(email, "[EMAIL]", 1)
    stripped = EMAIL_BRACKET_RE.sub("[EMAIL]", stripped)
    return stripped + "\n"

# --- Rekening ---
REK_BRACKET_RE = re.compile(r"\[REKENING\](?:\s*\[REKENING\])+")
REK_KEYWORDS = (
    r"no\s*\.?\s*rek|norek|rekening|rek\."
    r"|a\.?\s*n\.?\s*|atas\s*nama|an\."
    r"|bca|mandiri|bni|bri|btn|muamalat|syariah"
    r"|transfer\s*(?:ke|rek)?"
    r"|npwp"
)
REKENING_KEYWORD = re.compile(
    rf"(?:(?:{REK_KEYWORDS})\s*[:=]?\s*)(\d[\d\s]{{7,19}})",
    re.IGNORECASE,
)
STANDALONE_DIGITS = re.compile(r"^\s*(\d{8,20})\s*$")

def _terlihat_seperti_rekening(angka):
    clean = re.sub(r"\s+", "", angka)
    if re.match(r"^(0\d{2,4}|62\d{2,4})", clean):
        return False
    return 8 <= len(clean) <= 20

def detect_rekening(line):
    found = []
    for m in REKENING_KEYWORD.finditer(line):
        candidate = m.group(1).strip()
        if _terlihat_seperti_rekening(candidate):
            found.append(candidate)
    m = STANDALONE_DIGITS.match(line)
    if m and not found:
        candidate = m.group(1)
        if _terlihat_seperti_rekening(candidate):
            found.append(candidate)
    return found or None

def replace_rekening(line, items):
    stripped = line.rstrip("\n")
    for rek in sorted(set(items), key=len, reverse=True):
        stripped = stripped.replace(rek, "[REKENING]", 1)
    stripped = REK_BRACKET_RE.sub("[REKENING]", stripped)
    return stripped + "\n"

# Cell 4 — Utility & Core Processing
# Fungsi: pemrosesan file, normalisasi nama, pipeline bersihkan satu file.
# Tidak perlu diubah kecuali ingin menambah jenis PII baru.
PII_STEPS = [
    (detect_phone,    replace_phone),
    (detect_email,    replace_email),
    (detect_rekening, replace_rekening),
]

def normalize_filename(name):
    name = name.lower()
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w\.\-]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name

def process_file_wa(src, dst):
    with open(src, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    out_lines = []
    stat = {"media":0,"enkripsi":0,"system":0,"timestamp":0,
            "phone":0,"email":0,"rekening":0}
    for line in lines:
        wa_items = detect_wa(line)
        if wa_items is None:
            pass
        elif wa_items[0] in ("MEDIA","ENKRIPSI","SYSTEM"):
            stat[wa_items[0].lower() if wa_items[0]!="ENKRIPSI" else "enkripsi"] += 1
            continue
        else:
            line = replace_wa(line, wa_items)
            stat["timestamp"] += 1
        for detect_fn, replace_fn in PII_STEPS:
            items = detect_fn(line)
            if items:
                if detect_fn is detect_phone:    stat["phone"]    += len(items)
                elif detect_fn is detect_email:   stat["email"]    += len(items)
                elif detect_fn is detect_rekening: stat["rekening"] += len(items)
                line = replace_fn(line, items)
        out_lines.append(line)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.writelines(out_lines)
    return stat

# Cell 5 — Upload File Chat WhatsApp
# RUN CELL INI, lalu pilih file yang akan dibersihkan.
# Format yang didukung: .txt (file langsung) atau .zip (bisa isi banyak folder).
# Jika upload .zip, akan diekstrak otomatis ke folder source/.
#
# Penyesuaian:
# - Jika file tidak terbaca, pastikan encoding UTF-8.
# - Jika ingin proses folder yang sudah ada di Colab, ubah WORK_DIR.
WORK_DIR = "/content/clean_pii_work"
SOURCE_DIR = os.path.join(WORK_DIR, "source")
OUTPUT_DIR = os.path.join(WORK_DIR, "result")

if os.path.isdir(WORK_DIR):
    shutil.rmtree(WORK_DIR)
os.makedirs(SOURCE_DIR, exist_ok=True)

print("Upload file chat WhatsApp (.txt atau .zip):")
uploaded = files.upload()

for fname, data in uploaded.items():
    save_path = os.path.join(WORK_DIR, fname)
    with open(save_path, "wb") as f:
        f.write(data)
    if fname.endswith(".zip"):
        with zipfile.ZipFile(save_path, "r") as z:
            z.extractall(SOURCE_DIR)
        os.remove(save_path)
        print(f"  {fname} → diekstrak ke {SOURCE_DIR}")
    elif fname.endswith(".txt"):
        dest = os.path.join(SOURCE_DIR, fname)
        shutil.move(save_path, dest)
        print(f"  {fname} → {dest}")
    else:
        print(f"  {fname} → dilewati (bukan .txt/.zip)")

print("\nFile siap diproses!")

# Cell 6 — Jalankan Pembersihan
# Jalankan cell ini untuk memproses semua file yang sudah di-upload.
# Hasil: statistik jumlah file, baris yang dihapus, dan PII yang diganti.
total = {"file":0,"media":0,"enkripsi":0,"system":0,"timestamp":0,
         "phone":0,"email":0,"rekening":0}

for root, _, files_list in os.walk(SOURCE_DIR):
    for fname in files_list:
        if not fname.lower().endswith(".txt"):
            continue
        src = os.path.join(root, fname)
        rel = os.path.relpath(src, SOURCE_DIR)
        parts = rel.split(os.sep)
        normalized = [normalize_filename(p) for p in parts]
        dst = os.path.join(OUTPUT_DIR, *normalized)
        stat = process_file_wa(src, dst)
        total["file"] += 1
        for k in stat:
            total[k] += stat[k]

total_pii = total["phone"] + total["email"] + total["rekening"]
print("Selesai!")
print(f"  File diproses   : {total['file']}")
print(f"  Baris dihapus   : media={total['media']}, enkripsi={total['enkripsi']}, system={total['system']}")
print(f"  Timestamp strip : {total['timestamp']}")
print(f"  PII diganti     : phone={total['phone']}, email={total['email']}, rekening={total['rekening']}")
print(f"  Output          : {OUTPUT_DIR}")

# Cell 7 — Download Hasil
# Jalankan cell ini untuk mengunduh hasil pembersihan dalam format .zip.
# File akan diunduh ke komputer Anda.
result_zip = "/content/clean_pii_result"
shutil.make_archive(result_zip, "zip", OUTPUT_DIR)
print(f"Download: {result_zip}.zip")
files.download(f"{result_zip}.zip")
