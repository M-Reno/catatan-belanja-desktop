"""
date_helper.py — Fungsi-fungsi bantu kalkulasi tanggal dan format tampilan
Digunakan oleh: budget_controller.py, semua controller yang butuh format tanggal
"""

import math
from datetime import date, timedelta


def hitung_minggu_ke(tanggal_mulai: date) -> int:
    """
    Hitung urutan minggu dalam bulan berdasarkan tanggal mulai periode.
    Rumus: ceil(hari / 7) — tanggal 1–7 = minggu ke-1, 8–14 = minggu ke-2, dst.
    """
    return math.ceil(tanggal_mulai.day / 7)


def ambil_bulan(tanggal_mulai: date) -> int:
    """Ambil angka bulan (1–12) dari tanggal mulai periode."""
    return tanggal_mulai.month


def ambil_tahun(tanggal_mulai: date) -> int:
    """Ambil angka tahun 4 digit dari tanggal mulai periode."""
    return tanggal_mulai.year


def format_tanggal(tanggal: date) -> str:
    """Format objek date ke string dd-mm-yyyy untuk ditampilkan di UI."""
    return tanggal.strftime("%d-%m-%Y")


def hitung_tanggal_selesai(tanggal_mulai: date) -> date:
    """
    Hitung tanggal selesai secara otomatis = tanggal mulai + 6 hari.
    Digunakan untuk otomasi form Budget (FR-BG-4).
    """
    return tanggal_mulai + timedelta(days=6)


def nama_bulan(nomor_bulan: int) -> str:
    """
    Kembalikan nama bulan dalam Bahasa Indonesia berdasarkan angka bulan (1–12).
    Digunakan untuk label di halaman Riwayat dan header ekspor.
    """
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April",
        "Mei", "Juni", "Juli", "Agustus",
        "September", "Oktober", "November", "Desember"
    ]

    # Pastikan nomor bulan valid sebelum mengambil dari daftar
    if 1 <= nomor_bulan <= 12:
        return daftar_bulan[nomor_bulan - 1]

    return ""


def minggu_ke_label(minggu_ke: int) -> str:
    """
    Kembalikan label teks untuk urutan minggu, misalnya 'Minggu ke-4'.
    Digunakan untuk header halaman dan card Riwayat.
    """
    return f"Minggu ke-{minggu_ke}"


def bulan_punya_minggu_5(bulan: int, tahun: int) -> bool:
    """
    Cek apakah bulan tertentu memiliki tanggal ke-29 atau lebih (ada minggu ke-5).
    Digunakan untuk menentukan apakah tombol 'Minggu ke-5' perlu ditampilkan di State A.
    """
    import calendar

    # Ambil jumlah hari dalam bulan tersebut
    jumlah_hari = calendar.monthrange(tahun, bulan)[1]

    # Minggu ke-5 ada jika bulan tersebut punya tanggal 29, 30, atau 31
    return jumlah_hari >= 29


def format_rentang_tanggal(tgl_mulai: date, tgl_selesai: date) -> str:
    """
    Format dua tanggal menjadi string rentang, misalnya '23-11-2025 - 29-11-2025'.
    Digunakan untuk sub-label di halaman Dashboard, Daftar Belanja, dan Riwayat.
    """
    return f"{format_tanggal(tgl_mulai)} - {format_tanggal(tgl_selesai)}"


def get_minggu_dan_tahun_berjalan() -> tuple:
    """
    Kembalikan tuple (minggu_ke, bulan, tahun) berdasarkan tanggal hari ini.
    Digunakan saat aplikasi pertama dibuka untuk menentukan periode aktif Dashboard.
    """
    hari_ini = date.today()
    return (
        hitung_minggu_ke(hari_ini),
        ambil_bulan(hari_ini),
        ambil_tahun(hari_ini)
    )