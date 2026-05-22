# config/database.py
# Koneksi database, pembuatan tabel, dan data awal (seeder) — satu file
# Dijalankan saat aplikasi pertama kali dibuka via inisialisasi_database()

import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Pastikan folder src/ ada di sys.path agar import antar modul berfungsi
# tanpa perlu set PYTHONPATH manual dari terminal
_DIREKTORI_SRC = Path(__file__).resolve().parent.parent  # .../src/
if str(_DIREKTORI_SRC) not in sys.path:
    sys.path.insert(0, str(_DIREKTORI_SRC))


# =============================================================================
# PATH DATABASE
# =============================================================================

# File database disimpan di root folder proyek (satu level di atas src/)
DIREKTORI_PROYEK = _DIREKTORI_SRC.parent                   # .../catatan_belanja_beta1/
PATH_DATABASE    = DIREKTORI_PROYEK / "catatan_belanja.db"


# =============================================================================
# KONEKSI
# =============================================================================

def buka_koneksi() -> sqlite3.Connection:
    """
    Buka dan kembalikan koneksi ke database SQLite.
    Aktifkan foreign key enforcement karena SQLite menonaktifkannya secara default.
    """
    koneksi = sqlite3.connect(str(PATH_DATABASE))

    # Aktifkan foreign key agar ON DELETE CASCADE dan ON DELETE SET NULL bekerja
    koneksi.execute("PRAGMA foreign_keys = ON")

    # Kembalikan baris sebagai objek yang bisa diakses via nama kolom
    koneksi.row_factory = sqlite3.Row

    return koneksi


def tutup_koneksi(koneksi: sqlite3.Connection) -> None:
    """Tutup koneksi database dengan aman jika masih terbuka."""
    if koneksi:
        koneksi.close()


# =============================================================================
# PEMBUATAN TABEL
# =============================================================================

