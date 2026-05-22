# models/budget_model.py
# Seluruh akses database untuk tabel tb_periode_budget
# Digunakan oleh: budget_controller.py, dashboard_controller.py, riwayat_controller.py

import sqlite3
from datetime import date


# =============================================================================
# KONSTANTA STATUS PERIODE
# Gunakan konstanta ini di seluruh kode — jangan tulis angka 1/0 langsung
# =============================================================================

PERIODE_AKTIF   = 1   # Periode masih dalam rentang tanggal berjalan
PERIODE_SELESAI = 0   # Periode sudah melewati tanggal akhir


# =============================================================================
# OTOMASI STATUS
# =============================================================================

def tandai_periode_selesai_otomatis(koneksi: sqlite3.Connection) -> None:
    """
    Ubah status periode menjadi selesai jika tanggal akhirnya sudah terlewat.
    Dipanggil sekali saat aplikasi dibuka via inisialisasi_database().
    """
    tanggal_hari_ini = date.today().isoformat()

    koneksi.execute(
        """
        UPDATE tb_periode_budget
           SET is_active = ?
         WHERE tgl_selesai < ?
           AND is_active  = ?
        """,
        (PERIODE_SELESAI, tanggal_hari_ini, PERIODE_AKTIF)
    )
    koneksi.commit()


# =============================================================================
# SIMPAN & VALIDASI
# =============================================================================

def cek_duplikasi_budget(koneksi: sqlite3.Connection, minggu_ke: int, bulan: int, tahun: int) -> bool:
    """
    Cek apakah budget untuk kombinasi minggu+bulan+tahun sudah ada.
    Kembalikan True jika sudah ada (duplikasi — tidak boleh disimpan lagi).
    """
    hasil = koneksi.execute(
        """
        SELECT COUNT(*) as jumlah FROM tb_periode_budget
        WHERE minggu_ke = ? AND bulan = ? AND tahun = ?
        """,
        (minggu_ke, bulan, tahun)
    ).fetchone()
    return hasil["jumlah"] > 0


def simpan_budget(
    koneksi: sqlite3.Connection,
    minggu_ke: int,
    bulan: int,
    tahun: int,
    tgl_mulai: str,
    tgl_selesai: str,
    nominal_budget: float
) -> int:
    """
    Simpan budget baru ke tb_periode_budget.
    Kembalikan id_periode yang baru dibuat.
    Pastikan cek_duplikasi_budget() sudah dijalankan sebelum memanggil ini.
    """
    kursor = koneksi.execute(
        """
        INSERT INTO tb_periode_budget
            (minggu_ke, bulan, tahun, tgl_mulai, tgl_selesai, nominal_budget, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (minggu_ke, bulan, tahun, tgl_mulai, tgl_selesai, nominal_budget, PERIODE_AKTIF)
    )
    koneksi.commit()
    return kursor.lastrowid


# =============================================================================
# QUERY BACA
# =============================================================================

def ambil_budget_aktif(koneksi: sqlite3.Connection, minggu_ke: int, bulan: int, tahun: int) -> sqlite3.Row | None:
    """
    Ambil data budget aktif untuk minggu, bulan, dan tahun tertentu.
    Digunakan Dashboard untuk mengecek apakah ada budget minggu berjalan.
    Kembalikan satu baris atau None jika tidak ada.
    """
    return koneksi.execute(
        """
        SELECT * FROM tb_periode_budget
        WHERE minggu_ke = ? AND bulan = ? AND tahun = ?
          AND is_active = ?
        """,
        (minggu_ke, bulan, tahun, PERIODE_AKTIF)
    ).fetchone()


def ambil_semua_budget(koneksi: sqlite3.Connection) -> list:
    """
    Ambil seluruh riwayat budget diurutkan dari yang terbaru.
    Digunakan tabel riwayat di halaman Budget (FR-BG-3).
    """
    return koneksi.execute(
        """
        SELECT * FROM tb_periode_budget
        ORDER BY tahun DESC, bulan DESC, minggu_ke DESC
        """
    ).fetchall()


def ambil_budget_per_bulan(koneksi: sqlite3.Connection, bulan: int, tahun: int) -> list:
    """
    Ambil semua periode budget dalam bulan dan tahun tertentu.
    Digunakan halaman Riwayat untuk menampilkan daftar minggu.
    """
    return koneksi.execute(
        """
        SELECT * FROM tb_periode_budget
        WHERE bulan = ? AND tahun = ?
        ORDER BY minggu_ke ASC
        """,
        (bulan, tahun)
    ).fetchall()


def ambil_budget_by_id(koneksi: sqlite3.Connection, id_periode: int) -> sqlite3.Row | None:
    """
    Ambil satu data budget berdasarkan id_periode.
    Digunakan oleh export_controller dan riwayat_controller.
    """
    return koneksi.execute(
        "SELECT * FROM tb_periode_budget WHERE id_periode = ?",
        (id_periode,)
    ).fetchone()


def ambil_semua_tahun_tersedia(koneksi: sqlite3.Connection) -> list:
    """
    Ambil daftar tahun yang memiliki data budget.
    Digunakan untuk mengisi dropdown filter tahun di halaman Riwayat.
    """
    hasil = koneksi.execute(
        "SELECT DISTINCT tahun FROM tb_periode_budget ORDER BY tahun DESC"
    ).fetchall()
    return [baris["tahun"] for baris in hasil]
