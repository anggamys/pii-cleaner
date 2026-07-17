import os
import glob
import pandas as pd

def analyze_all_csv(folder_path):
    print("Menganalisis file CSV...")

    total_files = 0
    grand_total_tokens = 0
    grand_total_sentences = 0

    # Cari semua file CSV di dalam folder
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    for filepath in csv_files:
        try:
            # Baca CSV, hanya kolom yang dibutuhkan agar hemat memori
            df = pd.read_csv(filepath, usecols=['sentence_id'])

            tokens_in_file = len(df)
            sentences_in_file = df['sentence_id'].nunique()

            grand_total_tokens += tokens_in_file
            grand_total_sentences += sentences_in_file
            total_files += 1

        except Exception as e:
            # Jika file kosong atau korup
            print(f"Error baca {os.path.basename(filepath)}: {e}")

    print("Hasil Rekapitulasi Keseluruhan")
    print(f"Total File CSV  : {total_files:,}")
    print(f"Total Kalimat   : {grand_total_sentences:,}")
    print(f"Total Token     : {grand_total_tokens:,}")

    if grand_total_sentences > 0:
        print(f"Rata-rata token / kalimat : {grand_total_tokens/grand_total_sentences:.2f}")

if __name__ == "__main__":
    folder_path = "data_pseudo_label"

    if not os.path.isdir(folder_path):
        print(f"Folder '{folder_path}' tidak ditemukan!")
    else:
        analyze_all_csv(folder_path)
