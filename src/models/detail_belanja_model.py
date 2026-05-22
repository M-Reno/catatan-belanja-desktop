# models/detail_belanja_model.py
# Seluruh akses database untuk tabel tb_detail_belanja
# Digunakan oleh: belanja_controller.py, riwayat_controller.py, export_controller.py,
#                 dashboard_controller.py

import sqlite3


def tambah_item_belanja(
    koneksi: sqlite3.Connection,
    id_periode: int,
    id_barang: int,
    id_satuan: int,
    jumlah_barang: float,
    harga_satuan: float
) -> int:
    """
    Simpan item belanja baru ke tb_detail_belanja.
    Kembalikan id_detail yang baru dibuat.
    tanggal_input diisi otomatis oleh DEFAULT di skema database.
    """
    kursor = koneksi.execute(
        """
        INSERT INTO tb_detail_belanja
            (id_periode, id_barang, id_satuan, jumlah_barang, harga_satuan)
        VALUES (?, ?, ?, ?, ?)
        """,
        (id_periode, id_barang, id_satuan, jumlah_barang, harga_satuan)
    )
    koneksi.commit()
    return kursor.lastrowid


def ubah_item_belanja(
    koneksi: sqlite3.Connection,
    id_detail: int,
    id_barang: int,
    id_satuan: int,
    jumlah_barang: float,
    harga_satuan: float
) -> None:
    """Perbarui data item belanja yang sudah ada berdasarkan id_detail."""
    koneksi.execute(
        """
        UPDATE tb_detail_belanja
           SET id_barang     = ?,
               id_satuan     = ?,
               jumlah_barang = ?,
               harga_satuan  = ?
         WHERE id_detail = ?
        """,
        (id_barang, id_satuan, jumlah_barang, harga_satuan, id_detail)
    )
    koneksi.commit()


def hapus_item_belanja(koneksi: sqlite3.Connection, id_detail: int) -> None:
    """Hapus satu item belanja berdasarkan id_detail."""
    koneksi.execute(
        "DELETE FROM tb_detail_belanja WHERE id_detail = ?",
        (id_detail,)
    )
    koneksi.commit()


def cari_item_belanja(
    koneksi: sqlite3.Connection,
    id_periode: int,
    kata_kunci: str = "",
    id_kategori: int = 0
) -> list:
    """
    Ambil daftar item belanja dengan filter nama barang (LIKE) dan/atau kategori.
    id_kategori = 0 berarti tampilkan semua kategori (tidak difilter).
    Seluruh kondisi filter dieksekusi dalam satu query JOIN — tidak ada filter di Python.
    Implementasi sesuai PRD §11.2.
    """

    # Bungkus kata kunci dengan wildcard untuk pencarian sebagian teks
    pola_pencarian = f"%{kata_kunci}%"

    query = """
        SELECT
            db.id_detail,
            b.nama_barang,
            k.nama_kategori,
            db.jumlah_barang,
            s.nama_satuan,
            db.harga_satuan,
            (db.jumlah_barang * db.harga_satuan) AS harga_total,
            db.tanggal_input
        FROM tb_detail_belanja db
        JOIN tb_barang   b ON b.id_barang   = db.id_barang
        JOIN tb_kategori k ON k.id_kategori = b.id_kategori
        JOIN tb_satuan   s ON s.id_satuan   = db.id_satuan
        WHERE db.id_periode      = ?
          AND b.nama_barang LIKE ?
          AND (b.id_kategori     = ? OR ? = 0)
        ORDER BY db.tanggal_input ASC
    """

    # id_kategori dikirim dua kali untuk logika OR (filter aktif ATAU tampilkan semua)
    return koneksi.execute(
        query, (id_periode, pola_pencarian, id_kategori, id_kategori)
    ).fetchall()


def hitung_total_pengeluaran(koneksi: sqlite3.Connection, id_periode: int) -> float:
    """
    Hitung total semua pengeluaran dalam satu periode.
    harga_total dihitung di query (jumlah * harga_satuan), tidak disimpan di DB.
    Kembalikan 0.0 jika belum ada item.
    """
    hasil = koneksi.execute(
        """
        SELECT COALESCE(SUM(jumlah_barang * harga_satuan), 0) AS total
        FROM tb_detail_belanja
        WHERE id_periode = ?
        """,
        (id_periode,)
    ).fetchone()
    return float(hasil["total"])


def ambil_pengeluaran_harian(koneksi: sqlite3.Connection, id_periode: int) -> dict:
    """
    Ambil total pengeluaran per hari dalam satu periode untuk grafik Dashboard.
    Kembalikan dictionary {nama_hari: total} untuk 7 hari (Sen-Min).
    Hari tanpa transaksi tetap ada dengan nilai 0.0 (FR-DB-2).
    """

    # Nama hari singkatan sesuai PRD FR-DB-2 — urutan Senin=0 s.d. Minggu=6
    urutan_hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

    # Inisialisasi semua hari dengan 0 agar hari tanpa transaksi tetap tampil
    pengeluaran_per_hari = {hari: 0.0 for hari in urutan_hari}

    # strftime('%w') di SQLite: 0=Minggu, 1=Senin, ..., 6=Sabtu
    # Petakan ke index urutan_hari: Senin(1)->0, ..., Sabtu(6)->5, Minggu(0)->6
    hasil = koneksi.execute(
        """
        SELECT
            CAST(strftime('%w', tanggal_input) AS INTEGER) AS hari_angka,
            SUM(jumlah_barang * harga_satuan) AS total_hari
        FROM tb_detail_belanja
        WHERE id_periode = ?
        GROUP BY hari_angka
        """,
        (id_periode,)
    ).fetchall()

    # Konversi angka hari SQLite ke label Indonesia
    peta_hari = {1: "Sen", 2: "Sel", 3: "Rab", 4: "Kam", 5: "Jum", 6: "Sab", 0: "Min"}
    for baris in hasil:
        nama_hari = peta_hari.get(baris["hari_angka"])
        if nama_hari:
            pengeluaran_per_hari[nama_hari] = float(baris["total_hari"])

    return pengeluaran_per_hari


def ambil_item_by_id(koneksi: sqlite3.Connection, id_detail: int) -> sqlite3.Row | None:
    """
    Ambil satu item belanja lengkap berdasarkan id_detail.
    Digunakan saat mengisi form edit dengan data lama.
    """
    return koneksi.execute(
        """
        SELECT
            db.id_detail,
            db.id_barang,
            b.nama_barang,
            db.id_satuan,
            s.nama_satuan,
            b.id_kategori,
            k.nama_kategori,
            db.jumlah_barang,
            db.harga_satuan,
            (db.jumlah_barang * db.harga_satuan) AS harga_total
        FROM tb_detail_belanja db
        JOIN tb_barang   b ON b.id_barang   = db.id_barang
        JOIN tb_satuan   s ON s.id_satuan   = db.id_satuan
        JOIN tb_kategori k ON k.id_kategori = b.id_kategori
        WHERE db.id_detail = ?
        """,
        (id_detail,)
    ).fetchone()
