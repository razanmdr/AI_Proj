"""Data toko (produk, stok, penjualan, info, panduan) dan "alat" yang bisa dipanggil AI.

Semua data disimpan di folder data/ sebagai file biasa (CSV, JSON, Markdown)
supaya bisa diubah langsung lewat Excel / Notepad tanpa perlu database.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

KOLOM_PRODUK = ["id", "nama", "kategori", "harga", "stok", "stok_minimum", "satuan", "deskripsi"]
KOLOM_PENJUALAN = ["waktu", "id", "nama", "jumlah", "harga", "total"]

# Kata yang sering dipakai pembeli -> kata yang ada di katalog
SINONIM = {
    "makanan": "pakan",
    "makan": "pakan",
    "pelet": "voer",
    "pur": "voer",
    "kandang": "sangkar",
    "cockatiel": "falk",
    "parakeet": "parkit",
    "budgie": "parkit",
    "lb": "lovebird",
}

KATA_UMUM = {
    "ada", "apa", "apakah", "berapa", "harga", "harganya", "yang", "untuk", "buat", "dan", "atau",
    "di", "ke", "dari", "ini", "itu", "saya", "aku", "mau", "ingin", "cari", "beli", "jual",
    "toko", "punya", "masih", "stok", "tersedia", "dong", "kak", "pak", "bu", "min", "ya",
    "burung", "the", "a",
}


def format_rupiah(angka: float | int) -> str:
    """350000 -> 'Rp350.000'."""
    return "Rp" + f"{int(round(angka)):,}".replace(",", ".")


def _token(teks: str) -> list[str]:
    kata = re.findall(r"[a-z0-9]+", teks.lower())
    return [SINONIM.get(k, k) for k in kata if k not in KATA_UMUM]


class Toko:
    """Akses ke semua data toko di folder data/."""

    def __init__(self, data_dir: Path | str = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.file_produk = self.data_dir / "produk.csv"
        self.file_info = self.data_dir / "info_toko.json"
        self.file_panduan = self.data_dir / "panduan_perawatan.md"
        self.file_penjualan = self.data_dir / "penjualan.csv"

    # ── Produk & stok ────────────────────────────────────────────────────────
    def produk(self) -> pd.DataFrame:
        df = pd.read_csv(self.file_produk, dtype={"id": str})
        df["harga"] = pd.to_numeric(df["harga"], errors="coerce").fillna(0).astype(int)
        df["stok"] = pd.to_numeric(df["stok"], errors="coerce").fillna(0).astype(int)
        df["stok_minimum"] = pd.to_numeric(df["stok_minimum"], errors="coerce").fillna(0).astype(int)
        df["deskripsi"] = df["deskripsi"].fillna("")
        return df[KOLOM_PRODUK]

    def simpan_produk(self, df: pd.DataFrame) -> None:
        df = df[KOLOM_PRODUK].copy()
        df = df.dropna(subset=["id", "nama"])
        df["id"] = df["id"].astype(str).str.strip().str.upper()
        if df["id"].duplicated().any():
            dobel = ", ".join(sorted(df.loc[df["id"].duplicated(), "id"].unique()))
            raise ValueError(f"ID produk tidak boleh sama: {dobel}")
        for kolom in ("harga", "stok", "stok_minimum"):
            df[kolom] = pd.to_numeric(df[kolom], errors="coerce").fillna(0).astype(int)
            if (df[kolom] < 0).any():
                raise ValueError(f"Kolom '{kolom}' tidak boleh bernilai minus.")
        df.to_csv(self.file_produk, index=False)

    def kategori(self) -> list[str]:
        return sorted(self.produk()["kategori"].unique().tolist())

    def cari(self, kata_kunci: str = "", kategori: str = "", harga_maks: int = 0, batas: int = 10) -> pd.DataFrame:
        df = self.produk()
        if kategori:
            kat = kategori.lower()
            df = df[df["kategori"].str.lower().str.contains(re.escape(kat))]
        if harga_maks and harga_maks > 0:
            df = df[df["harga"] <= harga_maks]

        token = _token(kata_kunci)
        if token:
            teks = (df["nama"] + " " + df["kategori"] + " " + df["deskripsi"]).str.lower()
            nama = df["nama"].str.lower()
            # Cocok di awal nama paling penting, lalu di nama, lalu di kategori/deskripsi
            skor = sum(
                3 * nama.str.startswith(t).astype(int)
                + 2 * nama.str.contains(re.escape(t)).astype(int)
                + teks.str.contains(re.escape(t)).astype(int)
                for t in token
            )
            # Produk yang cocok dengan lebih banyak kata pencarian didahulukan
            cakupan = sum(teks.str.contains(re.escape(t)).astype(int) for t in token)
            df = df.assign(_cakupan=cakupan, _skor=skor)
            df = df[df["_skor"] > 0].sort_values(["_cakupan", "_skor", "harga"], ascending=[False, False, True])
            df = df.drop(columns=["_cakupan", "_skor"])
        return df.head(batas)

    def temukan(self, nama_atau_id: str) -> pd.Series | None:
        df = self.produk()
        kunci = nama_atau_id.strip()
        cocok_id = df[df["id"].str.upper() == kunci.upper()]
        if not cocok_id.empty:
            return cocok_id.iloc[0]
        hasil = self.cari(kunci, batas=1)
        return None if hasil.empty else hasil.iloc[0]

    def stok_menipis(self) -> pd.DataFrame:
        df = self.produk()
        return df[df["stok"] <= df["stok_minimum"]].sort_values("stok")

    # ── Penjualan ────────────────────────────────────────────────────────────
    def penjualan(self) -> pd.DataFrame:
        if not self.file_penjualan.exists():
            return pd.DataFrame(columns=KOLOM_PENJUALAN)
        df = pd.read_csv(self.file_penjualan, dtype={"id": str})
        df["waktu"] = pd.to_datetime(df["waktu"])
        return df

    def catat_penjualan(self, id_produk: str, jumlah: int, waktu: datetime | None = None) -> dict:
        """Kurangi stok dan simpan transaksi ke data/penjualan.csv."""
        if jumlah <= 0:
            raise ValueError("Jumlah harus lebih dari 0.")
        df = self.produk()
        baris = df.index[df["id"] == id_produk]
        if len(baris) == 0:
            raise ValueError(f"Produk dengan ID {id_produk} tidak ditemukan.")
        i = baris[0]
        if df.at[i, "stok"] < jumlah:
            raise ValueError(f"Stok {df.at[i, 'nama']} hanya {df.at[i, 'stok']}, tidak cukup untuk {jumlah}.")

        df.at[i, "stok"] -= jumlah
        self.simpan_produk(df)

        transaksi = {
            "waktu": (waktu or datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
            "id": id_produk,
            "nama": df.at[i, "nama"],
            "jumlah": int(jumlah),
            "harga": int(df.at[i, "harga"]),
            "total": int(df.at[i, "harga"] * jumlah),
        }
        pd.DataFrame([transaksi]).to_csv(
            self.file_penjualan, mode="a", header=not self.file_penjualan.exists(), index=False
        )
        return transaksi

    def ringkasan_penjualan(self, hari: int = 7) -> dict:
        df = self.penjualan()
        sejak = datetime.now() - timedelta(days=hari)
        df = df[df["waktu"] >= sejak] if not df.empty else df
        if df.empty:
            return {"periode_hari": hari, "jumlah_transaksi": 0, "total_omzet": format_rupiah(0), "produk_terlaris": []}
        terlaris = (
            df.groupby("nama", as_index=False)[["jumlah", "total"]].sum().sort_values("total", ascending=False).head(5)
        )
        return {
            "periode_hari": hari,
            "jumlah_transaksi": int(len(df)),
            "total_omzet": format_rupiah(df["total"].sum()),
            "produk_terlaris": [
                {"nama": r.nama, "terjual": int(r.jumlah), "omzet": format_rupiah(r.total)} for r in terlaris.itertuples()
            ],
        }

    # ── Info toko & panduan ──────────────────────────────────────────────────
    def info(self) -> dict:
        info = json.loads(self.file_info.read_text(encoding="utf-8"))
        info.pop("catatan_pemilik", None)
        return info

    def panduan(self) -> dict[str, str]:
        """Pecah panduan_perawatan.md per judul '## ...'."""
        teks = self.file_panduan.read_text(encoding="utf-8")
        bagian = {}
        for blok in re.split(r"^## ", teks, flags=re.M)[1:]:
            judul, _, isi = blok.partition("\n")
            bagian[judul.strip()] = isi.strip()
        return bagian


def _produk_ke_dict(baris: pd.Series, untuk_pemilik: bool = False) -> dict:
    data = {
        "id": baris["id"],
        "nama": baris["nama"],
        "kategori": baris["kategori"],
        "harga": format_rupiah(baris["harga"]),
        "satuan": baris["satuan"],
        "stok": int(baris["stok"]),
        "status": "Tersedia" if baris["stok"] > 0 else "Habis",
        "deskripsi": baris["deskripsi"],
    }
    if untuk_pemilik:
        data["stok_minimum"] = int(baris["stok_minimum"])
    return data


def buat_tools(toko: Toko, mode: str = "pelanggan") -> list:
    """Buat daftar fungsi yang bisa dipanggil Gemini.

    Docstring dan type hint tiap fungsi dibaca oleh Gemini sebagai petunjuk
    kapan dan bagaimana alat itu dipakai, jadi jangan dihapus.
    """
    pemilik = mode == "pemilik"

    def cari_produk(kata_kunci: str = "", kategori: str = "", harga_maks: int = 0) -> dict:
        """Cari produk di katalog toko (burung, pakan, sangkar, vitamin & obat, aksesoris).

        Args:
            kata_kunci: Kata pencarian, misalnya "lovebird", "pakan murai", "sangkar kenari". Kosongkan untuk melihat semua.
            kategori: Filter kategori: "Burung", "Pakan", "Kandang", "Vitamin & Obat", atau "Aksesoris". Kosongkan jika tidak perlu.
            harga_maks: Harga maksimal dalam rupiah (contoh 100000). Isi 0 jika tidak ada batas.
        """
        hasil = toko.cari(kata_kunci, kategori, harga_maks)
        return {
            "jumlah_hasil": len(hasil),
            "produk": [_produk_ke_dict(r, pemilik) for _, r in hasil.iterrows()],
            "kategori_tersedia": toko.kategori(),
        }

    def cek_stok(nama_atau_id: str) -> dict:
        """Cek harga dan stok satu produk berdasarkan nama atau ID (contoh "B01" atau "kenari lokal").

        Args:
            nama_atau_id: Nama produk atau ID produk.
        """
        baris = toko.temukan(nama_atau_id)
        if baris is None:
            return {"ditemukan": False, "pesan": f"Produk '{nama_atau_id}' tidak ada di katalog."}
        return {"ditemukan": True, **_produk_ke_dict(baris, pemilik)}

    def hitung_pesanan(id_produk: list[str], jumlah: list[int]) -> dict:
        """Hitung total harga pesanan dan buat link WhatsApp untuk konfirmasi ke toko.

        Args:
            id_produk: Daftar ID produk yang dipesan, contoh ["B01", "P01"]. Gunakan cari_produk dulu untuk mendapat ID.
            jumlah: Jumlah untuk tiap produk, urutannya sama dengan id_produk, contoh [1, 2].
        """
        if len(id_produk) != len(jumlah):
            return {"error": "Panjang id_produk dan jumlah harus sama."}
        df = toko.produk().set_index("id")
        rincian, peringatan, total = [], [], 0
        for pid, qty in zip(id_produk, jumlah):
            pid = str(pid).strip().upper()
            if pid not in df.index:
                peringatan.append(f"ID {pid} tidak ditemukan.")
                continue
            p = df.loc[pid]
            subtotal = int(p["harga"]) * int(qty)
            total += subtotal
            rincian.append({
                "id": pid, "nama": p["nama"], "jumlah": int(qty), "satuan": p["satuan"],
                "harga_satuan": format_rupiah(p["harga"]), "subtotal": format_rupiah(subtotal),
            })
            if p["stok"] < qty:
                peringatan.append(f"Stok {p['nama']} hanya {int(p['stok'])} {p['satuan']}.")

        info = toko.info()
        baris_pesan = [f"Halo {info.get('nama_toko', 'Toko')}, saya mau pesan:"]
        baris_pesan += [f"- {r['nama']} x{r['jumlah']} ({r['subtotal']})" for r in rincian]
        baris_pesan.append(f"Total: {format_rupiah(total)}")
        link = f"https://wa.me/{info.get('nomor_whatsapp', '')}?text=" + urllib.parse.quote("\n".join(baris_pesan))
        return {
            "rincian": rincian,
            "total": format_rupiah(total),
            "peringatan": peringatan,
            "link_whatsapp": link,
            "catatan": "Harga belum termasuk ongkir. Pesanan baru pasti setelah dikonfirmasi toko via WhatsApp.",
        }

    def info_toko() -> dict:
        """Informasi toko: alamat, jam buka, nomor WhatsApp, pembayaran, pengiriman, garansi, dan kebijakan."""
        return toko.info()

    def panduan_perawatan(topik: str) -> dict:
        """Ambil panduan perawatan burung dari catatan toko.

        Args:
            topik: Jenis burung (contoh "lovebird", "murai batu", "kenari") atau topik seperti "tanda burung sakit", "burung baru dibeli".
        """
        semua = toko.panduan()
        token = _token(topik)
        skor = {judul: sum(t in (judul + " " + isi).lower() for t in token) + 3 * sum(t in judul.lower() for t in token)
                for judul, isi in semua.items()}
        terbaik = max(skor, key=skor.get) if skor else None
        if not terbaik or skor[terbaik] == 0:
            return {"ditemukan": False, "topik_tersedia": list(semua)}
        return {"ditemukan": True, "topik": terbaik, "isi": semua[terbaik]}

    tools = [cari_produk, cek_stok, hitung_pesanan, info_toko, panduan_perawatan]

    if pemilik:
        def daftar_stok_menipis() -> dict:
            """Daftar produk yang stoknya sudah di bawah atau sama dengan stok minimum (perlu belanja/restok)."""
            df = toko.stok_menipis()
            return {"jumlah": len(df), "produk": [_produk_ke_dict(r, True) for _, r in df.iterrows()]}

        def ringkasan_penjualan(hari: int = 7) -> dict:
            """Ringkasan penjualan: jumlah transaksi, omzet, dan produk terlaris.

            Args:
                hari: Berapa hari ke belakang yang dihitung, contoh 1 untuk hari ini, 7 untuk seminggu, 30 untuk sebulan.
            """
            return toko.ringkasan_penjualan(hari)

        tools += [daftar_stok_menipis, ringkasan_penjualan]

    return tools
