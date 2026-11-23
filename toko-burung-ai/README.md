# 🐦 Si Kicau: Asisten AI Toko Burung

Asisten AI untuk toko burung keluarga. Pembeli bisa bertanya harga, stok, rekomendasi burung, dan cara merawat burung lewat chat. Pemilik toko (orang tua) punya menu sendiri untuk mengecek barang yang harus dibeli ulang, mengubah stok dan harga, mencatat penjualan, dan meminta AI membuatkan caption promosi.

Dibuat dengan **Gemini API** (function calling) dan **Streamlit**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-red?logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-API-blue?logo=google)

---

## ✨ Fitur

**Untuk pembeli (mode Pelanggan)**
- 💬 Tanya harga dan stok dengan bahasa sehari-hari ("ada lovebird di bawah 300 ribu?")
- 🐣 Rekomendasi burung untuk pemula, lengkap dengan pakan dan sangkar yang dibutuhkan
- 📖 Tips perawatan per jenis burung dari catatan toko sendiri
- 🧾 Hitung total pesanan dan buat link WhatsApp siap kirim ke toko
- 🛒 Katalog produk dengan filter kategori dan pencarian

**Untuk pemilik toko (mode Pemilik, bisa dikunci PIN)**
- 📦 Ubah stok, harga, dan tambah produk baru langsung di tabel
- ⚠️ Peringatan otomatis untuk barang yang stoknya menipis
- 🧾 Catat penjualan, stok otomatis berkurang, omzet harian dan mingguan langsung terlihat
- 🤖 Tanya AI: "barang apa yang harus dibeli minggu ini?", "bagaimana penjualan 7 hari terakhir?", "buatkan caption promosi lovebird"

**Pengaman**
- AI tidak boleh mengarang harga atau stok: semua jawaban diambil dari data toko lewat function calling
- Menolak permintaan jual-beli satwa yang dilindungi undang-undang
- Menyarankan dokter hewan untuk burung yang sakit parah

---

## 🏗️ Cara Kerja

```
Pembeli / pemilik mengetik pertanyaan
              │
              ▼
app.py  ── Streamlit (chat, katalog, kelola stok, catat penjualan)
              │
              ▼
assistant.py ── Gemini + system prompt (mode pelanggan / pemilik)
              │   Gemini memutuskan sendiri alat mana yang dipanggil
              ▼
store_tools.py ── alat-alat toko:
   cari_produk · cek_stok · hitung_pesanan · info_toko · panduan_perawatan
   (khusus pemilik) daftar_stok_menipis · ringkasan_penjualan
              │
              ▼
data/ ── produk.csv · info_toko.json · panduan_perawatan.md · penjualan.csv
```

Setiap jawaban di chat punya tombol **"Data yang dicek asisten"** yang menunjukkan alat apa saja yang dipakai AI, jadi jawabannya bisa dicek kebenarannya.

---

## 🗂️ Struktur Folder

```
toko-burung-ai/
├── app.py                    # Tampilan Streamlit
├── assistant.py              # Koneksi ke Gemini + prompt
├── store_tools.py            # Data toko & alat yang dipanggil AI
├── data/
│   ├── produk.csv            # Katalog: harga, stok, stok minimum (bisa dibuka di Excel)
│   ├── info_toko.json        # Alamat, jam buka, WhatsApp, pembayaran, garansi
│   ├── panduan_perawatan.md  # Tips perawatan per jenis burung
│   └── penjualan.csv         # Dibuat otomatis saat mencatat penjualan
├── tests/test_store_tools.py
├── .streamlit/secrets.toml.example
└── requirements.txt
```

---

## 🚀 Cara Menjalankan

### 1. Install

```bash
cd toko-burung-ai
```

```bash
pip install -r requirements.txt
```

### 2. Ambil API key Gemini (gratis)

Buka [aistudio.google.com](https://aistudio.google.com) → **Get API key**.

### 3. (Opsional) Simpan API key dan PIN pemilik

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Isi `GEMINI_API_KEY` dan `PIN_PEMILIK` di file itu. Kalau dilewati, API key bisa diketik di menu samping, dan menu pemilik terbuka tanpa PIN.

### 4. Jalankan

```bash
streamlit run app.py
```

Buka [http://localhost:8501](http://localhost:8501).

---

## ✏️ Menyesuaikan dengan Toko Sendiri

Data yang ada sekarang adalah **contoh**. Ganti dengan data toko asli:

| File | Isi yang perlu diganti |
|---|---|
| `data/info_toko.json` | Nama toko, alamat, nomor WhatsApp (format `628...`), jam buka, pembayaran, aturan pengiriman & garansi |
| `data/produk.csv` | Daftar produk, harga, stok, stok minimum. Bisa diedit di Excel atau lewat tab **Kelola Stok** |
| `data/panduan_perawatan.md` | Tips perawatan. Tambah bagian baru dengan judul `## Nama Burung` |

Tidak perlu mengubah kode: AI langsung memakai data terbaru.

Model Gemini bawaan adalah `gemini-flash-latest`. Bisa diganti di menu samping atau lewat environment variable `GEMINI_MODEL`.

---

## 💡 Contoh Pertanyaan

**Pembeli**
- "Ada lovebird apa saja dan harganya berapa?"
- "Saya pemula, burung apa yang mudah dirawat untuk anak SD?"
- "Murai batu saya bulunya rontok, kenapa ya?"
- "Mau pesan 1 kenari lokal jantan dan 2 biji kenari, totalnya berapa?"
- "Toko buka jam berapa hari Minggu?"

**Pemilik**
- "Barang apa yang harus dibeli ulang?"
- "Bagaimana penjualan 30 hari terakhir?"
- "Buatkan caption WhatsApp untuk promo parkit, bahasa santai."

---

## 🧪 Tes

```bash
python -m pytest -q tests
```

---

## 🌐 Online-kan Gratis (Opsional)

Upload ke GitHub, lalu deploy di [Streamlit Community Cloud](https://streamlit.io/cloud). Isi `GEMINI_API_KEY` dan `PIN_PEMILIK` di menu **Secrets** aplikasi.

Catatan: di Streamlit Cloud, perubahan stok dan penjualan yang disimpan ke file CSV bisa hilang ketika aplikasi di-restart. Untuk pemakaian sehari-hari yang serius, simpan data di Google Sheets atau database.
