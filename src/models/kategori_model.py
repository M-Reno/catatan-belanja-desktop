# models/kategori_model.py
# Seluruh akses database untuk tabel tb_kategori
# Digunakan oleh: master_data_controller.py, belanja_controller.py, riwayat_controller.py

import sqlite3


def ambil_semua_kategori(koneksi: sqlite3.Connection) -> list:
    """Ambil seluruh kategori diurutkan alfabetis."""
    return koneksi.execute(
        "SELECT id_kategori, nama_kategori FROM tb_kategori ORDER BY nama_kategori ASC"
    ).fetchall()


def tambah_kategori(koneksi: sqlite3.Connection, nama_kategori: str) -> bool:
    """
    Simpan kategori baru ke database.
    Kembalikan True jika berhasil, False jika nama sudah ada (duplikasi).
    """
    try:
        koneksi.execute(
            "INSERT INTO tb_kategori (nama_kategori) VALUES (?)",
            (nama_kategori.strip(),)
        )
        koneksi.commit()
        return True
    except sqlite3.IntegrityError:
        # Nama kategori sudah ada — UNIQUE constraint dilanggar
        return False


def ubah_kategori(koneksi: sqlite3.Connection, id_kategori: int, nama_baru: str) -> bool:
    """
    Perbarui nama kategori berdasarkan id.
    Kembalikan True jika berhasil, False jika nama baru sudah dipakai kategori lain.
    """
    try:
        koneksi.execute(
            "UPDATE tb_kategori SET nama_kategori = ? WHERE id_kategori = ?",
            (nama_baru.strip(), id_kategori)
        )
        koneksi.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def hapus_kategori(koneksi: sqlite3.Connection, id_kategori: int) -> None:
    """Hapus kategori — pastikan sudah cek cek_kategori_digunakan() sebelum memanggil ini."""
    koneksi.execute(
        "DELETE FROM tb_kategori WHERE id_kategori = ?",
        (id_kategori,)
    )
    koneksi.commit()


def cek_kategori_digunakan(koneksi: sqlite3.Connection, id_kategori: int) -> bool:
    """
    Cek apakah kategori masih dipakai oleh minimal satu barang di tb_barang.
    Kembalikan True jika masih digunakan (tidak boleh dihapus).
    """
    hasil = koneksi.execute(
        "SELECT COUNT(*) as jumlah FROM tb_barang WHERE id_kategori = ?",
        (id_kategori,)
    ).fetchone()
    return hasil["jumlah"] > 0
