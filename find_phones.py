"""
find_phones.py — Deteksi & bersihkan nomor telepon Indonesia.
"""

import re

PHONE_BRACKET_RE = re.compile(r"\[PHONE\](?:\s*\[PHONE\])+")

RAW_PHONE = re.compile(
    r"(?:(?<=\s)|(?<=^)|(?<=: ))(0\d{7,15}|\+62\d{7,15})(?=\s|$|[.,;:!?)}\]]|‎)"
)

ID_PREFIXES = (
    "62811",
    "62812",
    "62813",
    "62814",
    "62815",
    "62816",
    "62817",
    "62818",
    "62819",
    "62821",
    "62822",
    "62823",
    "62831",
    "62832",
    "62833",
    "62851",
    "62852",
    "62853",
    "62855",
    "62856",
    "62857",
    "62858",
    "62871",
    "62872",
    "62873",
    "62877",
    "62878",
    "62879",
    "62881",
    "62882",
    "62883",
    "62888",
    "62889",
    "62895",
    "62896",
    "62897",
    "62898",
    "62899",
    "0811",
    "0812",
    "0813",
    "0814",
    "0815",
    "0816",
    "0817",
    "0818",
    "0819",
    "0821",
    "0822",
    "0823",
    "0831",
    "0832",
    "0833",
    "0834",
    "0835",
    "0836",
    "0837",
    "0838",
    "0839",
    "0851",
    "0852",
    "0853",
    "0855",
    "0856",
    "0857",
    "0858",
    "0859",
    "0877",
    "0878",
    "0879",
    "0881",
    "0882",
    "0883",
    "0884",
    "0885",
    "0886",
    "0887",
    "0888",
    "0889",
    "0895",
    "0896",
    "0897",
    "0898",
    "0899",
    "021",
    "022",
    "023",
    "024",
    "025",
    "026",
    "027",
    "028",
    "029",
    "031",
    "032",
    "033",
    "034",
    "035",
    "036",
    "037",
    "038",
    "039",
    "041",
    "042",
    "043",
    "044",
    "045",
    "046",
    "047",
    "048",
    "049",
    "051",
    "052",
    "053",
    "054",
    "055",
    "056",
    "057",
    "058",
    "059",
    "061",
    "062",
    "063",
    "064",
    "065",
    "066",
    "067",
    "068",
    "069",
    "071",
    "072",
    "073",
    "074",
    "075",
    "076",
    "077",
    "078",
    "079",
)


def is_indonesian_phone(num: str) -> bool:
    clean = re.sub(r"[\s-]", "", num)
    if clean.startswith("+62"):
        clean = "0" + clean[3:]
    for prefix in ID_PREFIXES:
        if clean.startswith(prefix):
            return True
    if re.match(r"^0\d{6,11}$", clean):
        area = [
            "021",
            "022",
            "071",
            "072",
            "073",
            "074",
            "075",
            "0761",
            "077",
            "078",
            "031",
            "032",
            "0331",
            "0341",
            "0351",
            "0361",
            "0371",
            "0411",
            "0541",
            "0551",
            "0561",
            "061",
            "0627",
        ]
        for ac in area:
            if clean.startswith(ac):
                return True
    return False


def detect(line: str) -> list[str] | None:
    """Cari nomor telepon. Return None jika tidak ada."""
    found = []
    for m in RAW_PHONE.finditer(line):
        if is_indonesian_phone(m.group(1)):
            found.append(m.group(1))
    for m in re.finditer(r"(0\d{2,4}[\s-]?\d{3,8}[\s-]?\d{2,8})", line):
        c = m.group(1)
        if c not in found and is_indonesian_phone(c):
            found.append(c)
    return found or None


def replace(line: str, items: list[str]) -> str:
    """Ganti nomor telepon dengan [PHONE]."""
    stripped = line.rstrip("\n")
    for phone in sorted(set(items), key=len, reverse=True):
        stripped = stripped.replace(phone, "[PHONE]", 1)
    stripped = PHONE_BRACKET_RE.sub("[PHONE]", stripped)
    return stripped + "\n"