def _buat_semua_tabel(koneksi: sqlite3.Connection) -> None:
    """
    Buat kelima tabel jika belum ada.
    Aman dijalankan berulang kali karena menggunakan CREATE TABLE IF NOT EXISTS.
    """

    # Tabel 1: periode budget — menyimpan alokasi dana per minggu
    koneksi.execute("""
        CREATE TABLE IF NOT EXISTS tb_periode_budget (
            id_periode     INTEGER PRIMARY KEY AUTOINCREMENT,
            minggu_ke      INTEGER NOT NULL,
            bulan          INTEGER NOT NULL,
            tahun          INTEGER NOT NULL,
            tgl_mulai      DATE    NOT NULL,
            tgl_selesai    DATE    NOT NULL,
            nominal_budget REAL    NOT NULL DEFAULT 0,
            is_active      INTEGER NOT NULL DEFAULT 1,
            UNIQUE (minggu_ke, bulan, tahun)
        )
    """)

    # Tabel 2: kategori barang belanjaan
    koneksi.execute("""
        CREATE TABLE IF NOT EXISTS tb_kategori (
            id_kategori   INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_kategori TEXT    NOT NULL UNIQUE
        )
    """)

    # Tabel 3: satuan ukuran barang — dikelola dinamis via halaman Pengaturan
    koneksi.execute("""
        CREATE TABLE IF NOT EXISTS tb_satuan (
            id_satuan   INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_satuan TEXT    NOT NULL UNIQUE
        )
    """)

    # Tabel 4: master data barang — referensi nama barang unik
    koneksi.execute("""
        CREATE TABLE IF NOT EXISTS tb_barang (
            id_barang   INTEGER PRIMARY KEY AUTOINCREMENT,
            id_kategori INTEGER REFERENCES tb_kategori(id_kategori) ON DELETE SET NULL,
            nama_barang TEXT    NOT NULL,
            UNIQUE (nama_barang, id_kategori)
        )
    """)

    # Tabel 5: detail item yang dibeli dalam satu periode
    koneksi.execute("""
        CREATE TABLE IF NOT EXISTS tb_detail_belanja (
            id_detail      INTEGER  PRIMARY KEY AUTOINCREMENT,
            id_periode     INTEGER  NOT NULL REFERENCES tb_periode_budget(id_periode) ON DELETE CASCADE,
            id_barang      INTEGER  NOT NULL REFERENCES tb_barang(id_barang),
            id_satuan      INTEGER  NOT NULL REFERENCES tb_satuan(id_satuan),
            jumlah_barang  REAL     NOT NULL DEFAULT 0,
            harga_satuan   REAL     NOT NULL DEFAULT 0,
            tanggal_input  DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    koneksi.commit()


# =============================================================================
# SEEDER — DATA AWAL
# =============================================================================

def _isi_data_awal(koneksi: sqlite3.Connection) -> None:
    """
    Isi data awal untuk tb_kategori dan tb_satuan.
    INSERT OR IGNORE memastikan tidak ada duplikasi jika sudah ada.
    """

    # 5 kategori default
    kategori_awal = [
        ("Makanan & Minuman",),
        ("Kebersihan",),
        ("Kesehatan",),
        ("Pendidikan",),
        ("Lain-lain",),
    ]
    koneksi.executemany(
        "INSERT OR IGNORE INTO tb_kategori (nama_kategori) VALUES (?)",
        kategori_awal
    )

    # 8 satuan default — sesuai PRD §4.1 dan Design System §3.4
    satuan_awal = [
        ("pcs",),
        ("kg",),
        ("liter",),
        ("pack",),
        ("bungkus",),
        ("box",),
        ("lusin",),
        ("lainnya",),
    ]
    koneksi.executemany(
        "INSERT OR IGNORE INTO tb_satuan (nama_satuan) VALUES (?)",
        satuan_awal
    )

    koneksi.commit()


# =============================================================================
# FUNGSI UTAMA
# =============================================================================

def inisialisasi_database() -> Optional[sqlite3.Connection]:
    """
    Inisialisasi penuh database saat aplikasi pertama kali dibuka.
    Langkah: buka koneksi -> buat tabel -> isi seeder -> tandai periode kadaluarsa.

    Mengembalikan koneksi yang sudah siap dipakai oleh seluruh aplikasi.
    Jika terjadi error kritis, tampilkan dialog dan keluar dengan aman (NFR-05).
    """
    try:
        koneksi = buka_koneksi()

        # Buat semua tabel jika belum ada
        _buat_semua_tabel(koneksi)

        # Isi data awal satuan dan kategori
        _isi_data_awal(koneksi)

        # Tandai periode yang sudah melewati tanggal selesai sebagai tidak aktif
        from models.budget_model import tandai_periode_selesai_otomatis
        tandai_periode_selesai_otomatis(koneksi)

        return koneksi

    except sqlite3.DatabaseError as error_db:
        _tampilkan_error_kritis(
            f"Database tidak dapat dibuka atau rusak.\n\n"
            f"Detail: {error_db}\n\n"
            f"Pastikan file 'catatan_belanja.db' tidak dibuka oleh program lain,\n"
            f"atau hapus file tersebut agar aplikasi membuat database baru."
        )
        return None

    except Exception as error_umum:
        _tampilkan_error_kritis(
            f"Terjadi error saat memulai aplikasi.\n\n"
            f"Detail: {error_umum}"
        )
        return None


def _tampilkan_error_kritis(pesan: str) -> None:
    """
    Tampilkan dialog error yang jelas lalu keluar dengan aman (NFR-05).
    Menggunakan tkinter standar karena CTk mungkin belum terinisialisasi.
    """
    try:
        import tkinter as tk
        from tkinter import messagebox

        root_sementara = tk.Tk()
        root_sementara.withdraw()

        messagebox.showerror(
            title="Error — Catatan Belanja",
            message=pesan
        )
        root_sementara.destroy()

    except Exception:
        print(f"[ERROR KRITIS] {pesan}", file=sys.stderr)

    finally:
        sys.exit(1)


# =============================================================================
# ENTRY POINT — Untuk verifikasi langsung via terminal
# =============================================================================

if __name__ == "__main__":
    print(f"Inisialisasi database di: {PATH_DATABASE}")

    koneksi_test = inisialisasi_database()

    # Hentikan verifikasi jika database gagal diinisialisasi
    if koneksi_test is None:
        print("[ERROR] Database gagal diinisialisasi.", file=sys.stderr)
        sys.exit(1)

    tabel = koneksi_test.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    print(f"\nTabel yang terbentuk ({len(tabel)}):")
    for t in tabel:
        print(f"  - {t['name']}")

    kategori = koneksi_test.execute("SELECT * FROM tb_kategori").fetchall()
    print(f"\nKategori ({len(kategori)} item):")
    for k in kategori:
        print(f"  [{k['id_kategori']}] {k['nama_kategori']}")

    satuan = koneksi_test.execute("SELECT * FROM tb_satuan").fetchall()
    print(f"\nSatuan ({len(satuan)} item):")
    for s in satuan:
        print(f"  [{s['id_satuan']}] {s['nama_satuan']}")

    tutup_koneksi(koneksi_test)
    print("\nVerifikasi selesai. Database siap digunakan.")