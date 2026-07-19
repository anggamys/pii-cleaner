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

## Script Lainnya

Selain membersihkan PII, project ini juga memiliki script tambahan:

1. **`clean_text.py`**
   Script ini akan membaca file `.txt` di folder `source/` dan **menghapus seluruh baris kalimat** jika mengandung teks spesifik, antara lain:
   - Kalimat "SCROLL TO CONTINUE WITH CONTENT"
   - Kalimat yang diawali "Tonton juga video .."
   - Kalimat "[Gambas:Video 20detik]"
   - Kalimat yang diawali "Lihat juga Video.."
   - Kalimat yang diawali "Simak juga Video.."
   - Tanggal dengan format khusus: `(DD/MM/YYYY)` seperti `(21/11/2025)`
   
   Cara pakai: `python3 clean_text.py`

2. **`hitung_token.py`**
   Script ini digunakan untuk menghitung total token dan total kalimat dari seluruh file pseudo label (berformat CSV) di dalam folder `data_pseudo_label/`.
   
   Cara pakai: `python3 hitung_token.py`

## Struktur folder

```
.
├── source/            # Letakkan file chat .txt di sini
├── result/            # Output bersih (auto-generated)
├── data_pseudo_label/ # Kumpulan file CSV hasil pseudo label
├── clean_pii.py       # Main script untuk membersihkan PII
├── clean_text.py      # Script untuk hapus baris/kalimat spesifik
├── hitung_token.py    # Script untuk hitung kalimat & token CSV
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
