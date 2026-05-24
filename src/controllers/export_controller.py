"""
export_controller.py — Controller untuk export PDF dan Excel.
Mengambil data dari DB (semua item, tanpa filter) lalu memanggil
export_helper yang sesuai. Tidak ada logika bisnis di sini.

Spesifikasi: PRD §11.3.C & DEVELOPER_CHECKLIST Tahap 10
"""

import sqlite3

from models.detail_belanja_model import cari_item_belanja, hitung_total_pengeluaran
from models.budget_model import ambil_budget_by_id
from utils.export_helper import ekspor_pdf, ekspor_excel, _nama_file_default


class ExportController:
    """
    Controller export yang dipanggil dari view manapun yang butuh fitur ekspor.
    Bisa dipakai dari RiwayatPage (State A & B) maupun DaftarBelanjaPage.
    """

    def __init__(self, koneksi: sqlite3.Connection):
        self._koneksi = koneksi

    def _ambil_data_periode(self, id_periode: int) -> dict | None:
        """
        Ambil data periode dan hitung total + sisa budget.
        Kembalikan dict siap pakai untuk export_helper, atau None jika tidak ditemukan.
        """
        periode = ambil_budget_by_id(self._koneksi, id_periode)
        if periode is None:
            return None

        # Hitung total pengeluaran dari semua item di periode ini
        total = hitung_total_pengeluaran(self._koneksi, id_periode)
        sisa  = periode["nominal_budget"] - total

        return {
            "id_periode"        : periode["id_periode"],
            "minggu_ke"         : periode["minggu_ke"],
            "bulan"             : periode["bulan"],
            "tahun"             : periode["tahun"],
            "tgl_mulai"         : periode["tgl_mulai"],
            "tgl_selesai"       : periode["tgl_selesai"],
            "nominal_budget"    : periode["nominal_budget"],
            "total_pengeluaran" : total,
            "sisa_budget"       : sisa,
        }

    def _ambil_semua_item(self, id_periode: int) -> list:
        """
        Ambil SEMUA item belanja periode tanpa filter apapun.
        Export harus lengkap — tidak terpengaruh filter tampilan (PRD §11.3.C).
        """
        # kata_kunci="" dan id_kategori=0 → tampilkan semua baris
        return cari_item_belanja(self._koneksi, id_periode, kata_kunci="", id_kategori=0)

    def handle_ekspor(self, tipe: str, id_periode: int) -> tuple[bool, str]:
        """
        Jalankan alur ekspor lengkap:
        1. Ambil data periode dan semua item dari DB
        2. Tampilkan dialog simpan file ke pengguna
        3. Panggil helper PDF atau Excel sesuai tipe

        Parameter tipe: "pdf" atau "excel"
        Kembalikan tuple (berhasil: bool, pesan: str) untuk ditampilkan sebagai toast.
        """
        # Ambil data dari database
        data_periode = self._ambil_data_periode(id_periode)
        if data_periode is None:
            return False, "Data periode tidak ditemukan."

        daftar_item = self._ambil_semua_item(id_periode)

        # Tampilkan dialog simpan — nama file default sesuai pola Design System §10.5
        nama_default = _nama_file_default(data_periode)

        import tkinter.filedialog as fd
        if tipe == "pdf":
            path_file = fd.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Simpan Laporan PDF",
                initialfile=nama_default + ".pdf",
            )
        else:
            path_file = fd.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Simpan Laporan Excel",
                initialfile=nama_default + ".xlsx",
            )

        # Pengguna membatalkan dialog — tidak lakukan apa-apa
        if not path_file:
            return False, ""

        # Panggil helper yang sesuai
        try:
            if tipe == "pdf":
                ekspor_pdf(path_file, data_periode, daftar_item)
                return True, " File PDF berhasil disimpan"
            else:
                ekspor_excel(path_file, data_periode, daftar_item)
                return True, " File Excel berhasil disimpan"
        except Exception as e:
            return False, f"Gagal menyimpan file: {e}"
