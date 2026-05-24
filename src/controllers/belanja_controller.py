# controllers/belanja_controller.py
# Logika bisnis untuk halaman Daftar Belanja
# Menjembatani views/daftar_belanja_page.py dengan model-model di bawah

import sqlite3
from datetime import date

from models.budget_model import ambil_budget_per_bulan, PERIODE_AKTIF
from models.barang_model import ambil_barang_persis, tambah_barang, ambil_barang_by_nama
from models.satuan_model import ambil_semua_satuan
from models.kategori_model import ambil_semua_kategori
from models.detail_belanja_model import (
    tambah_item_belanja,
    ubah_item_belanja,
    hapus_item_belanja,
    cari_item_belanja,
    hitung_total_pengeluaran,
    ambil_item_by_id,
)


class BelanjaController:
    """
    Controller tunggal untuk seluruh operasi di halaman Daftar Belanja.
    View hanya memanggil metode ini — tidak boleh akses model langsung.
    """

    def __init__(self, koneksi: sqlite3.Connection):
        self._koneksi = koneksi

    # ─── DATA PERIODE ─────────────────────────────────────────────────────────

    def ambil_periode_per_bulan(self, bulan: int, tahun: int) -> list:
        """
        Ambil semua periode budget pada bulan dan tahun tertentu.
        Digunakan State A untuk menampilkan tombol minggu yang tersedia.
        """
        return ambil_budget_per_bulan(self._koneksi, bulan, tahun)

    def ambil_periode_by_minggu(self, minggu_ke: int, bulan: int, tahun: int):
        """
        Ambil satu periode berdasarkan minggu/bulan/tahun.
        Kembalikan None jika belum ada budget untuk periode itu.
        """
        hasil = self._koneksi.execute(
            """
            SELECT * FROM tb_periode_budget
            WHERE minggu_ke = ? AND bulan = ? AND tahun = ?
            """,
            (minggu_ke, bulan, tahun)
        ).fetchone()
        return hasil

    # ─── AUTOCOMPLETE & SATUAN/KATEGORI ──────────────────────────────────────

    def cari_nama_barang(self, kata_kunci: str) -> list:
        """
        Cari barang dari master data untuk fitur autocomplete.
        Kembalikan list row dengan nama_barang dan id_kategori.
        """
        if not kata_kunci.strip():
            return []
        return ambil_barang_by_nama(self._koneksi, kata_kunci)

    def ambil_barang_persis(self, nama_barang: str):
        """
        Cek apakah barang dengan nama ini sudah ada di master data.
        Digunakan untuk auto-fill kategori jika barang dikenali.
        """
        return ambil_barang_persis(self._koneksi, nama_barang)

    def ambil_daftar_satuan(self) -> list:
        """Ambil semua satuan dari tb_satuan untuk isi dropdown."""
        return ambil_semua_satuan(self._koneksi)

    def ambil_daftar_kategori(self) -> list:
        """Ambil semua kategori dari tb_kategori untuk isi dropdown."""
        return ambil_semua_kategori(self._koneksi)

    # ─── OPERASI ITEM ─────────────────────────────────────────────────────────

    def tambah_item(
        self,
        id_periode: int,
        nama_barang: str,
        id_kategori: int,
        id_satuan: int,
        jumlah: float,
        harga_satuan: float,
    ) -> dict:
        """
        Simpan item belanja baru setelah validasi.
        Jika nama barang belum ada di master, otomatis ditambahkan.
        Kembalikan dict {'berhasil': bool, 'pesan': str}.
        """
        # Validasi semua field wajib terisi
        nama = nama_barang.strip()
        if not nama:
            return {"berhasil": False, "pesan": "Nama barang wajib diisi."}
        if id_kategori <= 0:
            return {"berhasil": False, "pesan": "Kategori wajib dipilih."}
        if id_satuan <= 0:
            return {"berhasil": False, "pesan": "Satuan wajib dipilih."}
        if jumlah <= 0:
            return {"berhasil": False, "pesan": "Jumlah harus lebih dari 0."}
        if harga_satuan < 0:
            return {"berhasil": False, "pesan": "Harga tidak boleh negatif."}

        # Cek apakah barang sudah ada di master data — jika belum, tambahkan
        barang = ambil_barang_persis(self._koneksi, nama)
        if barang:
            # Barang sudah ada — gunakan id yang ada, abaikan kategori dari form
            id_barang = barang["id_barang"]
        else:
            # Barang baru — tambahkan ke master data dengan kategori yang dipilih
            id_barang = tambah_barang(self._koneksi, nama, id_kategori)

        if id_barang is None:
            return {"berhasil": False, "pesan": "Gagal menyimpan data barang."}

        # Simpan item ke tabel detail belanja
        tambah_item_belanja(
            self._koneksi, id_periode, id_barang, id_satuan, jumlah, harga_satuan
        )
        return {"berhasil": True, "pesan": "Item berhasil ditambahkan."}

    def ubah_item(
        self,
        id_detail: int,
        nama_barang: str,
        id_kategori: int,
        id_satuan: int,
        jumlah: float,
        harga_satuan: float,
    ) -> dict:
        """
        Perbarui item belanja yang sudah ada setelah validasi.
        Kembalikan dict {'berhasil': bool, 'pesan': str}.
        """
        nama = nama_barang.strip()
        if not nama:
            return {"berhasil": False, "pesan": "Nama barang wajib diisi."}
        if id_kategori <= 0:
            return {"berhasil": False, "pesan": "Kategori wajib dipilih."}
        if id_satuan <= 0:
            return {"berhasil": False, "pesan": "Satuan wajib dipilih."}
        if jumlah <= 0:
            return {"berhasil": False, "pesan": "Jumlah harus lebih dari 0."}
        if harga_satuan < 0:
            return {"berhasil": False, "pesan": "Harga tidak boleh negatif."}

        # Pastikan barang ada di master data
        barang = ambil_barang_persis(self._koneksi, nama)
        if barang:
            id_barang = barang["id_barang"]
        else:
            id_barang = tambah_barang(self._koneksi, nama, id_kategori)

        if id_barang is None:
            return {"berhasil": False, "pesan": "Gagal menyimpan data barang."}

        ubah_item_belanja(self._koneksi, id_detail, id_barang, id_satuan, jumlah, harga_satuan)
        return {"berhasil": True, "pesan": "Item berhasil diperbarui."}

    def hapus_item(self, id_detail: int) -> None:
        """Hapus satu item belanja dari database."""
        hapus_item_belanja(self._koneksi, id_detail)

    def ambil_item_by_id(self, id_detail: int):
        """Ambil satu item lengkap untuk mengisi form edit."""
        return ambil_item_by_id(self._koneksi, id_detail)

    # ─── QUERY TABEL ──────────────────────────────────────────────────────────

    def ambil_daftar_item(
        self, id_periode: int, kata_kunci: str = "", id_kategori: int = 0
    ) -> list:
        """
        Ambil daftar item dengan filter opsional.
        Dipanggil setiap kali tabel perlu di-render ulang.
        """
        return cari_item_belanja(self._koneksi, id_periode, kata_kunci, id_kategori)

    def hitung_total(self, id_periode: int) -> float:
        """Hitung total pengeluaran untuk footer tabel."""
        return hitung_total_pengeluaran(self._koneksi, id_periode)