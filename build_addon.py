# -*- coding: utf-8 -*-
"""
Access TV - NVDA Addon Build & Packaging Script
Mengompilasi seluruh struktur kode, pustaka audio BASS, dan data saluran menjadi berkas resmi AccessTV.nvda-addon.
"""

import os
import zipfile
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ADDON = os.path.join(ROOT_DIR, 'AccessTV.nvda-addon')

FILES_TO_INCLUDE = [
    'manifest.ini',
    'readme.html',
]

DIRS_TO_INCLUDE = [
    'doc',
    'globalPlugins',
]

EXCLUDE_EXTS = {'.pyc', '.pyo', '.tmp'}
EXCLUDE_DIRS = {'__pycache__', '.git', '.vscode'}

def build_addon():
    print(f"Memulai pembuatan paket NVDA Addon: {OUTPUT_ADDON}")

    if os.path.exists(OUTPUT_ADDON):
        try:
            os.remove(OUTPUT_ADDON)
            print("Berkas addon lama dibersihkan.")
        except Exception as e:
            print(f"Gagal menghapus berkas lama: {e}")

    added_files = 0
    with zipfile.ZipFile(OUTPUT_ADDON, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Masukkan berkas root
        for fname in FILES_TO_INCLUDE:
            fpath = os.path.join(ROOT_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)
                print(f" + Menambahkan: {fname}")
                added_files += 1

        # 2. Masukkan direktori
        for dname in DIRS_TO_INCLUDE:
            dpath = os.path.join(ROOT_DIR, dname)
            if not os.path.exists(dpath):
                continue

            for root, dirs, files in os.walk(dpath):
                # Filter folder yang diabaikan
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in EXCLUDE_EXTS or file.endswith('~'):
                        continue

                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, ROOT_DIR)
                    # Normalisasi path untuk zip (forward slash)
                    arc_name = rel_path.replace('\\', '/')

                    zf.write(full_path, arcname=arc_name)
                    added_files += 1

    sz = os.path.getsize(OUTPUT_ADDON)
    print(f"\nSukses! Paket berhasil dibuat: {OUTPUT_ADDON}")
    print(f"Total berkas di dalam paket: {added_files}")
    print(f"Ukuran paket: {sz:,} bytes ({sz / (1024 * 1024):.2f} MB)")

if __name__ == '__main__':
    build_addon()
