# models/barang_model.py
# Seluruh akses database untuk tabel tb_barang
# Digunakan oleh: belanja_controller.py untuk autocomplete dan auto-insert barang baru

import sqlite3


def ambil_barang_by_nama(koneksi: sqlite3.Connection, nama_barang: str) -> list:
    """
    Cari barang berdasarkan nama menggunakan LIKE untuk fitur autocomplete.
    Kembalikan daftar barang yang namanya mengandung kata pencarian.
    """
    pola = f"%{nama_barang}%"
    return koneksi.execute(
        """
        SELECT b.id_barang, b.nama_barang, b.id_kategori, k.nama_kategori
        FROM tb_barang b
        LEFT JOIN tb_kategori k ON k.id_kategori = b.id_kategori
        WHERE b.nama_barang LIKE ?
        ORDER BY b.nama_barang ASC
        """,
        (pola,)
    ).fetchall()


def ambil_barang_persis(koneksi: sqlite3.Connection, nama_barang: str) -> sqlite3.Row | None:
    """
    Cari barang dengan nama yang persis sama (case-insensitive).
    Digunakan untuk mengecek apakah barang sudah ada sebelum tambah baru.
    Kembalikan satu baris atau None jika tidak ditemukan.
    """
    return koneksi.execute(
        """
        SELECT b.id_barang, b.nama_barang, b.id_kategori, k.nama_kategori
        FROM tb_barang b
        LEFT JOIN tb_kategori k ON k.id_kategori = b.id_kategori
        WHERE LOWER(b.nama_barang) = LOWER(?)
        LIMIT 1
        """,
        (nama_barang.strip(),)
    ).fetchone()


def tambah_barang(koneksi: sqlite3.Connection, nama_barang: str, id_kategori: int) -> int | None:
    """
    Tambah barang baru ke master data tb_barang.
    Gunakan INSERT OR IGNORE untuk menghindari error jika sudah ada.
    Kembalikan id_barang (baik yang baru dibuat maupun yang sudah ada).
    """
    koneksi.execute(
        "INSERT OR IGNORE INTO tb_barang (nama_barang, id_kategori) VALUES (?, ?)",
        (nama_barang.strip(), id_kategori)
    )
    koneksi.commit()

    # Ambil id_barang setelah insert (bisa yang baru atau yang sudah ada)
    hasil = koneksi.execute(
        "SELECT id_barang FROM tb_barang WHERE LOWER(nama_barang) = LOWER(?) LIMIT 1",
        (nama_barang.strip(),)
    ).fetchone()

    return hasil["id_barang"] if hasil else None


def ambil_id_barang(koneksi: sqlite3.Connection, nama_barang: str, id_kategori: int) -> int | None:
    """
    Ambil id_barang berdasarkan kombinasi nama dan kategori.
    Kembalikan id atau None jika tidak ditemukan.
    """
    hasil = koneksi.execute(
        "SELECT id_barang FROM tb_barang WHERE LOWER(nama_barang) = LOWER(?) AND id_kategori = ?",
        (nama_barang.strip(), id_kategori)
    ).fetchone()
    return hasil["id_barang"] if hasil else None