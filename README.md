# PII Cleaner — WhatsApp Chat

Bersihkan data pribadi (PII) dari file chat WhatsApp `.txt`.

## PII yang dideteksi

| Jenis | Contoh | Label |
|-------|--------|-------|
| Nomor telepon | `081234567890`, `+62 812-3456-7890` | `[PHONE]` |
| Email | `nama@domain.com` | `[EMAIL]` |
| Nomor rekening | `1234567890` (setelah kata rekening, BCA, dll) | `[REKENING]` |

## Cara pakai

```bash
python3 clean_pii.py
```

Hasil bersih akan tersimpan di folder `result/` dengan struktur folder yang sama seperti `source/`.

## Struktur folder

```
.
├── source/            # Letakkan file chat .txt di sini
├── result/            # Output bersih (auto-generated)
├── clean_pii.py       # Entry point
├── find_phones.py     # Deteksi nomor telepon
├── find_emails.py     # Deteksi email
├── find_rekening.py   # Deteksi nomor rekening
├── tools.py           # Utility (rename, path, process_file)
└── README.md
```

## Contoh perubahan

**Sebelum:**
```
21/10/24 19.20 - +62 852-6871-2285: Assalamualaikum
transfer ke BCA 1234567890 a.n. Budi
kirim ke budi@example.com ya
```

**Sesudah:**
```
21/10/24 19.20 - [PHONE]: Assalamualaikum
transfer ke BCA [REKENING] a.n. Budi
kirim ke [EMAIL] ya
```
