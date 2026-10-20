# PRODUCT REQUIREMENT DOCUMENT (PRD)
## Access TV – Accessible TV Streaming Addon for NVDA

* **Dokumen:** Spesifikasi Kebutuhan Produk (PRD)
* **Nama Proyek:** Access TV (NVDA TV Streamer Addon)
* **Target Pengembang:** Joni (Coding Agent Hermes)
* **Owner / Inisiator:** Mahfud Pg & Dani (Tim Studio Hermes)
* **Platform Target:** NVDA Screen Reader (Windows 10/11, Python 3.11+ environment NVDA)
* **Format Output:** Berkas paket `.nvda-addon` (Siap pasang)
* **Status:** Ready for Implementation

---

## 1. Latar Belakang & Tujuan Produk
Banyak pengguna tunanetra mengalami kendala saat mengakses siaran televisi melalui web browser akibat:
1. Antarmuka web yang berat dan sarat iklan pop-up.
2. Kontrol video player web yang sering tidak terbaca (*unlabeled buttons*) oleh pembaca layar.
3. Kebutuhan utama pengguna tunanetra pada siaran TV (berita, talkshow, sinetron, olahraga) adalah **konten audio yang jernih, instan, dan hemat daya**.

**HarmoniTV** dirancang sebagai addon resmi NVDA yang menyediakan akses siaran TV streaming (Indonesia dan mancanegara) secara **Audio-First**, ringan, responsif, dan 100% aksesibel menggunakan kontrol keyboard standar Windows.

---

## 2. Karakteristik & Filosofi Desain
1. **100% Aksesibilitas NVDA:** Seluruh antarmuka menggunakan kontrol native `wxPython` (standar NVDA UI) agar seluruh label, tombol, slider, dan listbox terbaca sempurna oleh NVDA.
2. **Audio-First & Ringan:** Pemutaran fokus pada aliran audio murni (mengabaikan rendering video berat) sehingga penggunaan CPU < 1%, RAM minimal, dan laptop tidak panas.
3. **Pencarian Cepat & Minim Ketukan Keyboard:** Memungkinkan pengguna menemukan stasiun TV dalam hitungan detik tanpa harus menelusuri ribuan saluran secara manual.
4. **Biaya Rp 0 (Free & Legal):** Memanfaatkan daftar siaran Free-To-Air (FTA) dan direktori publik terbuka (seperti repositori terkurasi `iptv-org`).

---

## 3. Fitur Utama (Functional Requirements)

### 3.1. Pemilihan Negara (Country Selector)
* Antarmuka menyediakan ComboBox / Dropdown daftar negara.
* **Default Negara:** Indonesia (ID).
* Menyertakan negara-negara populer lainnya (Malaysia, Singapura, Arab Saudi, Inggris, Amerika Serikat, Jepang, dll) serta opsi *"Semua Negara / Global"*.
* Pemilihan negara langsung memperbarui daftar saluran di bawahnya secara instan tanpa membuat NVDA macet (*non-blocking asynchronous update*).

### 3.2. Daftar Saluran TV (Channel List)
* Menampilkan saluran TV resmi yang aktif berdasarkan negara yang dipilih.
* Navigasi list menggunakan Panah Bawah / Panah Atas.
* Menekan tombol **Enter** atau **Spasi** pada saluran langsung memulai pemutaran audio siaran.
* Status siaran (Playing / Buffering / Stopped / Error) dibacakan langsung oleh NVDA via speech announcement (`ui.message`).

### 3.3. Kotak Pencarian Cepat (Instant Search Box)
* Kolom edit teks (`wx.TextCtrl`) yang terletak sebelum daftar saluran.
* Pengguna cukup mengetikkan kata kunci (misal: *"Kompas"*, *"Metro"*, *"TVRI"*, *"Al Jazeera"*).
* Daftar saluran langsung difilter secara real-time saat pengguna mengetik, atau saat menekan Enter.

### 3.4. Manajemen Favorit (Favorites Management)
* **Tambah ke Favorit:** Tombol atau shortcut keyboard (misal: tombol aplikasi / context menu atau tombol khusus `Tambah ke Favorit`) untuk menyimpan saluran yang sedang dipilih.
* **Hapus dari Favorit:** Kemampuan menghapus saluran yang sudah tersimpan di daftar favorit.
* **Tab / Filter Favorit:** Menyediakan filter cepat atau tab khusus yang hanya menampilkan saluran-saluran favorit pengguna.
* Data favorit disimpan secara permanen ke file `favorites.json` di folder konfigurasi pengguna NVDA agar tidak hilang saat NVDA direstart.

### 3.5. Slider Pengatur Volume (Volume Slider)
* Kontrol slider native (`wx.Slider`) dengan rentang 0 s/d 100%.
* Dapat dikontrol dengan Panah Kiri/Kanan atau Panah Bawah/Atas.
* NVDA membacakan persentase volume secara real-time (misal: "Volume 50%").
* Volume terakhir disimpan dan diingat otomatis untuk sesi pemutaran berikutnya.

