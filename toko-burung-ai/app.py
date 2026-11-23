"""Aplikasi Streamlit: Asisten AI Toko Burung.

Jalankan dengan:  streamlit run app.py
"""

import os

import pandas as pd
import streamlit as st

from assistant import MODEL_BAWAAN, chat
from store_tools import Toko, format_rupiah

toko = Toko()
info = toko.info()
NAMA_TOKO = info.get("nama_toko", "Toko Burung")

st.set_page_config(page_title=f"Asisten AI {NAMA_TOKO}", page_icon="🐦", layout="wide")


def rahasia(nama: str) -> str:
    """Ambil nilai dari environment variable atau .streamlit/secrets.toml."""
    if os.getenv(nama):
        return os.getenv(nama, "")
    try:
        return st.secrets.get(nama, "")
    except Exception:
        return ""


# ── Menu samping ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title(f"🐦 {NAMA_TOKO}")
    st.caption(info.get("alamat", ""))

    mode_label = st.radio("Masuk sebagai", ["🛍️ Pelanggan", "🏠 Pemilik Toko"])
    mode = "pemilik" if "Pemilik" in mode_label else "pelanggan"

    if mode == "pemilik":
        pin_benar = rahasia("PIN_PEMILIK")
        if pin_benar:
            pin = st.text_input("PIN pemilik", type="password")
            if pin != pin_benar:
                st.warning("Masukkan PIN untuk membuka menu pemilik.")
                mode = "pelanggan"
        else:
            st.info("Tip: isi PIN_PEMILIK di secrets agar menu ini terkunci.")

    st.divider()
    api_key = rahasia("GEMINI_API_KEY") or st.text_input(
        "Gemini API key", type="password", help="Gratis dari aistudio.google.com → Get API key"
    )
    model = st.text_input("Model Gemini", value=MODEL_BAWAAN)

    if st.button("🗑️ Hapus percakapan"):
        st.session_state.pop(f"riwayat_{mode}", None)
        st.rerun()

    st.divider()
    st.markdown("**Jam buka**")
    for hari, jam in info.get("jam_buka", {}).items():
        st.caption(f"{hari}: {jam}")

kunci_riwayat = f"riwayat_{mode}"
st.session_state.setdefault(kunci_riwayat, [])
riwayat = st.session_state[kunci_riwayat]

# ── Tab ──────────────────────────────────────────────────────────────────────
nama_tab = ["💬 Tanya Asisten", "🛒 Katalog"]
if mode == "pemilik":
    nama_tab += ["📦 Kelola Stok", "🧾 Catat Penjualan"]
tabs = st.tabs(nama_tab)

CONTOH = {
    "pelanggan": [
        "Ada lovebird apa saja dan harganya berapa?",
        "Saya pemula, burung apa yang mudah dirawat untuk anak?",
        "Cara merawat murai batu bakalan gimana?",
        "Mau pesan 1 kenari lokal jantan dan 2 bungkus biji kenari, totalnya berapa?",
    ],
    "pemilik": [
        "Barang apa saja yang harus dibeli ulang minggu ini?",
        "Bagaimana penjualan 7 hari terakhir?",
        "Buatkan caption promosi WhatsApp untuk lovebird yang ready.",
        "Bantu balas pelanggan yang tanya apakah burung bisa dikirim ke luar kota.",
    ],
}

# ── Tab 1: Chat ──────────────────────────────────────────────────────────────
with tabs[0]:
    if mode == "pemilik":
        st.subheader("Asisten Pemilik Toko")
        st.caption("Tanyakan stok, barang yang perlu dibeli, penjualan, atau minta dibuatkan caption promosi.")
    else:
        st.subheader("Halo! Saya Si Kicau 🐦")
        st.caption("Tanya harga, stok, rekomendasi burung, atau cara merawat burung.")

    pertanyaan_contoh = None
    kolom = st.columns(len(CONTOH[mode]))
    for k, teks in zip(kolom, CONTOH[mode]):
        if k.button(teks, width="stretch"):
            pertanyaan_contoh = teks

    for m in riwayat:
        with st.chat_message(m["role"], avatar="🐦" if m["role"] == "assistant" else None):
            st.markdown(m["content"])
            if m.get("alat"):
                with st.expander("Data yang dicek asisten"):
                    for a in m["alat"]:
                        st.code(a, language=None)

    pesan = st.chat_input("Tulis pertanyaan di sini...") or pertanyaan_contoh
    if pesan:
        if not api_key:
            st.error("Masukkan Gemini API key di menu samping dulu ya.")
        else:
            with st.chat_message("user"):
                st.markdown(pesan)
            with st.chat_message("assistant", avatar="🐦"):
                with st.spinner("Sebentar, sedang mengecek..."):
                    jawaban, alat = chat(
                        pesan,
                        [{"role": m["role"], "content": m["content"]} for m in riwayat],
                        api_key=api_key,
                        toko=toko,
                        mode=mode,
                        model=model,
                    )
                st.markdown(jawaban)
            riwayat += [
                {"role": "user", "content": pesan},
                {"role": "assistant", "content": jawaban, "alat": alat},
            ]
            st.rerun()

