# src/controllers/master_data_controller.py
"""
Controller untuk manajemen master data (Satuan & Kategori).
Menghubungkan view dengan model, menangani validasi dan proteksi hapus.
"""

import sqlite3
from typing import Optional, List, Tuple
from models.satuan_model import (
    ambil_semua_satuan,
    tambah_satuan,
    ubah_satuan,
    hapus_satuan,
    cek_satuan_digunakan
)
from models.kategori_model import (
    ambil_semua_kategori,
    tambah_kategori,
    ubah_kategori,
    hapus_kategori,
    cek_kategori_digunakan
)


class MasterDataController:
    """
    Controller untuk halaman Pengaturan.
    Menangani CRUD satuan dan kategori dengan proteksi hapus.
    """

    def __init__(self, koneksi: sqlite3.Connection):
        self.koneksi = koneksi

    # ========== SATUAN ==========

    def muat_semua_satuan(self) -> List[Tuple[int, str]]:
        """Ambil seluruh data satuan dari database untuk ditampilkan di list."""
        return ambil_semua_satuan(self.koneksi)

    def simpan_satuan_baru(self, nama_satuan: str) -> Tuple[bool, str]:
        """
        Tambah satuan baru ke database.

        Returns:
            (success: bool, message: str)
        """
        # Validasi input kosong
        if not nama_satuan or nama_satuan.strip() == "":
            return False, "Nama satuan tidak boleh kosong."

        # Cek duplikasi akan ditangani oleh constraint UNIQUE di database
        # Jika duplikasi, SQLite akan raise IntegrityError
        try:
            tambah_satuan(self.koneksi, nama_satuan.strip())
            return True, f"Satuan '{nama_satuan}' berhasil ditambahkan."
        except sqlite3.IntegrityError:
            return False, f"Satuan '{nama_satuan}' sudah ada."

    def perbarui_satuan(self, id_satuan: int, nama_baru: str) -> Tuple[bool, str]:
        """
        Edit nama satuan yang sudah ada.

        Returns:
            (success: bool, message: str)
        """
        # Validasi input kosong
        if not nama_baru or nama_baru.strip() == "":
            return False, "Nama satuan tidak boleh kosong."

        try:
            ubah_satuan(self.koneksi, id_satuan, nama_baru.strip())
            return True, f"Satuan berhasil diperbarui menjadi '{nama_baru}'."
        except sqlite3.IntegrityError:
            return False, f"Satuan '{nama_baru}' sudah ada."

    def hapus_satuan_dengan_proteksi(self, id_satuan: int, nama_satuan: str) -> Tuple[bool, str]:
        """
        Hapus satuan dengan proteksi: cek apakah satuan sedang digunakan.

        Returns:
            (success: bool, message: str)
        """
        # Cek apakah satuan sedang digunakan di tb_detail_belanja
        if cek_satuan_digunakan(self.koneksi, id_satuan):
            return False, f"Satuan '{nama_satuan}' sedang digunakan dan tidak dapat dihapus."

        # Hapus satuan jika tidak digunakan
        hapus_satuan(self.koneksi, id_satuan)
        return True, f"Satuan '{nama_satuan}' berhasil dihapus."

    # ========== KATEGORI ==========

    def muat_semua_kategori(self) -> List[Tuple[int, str]]:
        """Ambil seluruh data kategori dari database untuk ditampilkan di list."""
        return ambil_semua_kategori(self.koneksi)

    def simpan_kategori_baru(self, nama_kategori: str) -> Tuple[bool, str]:
        """
        Tambah kategori baru ke database.

        Returns:
            (success: bool, message: str)
        """
        # Validasi input kosong
        if not nama_kategori or nama_kategori.strip() == "":
            return False, "Nama kategori tidak boleh kosong."

        try:
            tambah_kategori(self.koneksi, nama_kategori.strip())
            return True, f"Kategori '{nama_kategori}' berhasil ditambahkan."
        except sqlite3.IntegrityError:
            return False, f"Kategori '{nama_kategori}' sudah ada."

    def perbarui_kategori(self, id_kategori: int, nama_baru: str) -> Tuple[bool, str]:
        """
        Edit nama kategori yang sudah ada.

        Returns:
            (success: bool, message: str)
        """
        # Validasi input kosong
        if not nama_baru or nama_baru.strip() == "":
            return False, "Nama kategori tidak boleh kosong."

        try:
            ubah_kategori(self.koneksi, id_kategori, nama_baru.strip())
            return True, f"Kategori berhasil diperbarui menjadi '{nama_baru}'."
        except sqlite3.IntegrityError:
            return False, f"Kategori '{nama_baru}' sudah ada."

    def hapus_kategori_dengan_proteksi(self, id_kategori: int, nama_kategori: str) -> Tuple[bool, str]:
        """
        Hapus kategori dengan proteksi: cek apakah kategori sedang digunakan.

        Returns:
            (success: bool, message: str)
        """
        # Cek apakah kategori sedang digunakan di tb_barang
        if cek_kategori_digunakan(self.koneksi, id_kategori):
            return False, f"Kategori '{nama_kategori}' sedang digunakan dan tidak dapat dihapus."

        # Hapus kategori jika tidak digunakan
        hapus_kategori(self.koneksi, id_kategori)
        return True, f"Kategori '{nama_kategori}' berhasil dihapus."