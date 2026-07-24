# Panduan Penggunaan `clean_text.py`

Script `clean_text.py` digunakan untuk membersihkan file teks dari kalimat, frasa, atau atribut metadata yang tidak diperlukan (seperti teks iklan, tautan video sisipan, atau tanggal artikel) sebelum data diproses lebih lanjut.

## Cara Kerja

Script ini akan membaca setiap file `.txt` di dalam folder `source/`. Jika ditemukan **satu baris** yang mengandung kata kunci yang ditentukan, maka **seluruh baris tersebut akan dihapus**. 

File yang telah dibersihkan akan disimpan ke folder `result/` dengan mempertahankan nama file dan struktur sub-folder aslinya. Jika sebuah file tidak mengandung kata-kata yang harus dihapus, file tersebut akan tetap disalin secara utuh ke `result/`.

## Pola yang Dihapus

Secara bawaan (*default*), script ini akan menghapus baris yang mengandung:

1. **"SCROLL TO CONTINUE WITH CONTENT"** (teks iklan sisipan)
2. **"Tonton juga video .."** (ajakan menonton video)
3. **"[Gambas:Video 20detik]"** (kode embed video)
4. **"Lihat juga Video.."**
5. **"Simak juga Video.."**
6. **Tanggal berformat kurung** `(DD/MM/YYYY)` seperti `(21/11/2025)` atau `(01/01/2014)`.
   *Catatan: Tanggal dengan format teks biasa (misal: "21 November 2025") atau tanpa kurung tidak akan dihapus.*

## Cara Penggunaan

1. Pastikan file data sumber Anda berada di dalam folder `source/`.
2. Buka terminal/command prompt.
3. Jalankan perintah berikut:
   ```bash
   python3 clean_text.py
   ```
4. Output akan menampilkan ringkasan jumlah file yang diproses dan jumlah baris yang berhasil dihapus:
   ```
   Memproses penghapusan teks...
   Selesai
   Total file diproses : 727
   Total baris dihapus : 1267
   Output tersimpan di : result/
   ```

## Cara Menambah/Mengubah Teks yang Dihapus

Jika Anda ingin menambahkan kalimat lain untuk dihapus, buka file `clean_text.py` menggunakan teks editor dan tambahkan kata kuncinya di bagian `TEXT_TO_REMOVE`:

```python
TEXT_TO_REMOVE = [
    "SCROLL TO CONTINUE WITH CONTENT",
    "Tonton juga video",
    "[Gambas:Video 20detik]",
    "Lihat juga Video",
    "Simak juga Video",
    "KALIMAT BARU ANDA DI SINI", # <-- Tambahkan di sini
]
```

Cukup tulis kata awalan atau potongannya saja (tidak perlu kalimat utuh satu paragraf). Jika script menemukan teks tersebut di dalam sebuah baris, maka baris tersebut akan langsung dihapus.
