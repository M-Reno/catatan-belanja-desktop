"""
Halaman Riwayat — State A (list minggu per bulan) + State B (detail minggu).
Sesuai PRD §5.4 FR-RW-1 s.d. FR-RW-5, Design System §4.4.
"""

import sqlite3
from datetime import date
from typing import Optional
import customtkinter as ctk

from controllers.riwayat_controller import RiwayatController
from views.components.toast_notification import tampilkan_toast_error
from utils.format_helper import format_rupiah, format_jumlah
from utils.theme_helper import (
    BG_WINDOW, BG_SURFACE, BG_INPUT, BG_TABLE_ROW_ALT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_PLACEHOLDER,
    ACCENT_PRIMARY, ACCENT_HOVER,
    BTN_SECONDARY_BG,
    COLOR_WARNING, COLOR_DANGER, BORDER_COLOR,
    SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL,
    RADIUS_CARD, RADIUS_BTN, RADIUS_INPUT,
    HEIGHT_INPUT, HEIGHT_BTN_PRIMARY, HEIGHT_BTN_SECONDARY,
    get_font,
)

NAMA_BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


class RiwayatPage(ctk.CTkFrame):
    """
    Halaman Riwayat dengan dua state:
    State A — list card minggu dalam bulan yang dipilih
    State B — detail item belanja untuk satu periode minggu
    """

    def __init__(self, master, koneksi: sqlite3.Connection, navigasi_ke):
        super().__init__(master, fg_color=BG_WINDOW, corner_radius=0)

        self._koneksi  = koneksi
        self._navigasi = navigasi_ke
        self._ctrl     = RiwayatController(koneksi)

        self._bulan_aktif = date.today().month
        self._tahun_aktif = date.today().year

        self._id_periode_aktif: int = 0
        self._data_periode: Optional[dict] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._frame_state_a = self._buat_state_a()
        self._frame_state_b = self._buat_state_b()

        self._tampilkan_state("A")

    # ─── MANAJEMEN STATE ──────────────────────────────────────────────────────

    def _tampilkan_state(self, state: str) -> None:
        if state == "A":
            self._frame_state_b.grid_remove()
            self._frame_state_a.grid(row=0, column=0, sticky="nsew")
            self._muat_state_a()
        else:
            self._frame_state_a.grid_remove()
            self._frame_state_b.grid(row=0, column=0, sticky="nsew")
            self._muat_state_b()

    # =========================================================================
    # STATE A — LIST MINGGU
    # =========================================================================

    def _buat_state_a(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color=BG_WINDOW, corner_radius=0)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Header
        fh = ctk.CTkFrame(frame, fg_color="transparent")
        fh.grid(row=0, column=0, sticky="ew",
                padx=SPACE_XL, pady=(SPACE_XL, SPACE_SM))
        ctk.CTkLabel(fh, text="Riwayat", font=get_font("heading_1"),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(fh, text="Pilih bulan untuk melihat riwayat belanja",
                     font=get_font("small"), text_color=TEXT_SECONDARY,
                     anchor="w").pack(anchor="w", pady=(SPACE_XS, 0))

        # Divider
        ctk.CTkFrame(frame, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=1, column=0, sticky="ew", padx=SPACE_XL)

        # ScrollableFrame untuk seluruh konten bawah
        self._scroll_a = ctk.CTkScrollableFrame(
            frame, fg_color="transparent",
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=ACCENT_PRIMARY)
        self._scroll_a.grid(row=2, column=0, sticky="nsew",
                            padx=SPACE_XL, pady=SPACE_XL)
        self._scroll_a.grid_columnconfigure(0, weight=1)

        # Card filter bulan
        fbar = ctk.CTkFrame(self._scroll_a, fg_color=BG_SURFACE,
                            corner_radius=RADIUS_CARD,
                            border_width=1, border_color=BORDER_COLOR)
        fbar.grid(row=0, column=0, sticky="ew", pady=(0, SPACE_MD))

        ffilter = ctk.CTkFrame(fbar, fg_color="transparent")
        ffilter.grid(row=0, column=0, sticky="ew",
                     padx=SPACE_XL, pady=SPACE_MD)

        self._combo_bulan_a = ctk.CTkComboBox(
            ffilter, values=NAMA_BULAN, font=get_font("body"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            button_color=ACCENT_PRIMARY, button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_SURFACE, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BTN_SECONDARY_BG, text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT,
            width=180, state="readonly",
        )
        self._combo_bulan_a.pack(side="left")

        ctk.CTkButton(
            ffilter, text="Tampilkan", font=get_font("body"),
            fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            height=HEIGHT_BTN_SECONDARY, corner_radius=RADIUS_BTN, width=110,
            command=self._klik_tampilkan,
        ).pack(side="left", padx=(SPACE_SM, 0))

        # Frame tempat card minggu di-render (row 1 ke bawah di scroll_a)
        self._frame_kartu = ctk.CTkFrame(self._scroll_a, fg_color="transparent")
        self._frame_kartu.grid(row=1, column=0, sticky="ew")
        self._frame_kartu.grid_columnconfigure(0, weight=1)

        return frame

    def _muat_state_a(self) -> None:
        self._combo_bulan_a.set(NAMA_BULAN[self._bulan_aktif - 1])
        self._render_kartu()

    def _klik_tampilkan(self) -> None:
        idx = NAMA_BULAN.index(self._combo_bulan_a.get())
        self._bulan_aktif = idx + 1
        self._render_kartu()

    def _render_kartu(self) -> None:
        for widget in self._frame_kartu.winfo_children():
            widget.destroy()

        daftar = self._ctrl.ambil_minggu_per_bulan(self._bulan_aktif, self._tahun_aktif)

        if not daftar:
            ctk.CTkLabel(
                self._frame_kartu,
                text=f"Belum ada data riwayat untuk {NAMA_BULAN[self._bulan_aktif - 1]} {self._tahun_aktif}.",
                font=get_font("body"), text_color=TEXT_SECONDARY
            ).grid(row=0, column=0, pady=SPACE_2XL)
            return

        for idx, data in enumerate(daftar):
            self._buat_kartu_minggu(self._frame_kartu, idx, data)

    def _buat_kartu_minggu(self, parent, idx: int, data: dict) -> None:
        def _fmt(d): return "-".join(reversed(d.split("-")))

        card = ctk.CTkFrame(parent, fg_color=BG_SURFACE,
                            corner_radius=RADIUS_CARD,
                            border_width=1, border_color=BORDER_COLOR)
        card.grid(row=idx, column=0, sticky="ew", pady=(0, SPACE_MD))
        card.grid_columnconfigure(0, weight=1)

        # Judul + rentang tanggal
        fatas = ctk.CTkFrame(card, fg_color="transparent")
        fatas.grid(row=0, column=0, sticky="ew",
                   padx=SPACE_XL, pady=(SPACE_MD, SPACE_XS))
        fatas.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(fatas, text=f"Minggu ke-{data['minggu_ke']}",
                     font=get_font("body_bold"), text_color=TEXT_PRIMARY,
                     anchor="w").grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(fatas,
                     text=f"{_fmt(data['tgl_mulai'])}  –  {_fmt(data['tgl_selesai'])}",
                     font=get_font("period_label"), text_color=TEXT_SECONDARY,
                     anchor="w").grid(row=1, column=0, sticky="w", pady=(SPACE_XS, 0))

        # Total pengeluaran
        ctk.CTkLabel(card,
                     text=f"Total Pengeluaran: {format_rupiah(data['total_pengeluaran'])}",
                     font=get_font("body"), text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=1, column=0, sticky="w",
                            padx=SPACE_XL, pady=(0, SPACE_SM))

        # Divider tipis
        ctk.CTkFrame(card, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=2, column=0, sticky="ew", padx=SPACE_XL)

        # Baris tombol
        ftombol = ctk.CTkFrame(card, fg_color="transparent")
        ftombol.grid(row=3, column=0, sticky="ew",
                     padx=SPACE_XL, pady=(SPACE_SM, SPACE_MD))

        # Export hanya muncul jika ada data (total > 0) — FR-RW State A
        if data["total_pengeluaran"] > 0:
            ctk.CTkButton(
                ftombol, text="Export PDF", font=get_font("small"),
                fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
                text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
                corner_radius=RADIUS_BTN, width=90,
                command=lambda: tampilkan_toast_error(self, "Export tersedia di Tahap 10.")
            ).pack(side="left", padx=(0, SPACE_SM))

            ctk.CTkButton(
                ftombol, text="Export Excel", font=get_font("small"),
                fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
                text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
                corner_radius=RADIUS_BTN, width=95,
                command=lambda: tampilkan_toast_error(self, "Export tersedia di Tahap 10.")
            ).pack(side="left", padx=(0, SPACE_SM))

        # Tombol Detail selalu ada di semua card
        ctk.CTkButton(
            ftombol, text="Detail  ›", font=get_font("body"),
            fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            height=HEIGHT_BTN_SECONDARY, corner_radius=RADIUS_BTN, width=90,
            command=lambda d=data: self._buka_detail(d)
        ).pack(side="right")

    def _buka_detail(self, data: dict) -> None:
        self._id_periode_aktif = data["id_periode"]
        self._tampilkan_state("B")

    # =========================================================================
    # STATE B — DETAIL MINGGU
    # =========================================================================

    def _buat_state_b(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color=BG_WINDOW, corner_radius=0)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Header
        fh = ctk.CTkFrame(frame, fg_color="transparent")
        fh.grid(row=0, column=0, sticky="ew",
                padx=SPACE_XL, pady=(SPACE_XL, SPACE_SM))
        fh.grid_columnconfigure(0, weight=1)

        fj = ctk.CTkFrame(fh, fg_color="transparent")
        fj.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(fj, text="Riwayat", font=get_font("heading_1"),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        self._label_periode_b = ctk.CTkLabel(
            fj, text="", font=get_font("period_label"),
            text_color=TEXT_SECONDARY, anchor="w")
        self._label_periode_b.pack(anchor="w")

        ctk.CTkButton(
            fh, text="← Kembali", font=get_font("body"),
            fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            command=lambda: self._tampilkan_state("A"),
        ).grid(row=0, column=1, sticky="e")

        # Divider
        ctk.CTkFrame(frame, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=1, column=0, sticky="ew", padx=SPACE_XL)

        # Konten utama
        fi = ctk.CTkFrame(frame, fg_color="transparent")
        fi.grid(row=2, column=0, sticky="nsew", padx=SPACE_XL, pady=SPACE_XL)
        fi.grid_columnconfigure(0, weight=1)
        fi.grid_rowconfigure(0, weight=0)
        fi.grid_rowconfigure(1, weight=1)

        self._buat_stat_cards(fi)
        self._buat_tabel_detail(fi)

        return frame

    # ── STAT CARDS ────────────────────────────────────────────────────────────

    def _buat_stat_cards(self, parent) -> None:
        fstat = ctk.CTkFrame(parent, fg_color="transparent")
        fstat.grid(row=0, column=0, sticky="ew", pady=(0, SPACE_MD))
        fstat.grid_columnconfigure(0, weight=1)
        fstat.grid_columnconfigure(1, weight=1)
        fstat.grid_columnconfigure(2, weight=1)

        def _buat_card(col, label_teks, pad_x):
            card = ctk.CTkFrame(fstat, fg_color=BG_SURFACE, corner_radius=RADIUS_CARD,
                                border_width=1, border_color=BORDER_COLOR)
            card.grid(row=0, column=col, sticky="nsew", padx=pad_x)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=label_teks, font=get_font("small"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w",
                                padx=SPACE_XL, pady=(SPACE_MD, SPACE_XS))
            nilai_lbl = ctk.CTkLabel(card, text="Rp0", font=get_font("currency_lg"),
                                     text_color=TEXT_PRIMARY, anchor="w")
            nilai_lbl.grid(row=1, column=0, sticky="w",
                           padx=SPACE_XL, pady=(0, SPACE_MD))
            return nilai_lbl

        self._label_budget   = _buat_card(0, "Budget",             (0, SPACE_SM))
        self._label_total_b  = _buat_card(1, "Total Pengeluaran",  (SPACE_SM, SPACE_SM))
        self._label_sisa     = _buat_card(2, "Sisa Budget",        (SPACE_SM, 0))

    # ── TABEL DETAIL ──────────────────────────────────────────────────────────

    def _buat_tabel_detail(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=BG_SURFACE,
                            corner_radius=RADIUS_CARD,
                            border_width=1, border_color=BORDER_COLOR)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        # Filter bar: search + kategori + export
        fbar = ctk.CTkFrame(card, fg_color="transparent")
        fbar.grid(row=0, column=0, sticky="ew",
                  padx=SPACE_MD, pady=(SPACE_MD, SPACE_SM))
        fbar.grid_columnconfigure(0, weight=1)

        self._entry_cari_b = ctk.CTkEntry(
            fbar, placeholder_text="🔍  Cari nama barang...",
            font=get_font("body"), fg_color=BG_INPUT, border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_PLACEHOLDER,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT)
        self._entry_cari_b.grid(row=0, column=0, sticky="ew",
                                padx=(SPACE_SM, SPACE_SM))
        self._entry_cari_b.bind("<KeyRelease>", lambda e: self._render_tabel_b())

        self._combo_kat_b = ctk.CTkComboBox(
            fbar, values=["Semua Kategori"], font=get_font("body"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            button_color=ACCENT_PRIMARY, button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_SURFACE, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BTN_SECONDARY_BG, text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT,
            width=180, state="readonly",
            command=lambda _: self._render_tabel_b())
        self._combo_kat_b.grid(row=0, column=1, padx=(0, SPACE_SM))

        fe = ctk.CTkFrame(fbar, fg_color="transparent")
        fe.grid(row=0, column=2)
        ctk.CTkButton(fe, text="Export PDF", font=get_font("small"),
                      fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
                      text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
                      corner_radius=RADIUS_BTN, width=90,
                      command=self._export_pdf
                      ).pack(side="left", padx=(0, SPACE_SM))
        ctk.CTkButton(fe, text="Export Excel", font=get_font("small"),
                      fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
                      text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
                      corner_radius=RADIUS_BTN, width=95,
                      command=self._export_excel
                      ).pack(side="left")

        # Definisi kolom tabel — 6 kolom, tanpa Aksi (read-only)
        # col: 0=No(40) 1=Nama(w4) 2=Jumlah(w1) 3=Satuan(w1) 4=HargaSat(w2) 5=Total(w2)
        COL_NO = 40
        COL_W  = [4, 1, 1, 2, 2]
        _PX    = 10

        def _set_kolom(f):
            f.grid_columnconfigure(0, minsize=COL_NO, weight=0)
            for i, w in enumerate(COL_W, start=1):
                f.grid_columnconfigure(i, weight=w)

        self._frame_baris_b = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=ACCENT_PRIMARY)
        self._frame_baris_b.grid(row=1, column=0, sticky="nsew",
                                  padx=SPACE_MD, pady=(0, 0))
        _set_kolom(self._frame_baris_b)

        # Header kolom
        HDR = [("No","center"), ("Nama Barang","center"), ("Jumlah","center"),
               ("Satuan","center"), ("Harga Satuan","center"), ("Total","center")]
        self._widget_header_b = []
        for col, (teks, anc) in enumerate(HDR):
            lbl = ctk.CTkLabel(self._frame_baris_b, text=teks,
                               font=get_font("body_bold"), text_color=ACCENT_PRIMARY,
                               anchor=anc, fg_color="transparent", padx=_PX)
            lbl.grid(row=0, column=col, sticky="ew", pady=(SPACE_SM, SPACE_XS))
            self._widget_header_b.append(lbl)

        sep = ctk.CTkFrame(self._frame_baris_b, fg_color=BORDER_COLOR,
                           height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(0, SPACE_XS))
        self._widget_header_b.append(sep)

        self._px_cell_b = _PX

        # Garis + footer total
        ctk.CTkFrame(card, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=2, column=0, sticky="ew", padx=SPACE_MD)

        ff = ctk.CTkFrame(card, fg_color="transparent")
        ff.grid(row=3, column=0, sticky="ew",
                padx=SPACE_MD, pady=(SPACE_XS, SPACE_MD))
        ff.grid_columnconfigure(0, weight=1)
        self._label_footer_total = ctk.CTkLabel(
            ff, text="Total: Rp0", font=get_font("body_bold"),
            text_color=TEXT_PRIMARY, anchor="e")
        self._label_footer_total.grid(row=0, column=0, sticky="e", padx=SPACE_MD)

    # ── MUAT & RENDER STATE B ─────────────────────────────────────────────────

    def _muat_state_b(self) -> None:
        self._data_periode = self._ctrl.ambil_data_periode(self._id_periode_aktif)
        if self._data_periode is None:
            return

        def _fmt(d): return "-".join(reversed(d.split("-")))
        dp = self._data_periode

        # Sub-label header: Bulan · Minggu ke-N · rentang tanggal
        self._label_periode_b.configure(
            text=f"{NAMA_BULAN[dp['bulan'] - 1]}  ·  Minggu ke-{dp['minggu_ke']}  ·  "
                 f"{_fmt(dp['tgl_mulai'])}  –  {_fmt(dp['tgl_selesai'])}")

        # Stat cards — selalu total keseluruhan, tidak berubah saat filter aktif
        self._label_budget.configure(text=format_rupiah(dp["nominal_budget"]))
        self._label_total_b.configure(text=format_rupiah(dp["total_pengeluaran"]))

        # Warna sisa budget sesuai threshold 20% (FR-DB-3)
        sisa  = dp["sisa_budget"]
        batas = dp["nominal_budget"] * 0.20
        if sisa < 0:
            warna_sisa = COLOR_DANGER
        elif sisa < batas:
            warna_sisa = COLOR_WARNING
        else:
            warna_sisa = TEXT_PRIMARY
        self._label_sisa.configure(text=format_rupiah(sisa), text_color=warna_sisa)

        # Isi dropdown kategori dan reset filter
        self._muat_dropdown_kategori()
        self._entry_cari_b.delete(0, "end")
        self._combo_kat_b.set("Semua Kategori")
        self._render_tabel_b()

    def _muat_dropdown_kategori(self) -> None:
        daftar = self._ctrl.ambil_daftar_kategori()
        nama   = [k["nama_kategori"] for k in daftar]
        self._combo_kat_b.configure(values=["Semua Kategori"] + nama)
        self._combo_kat_b.set("Semua Kategori")
        self._daftar_kategori = daftar

    def _ambil_id_kategori_terpilih(self) -> int:
        nama = self._combo_kat_b.get()
        if nama == "Semua Kategori":
            return 0
        if not hasattr(self, "_daftar_kategori"):
            return 0
        for kat in self._daftar_kategori:
            if kat["nama_kategori"] == nama:
                return kat["id_kategori"]
        return 0

    def _render_tabel_b(self) -> None:
        """
        Hapus baris data (row >= 2) dan render ulang sesuai filter aktif.
        Footer total mengikuti item yang tampil (FR-RW-4).
        Export selalu mengambil semua data — tidak terpengaruh filter (FR-RW-5).
        """
        header_ids = {id(w) for w in self._widget_header_b}
        for widget in self._frame_baris_b.winfo_children():
            if id(widget) not in header_ids:
                widget.destroy()

        kata_kunci  = self._entry_cari_b.get()
        id_kategori = self._ambil_id_kategori_terpilih()
        daftar      = self._ctrl.ambil_daftar_item(
            self._id_periode_aktif, kata_kunci, id_kategori)

        _PX = self._px_cell_b

        if not daftar:
            pesan = ("Tidak ada item yang cocok dengan filter ini."
                     if kata_kunci or id_kategori
                     else "Tidak ada item belanja pada periode ini.")
            ctk.CTkLabel(
                self._frame_baris_b, text=pesan,
                font=get_font("body"), text_color=TEXT_SECONDARY
            ).grid(row=2, column=0, columnspan=6, pady=SPACE_2XL)
            self._label_footer_total.configure(text="Total: Rp0")
            return

        for idx, item in enumerate(daftar):
            baris_row = idx + 2
            warna     = BG_TABLE_ROW_ALT if idx % 2 == 1 else "transparent"

            # Kolom 0: nomor urut
            ctk.CTkLabel(self._frame_baris_b, text=str(idx + 1),
                         font=get_font("body"), text_color=TEXT_PRIMARY,
                         anchor="center", fg_color=warna, padx=_PX
                         ).grid(row=baris_row, column=0, sticky="ew", pady=SPACE_SM)

            # Kolom 1–5: data item (read-only, tanpa kolom Aksi)
            for col, (teks, anc) in enumerate([
                (item["nama_barang"],                  "w"),
                (format_jumlah(item["jumlah_barang"]), "e"),
                (item["nama_satuan"],                  "center"),
                (format_rupiah(item["harga_satuan"]),  "e"),
                (format_rupiah(item["harga_total"]),   "e"),
            ], start=1):
                ctk.CTkLabel(self._frame_baris_b, text=teks,
                             font=get_font("body"), text_color=TEXT_PRIMARY,
                             anchor=anc, fg_color=warna, padx=_PX
                             ).grid(row=baris_row, column=col, sticky="ew",
                                    pady=SPACE_SM)

        # Footer total mengikuti filter yang aktif
        total_filter = sum(item["harga_total"] for item in daftar)
        self._label_footer_total.configure(
            text=f"Total: {format_rupiah(total_filter)}")

    # ── EXPORT (stub — diimplementasi Tahap 10) ───────────────────────────────

    def _export_pdf(self) -> None:
        tampilkan_toast_error(self, "Export PDF tersedia di Tahap 10.")

    def _export_excel(self) -> None:
        tampilkan_toast_error(self, "Export Excel tersedia di Tahap 10.")