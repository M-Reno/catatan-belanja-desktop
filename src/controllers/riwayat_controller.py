# controllers/riwayat_controller.py
# Logika bisnis untuk halaman Riwayat (State A: list minggu, State B: detail minggu)
# Menjembatani views/riwayat_page.py dengan model-model di bawah

import sqlite3

from models.budget_model import ambil_budget_per_bulan, ambil_budget_by_id
from models.detail_belanja_model import cari_item_belanja, hitung_total_pengeluaran
from models.kategori_model import ambil_semua_kategori


class RiwayatController:
    """
    Controller untuk seluruh operasi di halaman Riwayat.
    View tidak boleh akses model langsung — semua lewat sini.
    """

    def __init__(self, koneksi: sqlite3.Connection):
        self._koneksi = koneksi

    # ─── STATE A: LIST MINGGU ─────────────────────────────────────────────────

    def ambil_minggu_per_bulan(self, bulan: int, tahun: int) -> list:
        """
        Ambil semua periode budget pada bulan dan tahun tertentu,
        lengkap dengan total pengeluaran masing-masing.
        Digunakan State A untuk menampilkan card minggu.
        Kembalikan list dict dengan kunci tambahan: total_pengeluaran.
        """
        daftar_periode = ambil_budget_per_bulan(self._koneksi, bulan, tahun)

        hasil = []
        for periode in daftar_periode:
            # Hitung total pengeluaran tiap periode dalam satu query
            total = hitung_total_pengeluaran(self._koneksi, periode["id_periode"])
            hasil.append({
                "id_periode"     : periode["id_periode"],
                "minggu_ke"      : periode["minggu_ke"],
                "bulan"          : periode["bulan"],
                "tahun"          : periode["tahun"],
                "tgl_mulai"      : periode["tgl_mulai"],
                "tgl_selesai"    : periode["tgl_selesai"],
                "nominal_budget" : periode["nominal_budget"],
                "total_pengeluaran": total,
            })
        return hasil

    # ─── STATE B: DETAIL MINGGU ───────────────────────────────────────────────

    def ambil_data_periode(self, id_periode: int) -> dict | None:
        """
        Ambil satu data periode budget berdasarkan id_periode.
        Digunakan State B untuk mengisi tiga stat card.
        Kembalikan dict dengan kunci tambahan: total_pengeluaran, sisa_budget.
        Kembalikan None jika periode tidak ditemukan.
        """
        periode = ambil_budget_by_id(self._koneksi, id_periode)
        if periode is None:
            return None

        total = hitung_total_pengeluaran(self._koneksi, id_periode)
        sisa  = periode["nominal_budget"] - total

        return {
            "id_periode"       : periode["id_periode"],
            "minggu_ke"        : periode["minggu_ke"],
            "bulan"            : periode["bulan"],
            "tahun"            : periode["tahun"],
            "tgl_mulai"        : periode["tgl_mulai"],
            "tgl_selesai"      : periode["tgl_selesai"],
            "nominal_budget"   : periode["nominal_budget"],
            "total_pengeluaran": total,
            "sisa_budget"      : sisa,
        }

    def ambil_daftar_item(
        self,
        id_periode: int,
        kata_kunci: str = "",
        id_kategori: int = 0
    ) -> list:
        """
        Ambil item belanja dengan filter opsional (auto-search + kategori).
        Dipanggil setiap kali tabel State B perlu di-render ulang.
        id_kategori=0 berarti tampilkan semua kategori.
        """
        return cari_item_belanja(self._koneksi, id_periode, kata_kunci, id_kategori)

    def ambil_daftar_item_semua(self, id_periode: int) -> list:
        """
        Ambil SEMUA item belanja tanpa filter apapun.
        Digunakan oleh export — laporan harus lengkap, tidak terpotong filter tampilan.
        """
        return cari_item_belanja(self._koneksi, id_periode, kata_kunci="", id_kategori=0)

    def ambil_daftar_kategori(self) -> list:
        """
        Ambil semua kategori untuk isi dropdown filter di State B.
        """
        return ambil_semua_kategori(self._koneksi)