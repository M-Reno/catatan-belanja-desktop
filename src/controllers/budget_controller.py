"""
budget_controller.py — Business logic untuk manajemen budget mingguan
Dipanggil oleh: BudgetPage (views/budget_page.py)
"""

import sqlite3
from datetime import date, timedelta
from typing import Tuple, List, Dict

from models.budget_model import (
    simpan_budget, cek_duplikasi_budget, ambil_semua_budget
)
from utils.date_helper import (
    hitung_minggu_ke, ambil_bulan, ambil_tahun, format_tanggal
)


class BudgetController:
    """Controller untuk halaman Budget — handle validasi, simpan, dan load data."""

    def __init__(self, koneksi: sqlite3.Connection):
        self.koneksi = koneksi

    def simpan_budget_baru(
        self, tgl_mulai_str: str, tgl_selesai_str: str, nominal_str: str
    ) -> Tuple[bool, str]:
        """
        Validasi dan simpan budget baru.
        Return: (success: bool, message: str)
        """

        # Validasi 1: semua field wajib terisi
        if not tgl_mulai_str or not tgl_selesai_str or not nominal_str:
            return False, "Semua field wajib diisi."

        # Parse tanggal — tkcalendar mengembalikan string dd-mm-yyyy atau dd/mm/yyyy
        try:
            # Coba parse format dd-mm-yyyy dulu
            if "-" in tgl_mulai_str:
                tgl_mulai = date.fromisoformat(
                    "-".join(reversed(tgl_mulai_str.split("-")))
                )
                tgl_selesai = date.fromisoformat(
                    "-".join(reversed(tgl_selesai_str.split("-")))
                )
            else:
                # Format dd/mm/yyyy
                parts_mulai = tgl_mulai_str.split("/")
                parts_selesai = tgl_selesai_str.split("/")
                tgl_mulai = date(
                    int(parts_mulai[2]), int(parts_mulai[1]), int(parts_mulai[0])
                )
                tgl_selesai = date(
                    int(parts_selesai[2]), int(parts_selesai[1]), int(parts_selesai[0])
                )
        except (ValueError, IndexError):
            return False, "Format tanggal tidak valid."

        # Parse nominal — strip Rp dan titik
        try:
            nominal = float(nominal_str.replace("Rp", "").replace(".", "").strip())
        except ValueError:
            return False, "Nominal budget harus berupa angka."

        # Validasi 2: nominal harus > 0
        if nominal <= 0:
            return False, "Nominal budget harus lebih dari Rp0."

        # Validasi 3: tanggal selesai harus >= tanggal mulai
        if tgl_selesai < tgl_mulai:
            return False, "Tanggal selesai tidak boleh lebih awal dari tanggal mulai."

        # Hitung minggu_ke, bulan, tahun dari tgl_mulai
        minggu_ke = hitung_minggu_ke(tgl_mulai)
        bulan = ambil_bulan(tgl_mulai)
        tahun = ambil_tahun(tgl_mulai)

        # Validasi 4: cek duplikasi budget (minggu + bulan + tahun sudah ada)
        if cek_duplikasi_budget(self.koneksi, minggu_ke, bulan, tahun):
            return False, "Budget untuk minggu ini sudah pernah dibuat."

        # Simpan ke database
        try:
            simpan_budget(
                self.koneksi,
                minggu_ke,
                bulan,
                tahun,
                tgl_mulai.isoformat(),
                tgl_selesai.isoformat(),
                nominal
            )
            return True, "Budget berhasil disimpan!"
        except Exception as e:
            return False, f"Gagal menyimpan budget: {str(e)}"

    def muat_riwayat_budget(self) -> List[Dict]:
        """
        Ambil semua budget yang pernah dibuat untuk ditampilkan di tabel riwayat.
        Return list of dict: {minggu_ke, tanggal_str, nominal_str}
        """
        hasil_query = ambil_semua_budget(self.koneksi)
        riwayat = []

        for row in hasil_query:
            # Akses via nama kolom — urutan SELECT * tidak diasumsikan
            minggu_ke       = row["minggu_ke"]
            tgl_mulai_str   = row["tgl_mulai"]
            tgl_selesai_str = row["tgl_selesai"]
            nominal         = row["nominal_budget"]

            # Parse tanggal dari ISO format
            tgl_mulai = date.fromisoformat(tgl_mulai_str)
            tgl_selesai = date.fromisoformat(tgl_selesai_str)

            # Format untuk tampilan: dd-mm-yyyy - dd-mm-yyyy
            tanggal_str = f"{format_tanggal(tgl_mulai)} - {format_tanggal(tgl_selesai)}"

            # Format nominal ke Rupiah
            from utils.format_helper import format_rupiah
            nominal_str = format_rupiah(nominal)

            riwayat.append({
                "minggu_ke": minggu_ke,
                "tanggal": tanggal_str,
                "nominal": nominal_str
            })

        return riwayat

    def hitung_tanggal_selesai(self, tgl_mulai_str: str) -> str:
        """
        Hitung tanggal selesai otomatis (tgl_mulai + 6 hari).
        Return: string tanggal dalam format dd-mm-yyyy atau dd/mm/yyyy sesuai input.
        """
        if not tgl_mulai_str:
            return ""

        try:
            # Deteksi separator
            separator = "-" if "-" in tgl_mulai_str else "/"

            # Parse tanggal
            if separator == "-":
                parts = tgl_mulai_str.split("-")
            else:
                parts = tgl_mulai_str.split("/")

            tgl_mulai = date(int(parts[2]), int(parts[1]), int(parts[0]))

            # Tambah 6 hari
            tgl_selesai = tgl_mulai + timedelta(days=6)

            # Format kembali dengan separator yang sama
            return f"{tgl_selesai.day:02d}{separator}{tgl_selesai.month:02d}{separator}{tgl_selesai.year}"
        except (ValueError, IndexError):
            return ""