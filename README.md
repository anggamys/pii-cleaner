# Data Cleaning — WhatsApp Chat

Pipeline pembersihan data chat WhatsApp untuk keperluan riset NLP.

## Yang dibersihkan

### PII (Personal Identifiable Information)
| Jenis | Contoh | Label |
|---|---|---|
| Nomor telepon | `081234567890`, `+62 812-3456-7890` | `[PHONE]` |
| Email | `nama@domain.com` | `[EMAIL]` |
| Nomor rekening | `1234567890` (setelah kata rekening, BCA, dll) | `[REKENING]` |

### Template otomatis WhatsApp
| Jenis | Contoh | Aksi |
|---|---|---|
| Timestamp di awal baris | `24/07/24 09.43 - ` | Di-strip, teks chat tetap |
| Media placeholder (ID) | `<Media tidak disertakan>` | Baris dihapus |
| Media placeholder (EN) | `<Media omitted>` | Baris dihapus |
| Pesan enkripsi (ID) | `Pesan dan telepon terenkripsi secara end-to-end...` | Baris dihapus |
| Pesan enkripsi (EN) | `Messages and calls are end-to-end encrypted...` | Baris dihapus |

## Cara pakai

```bash
# Proses folder source/ (default)
python3 clean_pii.py

# Proses folder lain (path relatif atau absolut)
python3 clean_pii.py source-babel
python3 clean_pii.py archive/source-babel
python3 clean_pii.py /path/absolut/ke/folder
```

Output tersimpan otomatis di `result-<nama_folder>/` dengan struktur yang sama.

## Contoh perubahan

**Sebelum:**
```
24/07/24 09.43 - Pesan dan telepon terenkripsi secara end-to-end. Hanya orang di obrolan ini...
24/07/24 09.43 - Ayah: <Media tidak disertakan>
24/07/24 09.44 - Rafliansyah: transfer ke BCA 1234567890 a.n. Budi
24/07/24 09.45 - Rafliansyah: kirim ke budi@example.com ya
Jd kmren belajar mobil e
```

**Sesudah:**
```
Rafliansyah: transfer ke BCA [REKENING] a.n. Budi
Rafliansyah: kirim ke [EMAIL] ya
Jd kmren belajar mobil e
```

## Script lainnya

### `clean_text.py`
Membersihkan file `.txt` artikel berita dari baris boilerplate:
- `SCROLL TO CONTINUE WITH CONTENT`
- `Tonton juga video ...` / `Lihat juga Video ...` / `Simak juga Video ...`
- `[Gambas:Video 20detik]`
- Tanggal format `(DD/MM/YYYY)` seperti `(21/11/2025)`

```bash
python3 clean_text.py
```

### `hitung_token.py`
Menghitung total kalimat dan token dari file CSV pseudo label di `data_pseudo_label/`.

```bash
python3 hitung_token.py
```

## Struktur folder

```
.
├── source/               # Folder default input file chat .txt
├── result/               # Output default (auto-generated)
├── source-<nama>/        # Folder input alternatif
├── result-<nama>/        # Output sesuai folder input (auto-generated)
├── data_pseudo_label/    # File CSV hasil pseudo label
│
├── clean_pii.py          # Main script: bersihkan PII + template WA
├── clean_text.py         # Script: hapus baris boilerplate artikel
├── hitung_token.py       # Script: hitung kalimat & token dari CSV
│
├── find_phones.py        # Modul: deteksi nomor telepon
├── find_emails.py        # Modul: deteksi email
├── find_rekening.py      # Modul: deteksi nomor rekening
├── find_wa_template.py   # Modul: deteksi template WA (timestamp, media, enkripsi)
└── tools.py              # Utility: path, normalize, process_file
```
