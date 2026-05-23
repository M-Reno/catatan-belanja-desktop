"""
dashboard_controller.py — Business logic untuk halaman Dashboard
Dipanggil oleh: DashboardPage (views/dashboard_page.py)

Tanggung jawab:
- Cek apakah ada budget aktif untuk minggu berjalan
- Hitung total pengeluaran dan sisa budget
- Sediakan data grafik harian (Sen–Min)
"""

import sqlite3
from datetime import date

from models.budget_model import ambil_budget_aktif
from models.detail_belanja_model import hitung_total_pengeluaran, ambil_pengeluaran_harian
from utils.date_helper import (
    hitung_minggu_ke, ambil_bulan, ambil_tahun,
    format_rentang_tanggal, nama_bulan
)
from utils.format_helper import format_rupiah


class DashboardController:
    """Controller halaman Dashboard — sediakan semua data yang dibutuhkan view."""

    def __init__(self, koneksi: sqlite3.Connection):
        self.koneksi = koneksi

    def muat_data_dashboard(self) -> dict | None:
        """
        Cek apakah ada budget aktif untuk minggu berjalan.
        Jika ada, kembalikan dict lengkap untuk dirender.
        Jika tidak ada, kembalikan None (trigger empty state).
        """
        hari_ini = date.today()
        minggu_ke = hitung_minggu_ke(hari_ini)
        bulan     = ambil_bulan(hari_ini)
        tahun     = ambil_tahun(hari_ini)

        # Cari budget aktif untuk minggu ini
        budget = ambil_budget_aktif(self.koneksi, minggu_ke, bulan, tahun)

        if budget is None:
            # Tidak ada budget — tampilkan empty state
            return None

        id_periode      = budget["id_periode"]
        nominal_budget  = float(budget["nominal_budget"])
        tgl_mulai_str   = budget["tgl_mulai"]
        tgl_selesai_str = budget["tgl_selesai"]

        # Hitung total pengeluaran dari semua item dalam periode ini
        total_pengeluaran = hitung_total_pengeluaran(self.koneksi, id_periode)

        # Hitung sisa budget — bisa negatif jika melebihi budget
        sisa_budget = nominal_budget - total_pengeluaran

        # Batas peringatan = 20% dari nominal awal (FR-DB-3)
        batas_peringatan = nominal_budget * 0.20

        # Tentukan warna sisa budget berdasarkan statusnya
        if sisa_budget < 0:
            status_sisa = "danger"    # Merah — melebihi budget
        elif sisa_budget < batas_peringatan:
            status_sisa = "warning"   # Kuning — hampir habis
        else:
            status_sisa = "normal"    # Normal

        # Parse tanggal ISO untuk format tampilan
        from datetime import date as _date
        tgl_mulai  = _date.fromisoformat(tgl_mulai_str)
        tgl_selesai = _date.fromisoformat(tgl_selesai_str)

        # Label sub-header: "Minggu ke-4 · November 2025 · 23-11-2025 - 29-11-2025"
        label_periode = (
            f"Minggu ke-{minggu_ke} · "
            f"{nama_bulan(bulan)} {tahun} · "
            f"{format_rentang_tanggal(tgl_mulai, tgl_selesai)}"
        )

        return {
            "id_periode"        : id_periode,
            "nominal_budget"    : nominal_budget,
            "total_pengeluaran" : total_pengeluaran,
            "sisa_budget"       : sisa_budget,
            "status_sisa"       : status_sisa,
            "label_periode"     : label_periode,
            # String siap tampil
            "str_total"         : format_rupiah(total_pengeluaran),
            "str_sisa"          : format_rupiah(sisa_budget),
        }

    def muat_data_grafik(self, id_periode: int) -> dict:
        """
        Kembalikan dict {nama_hari: total} untuk 7 hari (Sen–Min).
        Hari tanpa transaksi tetap ada dengan nilai 0.0 (FR-DB-2).
        """
        return ambil_pengeluaran_harian(self.koneksi, id_periode)