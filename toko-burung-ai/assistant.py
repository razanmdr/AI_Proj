"""Otak asisten: menghubungkan Gemini dengan alat-alat toko (function calling)."""

from __future__ import annotations

import os

from google import genai
from google.genai import errors, types

from store_tools import Toko, buat_tools

MODEL_BAWAAN = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

ATURAN_UMUM = """
Aturan penting:
- Selalu jawab dalam Bahasa Indonesia yang ramah, sopan, dan mudah dipahami orang awam. Jawaban singkat (maksimal 5-6 kalimat) kecuali sedang menampilkan daftar.
- JANGAN pernah mengarang harga, stok, jam buka, atau nomor telepon. Selalu ambil dari alat (cari_produk, cek_stok, info_toko, dll).
- Tulis harga dalam format rupiah, contoh Rp350.000.
- Untuk pertanyaan perawatan burung, pakai alat panduan_perawatan dulu, lalu boleh ditambah pengetahuan umum yang aman. Jika burung tampak sakit parah, sarankan segera ke dokter hewan. Jangan memberi dosis obat manusia.
- Toko hanya menjual burung hasil penangkaran. Tolak dengan sopan permintaan membeli, menangkap, atau memperdagangkan satwa yang dilindungi undang-undang (misalnya jalak bali, cucak rawa, kakatua jambul kuning, nuri kepala hitam) dan jelaskan alasannya singkat.
- Jika sesuatu tidak ada di katalog, katakan terus terang dan tawarkan produk yang mirip.
- Tolak dengan halus pertanyaan yang tidak ada hubungannya dengan toko atau burung.
"""

PROMPT_PELANGGAN = """Kamu adalah "Si Kicau", asisten virtual {nama_toko}, sebuah toko burung keluarga.
Kamu melayani pembeli lewat chat: menjawab harga dan stok, merekomendasikan burung/pakan/sangkar yang cocok,
memberi tips perawatan, dan membantu menghitung pesanan.

Saat pembeli ingin memesan:
1. Pastikan produk dan jumlahnya jelas (pakai cari_produk untuk dapat ID).
2. Panggil hitung_pesanan, tampilkan rinciannya dan totalnya.
3. Berikan link WhatsApp dari hasil alat agar pembeli konfirmasi ke toko. Jelaskan bahwa pesanan baru pasti setelah dikonfirmasi pemilik toko.

Saat merekomendasikan untuk pemula, sarankan juga perlengkapan pendukungnya (pakan, sangkar, vitamin) yang ada di katalog.
""" + ATURAN_UMUM

PROMPT_PEMILIK = """Kamu adalah asisten pribadi pemilik {nama_toko}, sebuah toko burung keluarga.
Penggunamu adalah pemilik toko (orang tua), jadi jelaskan dengan bahasa sederhana dan langsung ke inti.
Kamu membantu: mengecek stok, melihat barang yang harus dibeli ulang (daftar_stok_menipis),
melihat ringkasan penjualan (ringkasan_penjualan), membuat draf balasan untuk pelanggan, dan membuat draf
caption promosi untuk WhatsApp/Instagram berdasarkan produk yang benar-benar ada di katalog.
Kamu tidak bisa mengubah stok atau harga; jika diminta, arahkan pemilik ke tab "Kelola Stok" atau "Catat Penjualan".
""" + ATURAN_UMUM


def _ke_konten_gemini(riwayat: list[dict]) -> list[types.Content]:
    return [
        types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part(text=m["content"])])
        for m in riwayat
    ]


def _ambil_panggilan_alat(respons) -> list[str]:
    """Catat alat apa saja yang dipakai Gemini, untuk ditampilkan di layar."""
    catatan = []
    for konten in respons.automatic_function_calling_history or []:
        for part in konten.parts or []:
            if part.function_call:
                argumen = ", ".join(f"{k}={v!r}" for k, v in (part.function_call.args or {}).items())
                catatan.append(f"{part.function_call.name}({argumen})")
    return catatan


def chat(
    pesan: str,
    riwayat: list[dict],
    api_key: str,
    toko: Toko | None = None,
    mode: str = "pelanggan",
    model: str = MODEL_BAWAAN,
) -> tuple[str, list[str]]:
    """Kirim pesan ke asisten.

    Args:
        pesan: Pesan terbaru dari pengguna.
        riwayat: Percakapan sebelumnya, format [{"role": "user"/"assistant", "content": "..."}].
        api_key: API key Gemini.
        toko: Objek data toko (bawaan: folder data/).
        mode: "pelanggan" atau "pemilik".
        model: Nama model Gemini.

    Returns:
        (jawaban, daftar alat yang dipanggil)
    """
    toko = toko or Toko()
    nama_toko = toko.info().get("nama_toko", "toko burung")
    prompt = (PROMPT_PEMILIK if mode == "pemilik" else PROMPT_PELANGGAN).format(nama_toko=nama_toko)

    client = genai.Client(api_key=api_key)
    sesi = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            tools=buat_tools(toko, mode),
            temperature=0.4,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=8),
        ),
        history=_ke_konten_gemini(riwayat),
    )

    try:
        respons = sesi.send_message(pesan)
    except errors.ClientError as e:
        if e.code in (401, 403) or "API key" in str(e):
            return "API key Gemini tidak valid. Periksa kembali API key di menu samping.", []
        if e.code == 404:
            return f"Model '{model}' tidak ditemukan. Coba ganti nama model di menu samping.", []
        if e.code == 429:
            return "Batas pemakaian gratis Gemini sedang penuh. Tunggu sebentar lalu coba lagi.", []
        return f"Maaf, terjadi kesalahan dari Gemini: {e.message}", []
    except errors.ServerError:
        return "Server Gemini sedang sibuk. Silakan coba lagi beberapa saat lagi.", []
    except Exception as e:  # misalnya internet putus
        return f"Maaf, tidak bisa terhubung ke Gemini ({type(e).__name__}). Periksa koneksi internet lalu coba lagi.", []

    jawaban = respons.text or "Maaf, saya belum bisa menjawab itu. Coba tanyakan dengan kalimat lain ya."
    return jawaban, _ambil_panggilan_alat(respons)
