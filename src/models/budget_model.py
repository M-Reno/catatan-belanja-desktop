# models/budget_model.py
# Akses database untuk tb_periode_budget
# Fungsi lengkap diimplementasikan di Tahap 2 — file ini berisi bagian yang
# dibutuhkan oleh database.py saat inisialisasi (Gap #2 Design System §8)

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

    # Ambil tanggal hari ini dalam format ISO (yyyy-mm-dd) untuk perbandingan dengan kolom DATE di SQLite
    tanggal_hari_ini = date.today().isoformat()

    # Cari semua periode yang masih ditandai aktif tapi tgl_selesai-nya sudah lewat
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