### 3.6. Kontrol Pemutaran Global & Shortcut Keyboard
* **Tombol Dialog Utama:** Shortcut global (misal: `Ctrl + Windows + A`) untuk membuka dialog Access TV dari aplikasi apa pun.
* **Play / Pause / Stop:**
  * Tombol dialog atau shortcut global untuk Menghentikan / Melanjutkan siaran (misal: `Ctrl + Windows + Shift + S` untuk Stop siaran instan tanpa buka menu).
* **Info Siaran:** Shortcut cepat untuk membaca nama saluran yang sedang aktif diputar.

---

## 4. Arsitektur Teknis & Kebutuhan Koding (Untuk Joni)

### 4.1. Struktur Berkas Addon
```text
HarmoniTV/
├── manifest.ini               # Metadata addon NVDA (nama, versi, kompatibilitas 2024.x+)
├── buildVars.py               # Skrip deklarasi build scons
├── docHandler.py              # Handler dokumentasi standar NVDA
└── globalPlugins/
    └── harmoniTV/
        ├── __init__.py        # GlobalPlugin: registrasi gesture shortcut & menu tools NVDA
        ├── gui_dialog.py      # Antarmuka wxPython (Search, Combo Negara, List, Slider)
        ├── player_engine.py   # Mesin pemutar audio streaming (BASS / Headless MPV)
        ├── channel_manager.py # Manajemen database saluran & filter negara
        ├── favorites.py       # Handler JSON read/write favorit pengguna
        └── data/
            ├── channels_id.json    # Cache daftar TV Indonesia utama (offline-ready)
            └── countries.json      # Daftar metadata negara
```

### 4.2. Mesin Pemutar Audio (Player Engine)
* **Rekomendasi Pilihan 1 (Utama):** Menggunakan pustaka audio **BASS library** (`bass.dll` dan `basshls.dll`) yang sudah biasa terintegrasi dengan modul NVDA. BASS sangat stabil menangani streaming HLS (`.m3u8`) dengan latensi rendah dan konsumsi memori minim.
* **Pilihan 2 (Alternatif):** Biner `mpv.exe` portable yang dipanggil dalam mode *headless* (`--no-video --volume=...`) via proses terisolasi.

### 4.3. Sumber Data Saluran (Channels Source)
1. **Bundled Core List (Indonesia):** Menyertakan file lokal `channels_id.json` berisi saluran utama Indonesia (Kompas TV, Metro TV, TVRI Nasional, TVOne, CNN Indonesia, CNBC Indonesia, Trans TV, Trans7, RTV, Net TV, dll) agar addon langsung jalan tanpa ketergantungan fetch jaringan pertama kali.
2. **Global Sync (Opsional/Background):** Mengambil data negara lain secara modular dari repositori publik terpercaya (`https://iptv-org.github.io/api/channels.json` dan `streams.json`).

---

## 5. Alur Navigasi Tab Keyboard (Tab Order & UX)
Pengguna tunanetra mengutamakan navigasi tab yang efisien:
1. **Fokus Awal:** Langsung masuk ke `Kotak Pencarian Saluran` (Text Ctrl).
2. **Tab 1x:** `Pilihan Negara` (ComboBox, Panah Atas/Bawah untuk ganti negara).
3. **Tab 2x:** `Filter Tampilan` (Radio button / Checkbox: "Semua Saluran" vs "Favorit Saja").
4. **Tab 3x:** `Daftar Saluran TV` (ListBox, Panah Atas/Bawah, Enter untuk Play).
5. **Tab 4x:** Tombol `Play / Stop`.
6. **Tab 5x:** Tombol `Tambah / Hapus Favorit`.
7. **Tab 6x:** `Slider Volume` (Slider 0-100%).
8. **Tab 7x:** Tombol `Tutup`.

---

## 6. Kriteria Keberhasilan (Acceptance Criteria)
- [ ] Berkas berhasil dikompilasi menjadi `HarmoniTV.nvda-addon`.
- [ ] Dapat diinstal pada NVDA versi terbaru tanpa peringatan error kompatibilitas.
- [ ] NVDA membacakan setiap komponen dengan nama yang jelas tanpa ada tombol tanpa label.
- [ ] Siaran TV Indonesia utama (TVRI, Kompas TV, Metro TV, dll) dapat berbunyi dalam waktu kurang dari 3 detik setelah ditekan Enter.
- [ ] Menambahkan dan menghapus favorit berjalan mulus dan tersimpan ke disk.
- [ ] Pencarian instan menyaring daftar saluran secara responsif tanpa lag.
- [ ] Penggunaan memori dan CPU saat memutar siaran tidak mengganggu kelancaran bicara screen reader NVDA.