# ── Tab 2: Katalog ───────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Katalog Produk")
    k1, k2 = st.columns([1, 2])
    pilih_kat = k1.selectbox("Kategori", ["Semua"] + toko.kategori())
    cari = k2.text_input("Cari produk", placeholder="contoh: kenari, sangkar, vitamin")

    df = toko.cari(cari, "" if pilih_kat == "Semua" else pilih_kat, batas=1000) if cari or pilih_kat != "Semua" else toko.produk()
    tampil = pd.DataFrame({
        "Produk": df["nama"],
        "Kategori": df["kategori"],
        "Harga": df["harga"].map(format_rupiah),
        "Stok": df.apply(lambda r: f"{r['stok']} {r['satuan']}" if r["stok"] > 0 else "Habis", axis=1),
        "Keterangan": df["deskripsi"],
    })
    st.dataframe(tampil, hide_index=True, width="stretch")
    st.caption(f"Pemesanan & konfirmasi: WhatsApp {info.get('nomor_whatsapp', '-')}")

# ── Tab 3 & 4: khusus pemilik ────────────────────────────────────────────────
if mode == "pemilik":
    with tabs[2]:
        st.subheader("Kelola Stok & Harga")
        menipis = toko.stok_menipis()
        if not menipis.empty:
            st.warning(
                "**Perlu restok:** "
                + ", ".join(f"{r.nama} (sisa {r.stok})" for r in menipis.itertuples())
            )
        else:
            st.success("Semua stok aman.")

        st.caption("Ubah angka langsung di tabel, tambah baris untuk produk baru, lalu klik Simpan.")
        diedit = st.data_editor(
            toko.produk(),
            num_rows="dynamic",
            width="stretch",
            hide_index=True,
            column_config={
                "id": st.column_config.TextColumn("ID", required=True, help="Contoh: B12, P10"),
                "nama": st.column_config.TextColumn("Nama", required=True),
                "kategori": st.column_config.SelectboxColumn(
                    "Kategori", options=["Burung", "Pakan", "Kandang", "Vitamin & Obat", "Aksesoris"], required=True
                ),
                "harga": st.column_config.NumberColumn("Harga (Rp)", min_value=0, step=1000, format="%d"),
                "stok": st.column_config.NumberColumn("Stok", min_value=0, step=1),
                "stok_minimum": st.column_config.NumberColumn("Stok minimum", min_value=0, step=1),
                "satuan": st.column_config.TextColumn("Satuan"),
                "deskripsi": st.column_config.TextColumn("Deskripsi", width="large"),
            },
        )
        if st.button("💾 Simpan perubahan", type="primary"):
            try:
                toko.simpan_produk(diedit)
                st.success("Tersimpan!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with tabs[3]:
        st.subheader("Catat Penjualan")
        produk = toko.produk()
        tersedia = produk[produk["stok"] > 0]
        if tersedia.empty:
            st.info("Semua produk sedang habis. Tambah stok dulu di tab Kelola Stok.")
        else:
            label = {
                r.id: f"{r.id} — {r.nama} ({format_rupiah(r.harga)}, stok {r.stok})" for r in tersedia.itertuples()
            }
            with st.form("form_penjualan", clear_on_submit=True):
                pilihan = st.selectbox("Produk", list(label), format_func=label.get)
                jumlah = st.number_input("Jumlah", min_value=1, value=1, step=1)
                if st.form_submit_button("Catat", type="primary"):
                    try:
                        t = toko.catat_penjualan(pilihan, int(jumlah))
                        st.session_state["pesan_jual"] = (
                            f"Tercatat: {t['nama']} x{t['jumlah']} = {format_rupiah(t['total'])}. Stok otomatis dikurangi."
                        )
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
        if "pesan_jual" in st.session_state:
            st.success(st.session_state.pop("pesan_jual"))

        r1, r2 = st.columns(2)
        hari_ini, minggu = toko.ringkasan_penjualan(1), toko.ringkasan_penjualan(7)
        r1.metric("Omzet hari ini", hari_ini["total_omzet"], f"{hari_ini['jumlah_transaksi']} transaksi", delta_color="off")
        r2.metric("Omzet 7 hari", minggu["total_omzet"], f"{minggu['jumlah_transaksi']} transaksi", delta_color="off")

        jual = toko.penjualan()
        if not jual.empty:
            st.markdown("**Transaksi terakhir**")
            jual = jual.sort_values("waktu", ascending=False).head(20)
            st.dataframe(
                pd.DataFrame({
                    "Waktu": jual["waktu"].dt.strftime("%d-%m-%Y %H:%M"),
                    "Produk": jual["nama"],
                    "Jumlah": jual["jumlah"],
                    "Total": jual["total"].map(format_rupiah),
                }),
                hide_index=True,
                width="stretch",
            )
