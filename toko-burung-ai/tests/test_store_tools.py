import shutil
from pathlib import Path
from urllib.parse import unquote

import pytest

from store_tools import Toko, buat_tools, format_rupiah

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def toko(tmp_path):
    for f in ("produk.csv", "info_toko.json", "panduan_perawatan.md"):
        shutil.copy(DATA / f, tmp_path / f)
    return Toko(tmp_path)


def alat(toko, mode="pelanggan"):
    return {f.__name__: f for f in buat_tools(toko, mode)}


def test_format_rupiah():
    assert format_rupiah(350000) == "Rp350.000"
    assert format_rupiah(0) == "Rp0"


def test_cari_lovebird(toko):
    hasil = alat(toko)["cari_produk"]("lovebird")
    ids = [p["id"] for p in hasil["produk"]]
    assert set(ids[:2]) == {"B01", "B02"}
    assert all("stok_minimum" not in p for p in hasil["produk"])


def test_sinonim_dan_harga_maks(toko):
    hasil = alat(toko)["cari_produk"]("kandang", harga_maks=100000)
    ids = [p["id"] for p in hasil["produk"]]
    assert ids[:2] == ["K01", "K05"]
    assert "K02" not in ids  # Rp150.000, di atas batas
    assert alat(toko)["cari_produk"]("cockatiel")["produk"][0]["id"] == "B06"


def test_filter_kategori(toko):
    hasil = alat(toko)["cari_produk"](kategori="Pakan")
    assert hasil["jumlah_hasil"] > 0
    assert {p["kategori"] for p in hasil["produk"]} == {"Pakan"}


def test_cek_stok(toko):
    cek = alat(toko)["cek_stok"]
    assert cek("b01")["nama"] == "Lovebird Biola"
    assert cek("kenari lokal")["id"] == "B03"
    assert cek("jerapah")["ditemukan"] is False


def test_hitung_pesanan(toko):
    hasil = alat(toko)["hitung_pesanan"](["B03", "P02", "ZZZ"], [1, 2, 1])
    assert hasil["total"] == "Rp540.000"
    assert any("ZZZ" in p for p in hasil["peringatan"])
    assert hasil["link_whatsapp"].startswith("https://wa.me/6281234567890?text=")
    assert "Total: Rp540.000" in unquote(hasil["link_whatsapp"])


def test_hitung_pesanan_stok_kurang(toko):
    hasil = alat(toko)["hitung_pesanan"](["B07"], [3])
    assert any("Stok" in p for p in hasil["peringatan"])


def test_panduan(toko):
    p = alat(toko)["panduan_perawatan"]
    assert p("murai batu")["topik"] == "Murai Batu"
    assert p("cockatiel")["topik"] == "Falk"
    assert p("burung saya sakit")["topik"] == "Tanda Burung Sakit"
    assert p("xyz")["ditemukan"] is False


def test_tools_pemilik(toko):
    assert "daftar_stok_menipis" not in alat(toko)
    a = alat(toko, "pemilik")
    menipis = a["daftar_stok_menipis"]()
    ids = {p["id"] for p in menipis["produk"]}
    assert {"P03", "P09"} <= ids
    assert "B05" not in ids


def test_catat_penjualan(toko):
    stok_awal = int(toko.produk().set_index("id").at["P01", "stok"])
    t = toko.catat_penjualan("P01", 3)
    assert t["total"] == 75000
    assert int(toko.produk().set_index("id").at["P01", "stok"]) == stok_awal - 3
    toko.catat_penjualan("B05", 2)
    r = alat(toko, "pemilik")["ringkasan_penjualan"](7)
    assert r["jumlah_transaksi"] == 2
    assert r["total_omzet"] == "Rp195.000"
    assert r["produk_terlaris"][0]["nama"] == "Parkit (Budgie)"


def test_catat_penjualan_stok_tidak_cukup(toko):
    with pytest.raises(ValueError):
        toko.catat_penjualan("B07", 5)
    with pytest.raises(ValueError):
        toko.catat_penjualan("TIDAKADA", 1)


def test_simpan_produk_validasi(toko):
    df = toko.produk()
    df.loc[1, "id"] = df.loc[0, "id"]
    with pytest.raises(ValueError):
        toko.simpan_produk(df)


def test_info_tanpa_catatan_pemilik(toko):
    assert "catatan_pemilik" not in alat(toko)["info_toko"]()
