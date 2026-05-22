# models/satuan_model.py
# Seluruh akses database untuk tabel tb_satuan
# Digunakan oleh: master_data_controller.py, belanja_controller.py

import sqlite3


def ambil_semua_satuan(koneksi: sqlite3.Connection) -> list:
    """Ambil seluruh satuan diurutkan alfabetis."""
    return koneksi.execute(
        "SELECT id_satuan, nama_satuan FROM tb_satuan ORDER BY nama_satuan ASC"
    ).fetchall()


def tambah_satuan(koneksi: sqlite3.Connection, nama_satuan: str) -> bool:
    """
    Simpan satuan baru ke database.
    Kembalikan True jika berhasil, False jika nama sudah ada (duplikasi).
    """
    try:
        koneksi.execute(
            "INSERT INTO tb_satuan (nama_satuan) VALUES (?)",
            (nama_satuan.strip(),)
        )
        koneksi.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def ubah_satuan(koneksi: sqlite3.Connection, id_satuan: int, nama_baru: str) -> bool:
    """
    Perbarui nama satuan berdasarkan id.
    Kembalikan True jika berhasil, False jika nama baru sudah dipakai satuan lain.
    """
    try:
        koneksi.execute(
            "UPDATE tb_satuan SET nama_satuan = ? WHERE id_satuan = ?",
            (nama_baru.strip(), id_satuan)
        )
        koneksi.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def hapus_satuan(koneksi: sqlite3.Connection, id_satuan: int) -> None:
    """Hapus satuan — pastikan sudah cek cek_satuan_digunakan() sebelum memanggil ini."""
    koneksi.execute(
        "DELETE FROM tb_satuan WHERE id_satuan = ?",
        (id_satuan,)
    )
    koneksi.commit()


def cek_satuan_digunakan(koneksi: sqlite3.Connection, id_satuan: int) -> bool:
    """
    Cek apakah satuan masih dipakai oleh minimal satu item di tb_detail_belanja.
    Kembalikan True jika masih digunakan (tidak boleh dihapus).
    """
    hasil = koneksi.execute(
        "SELECT COUNT(*) as jumlah FROM tb_detail_belanja WHERE id_satuan = ?",
        (id_satuan,)
    ).fetchone()
    return hasil["jumlah"] > 0
