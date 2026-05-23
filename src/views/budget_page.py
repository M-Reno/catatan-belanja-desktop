# views/budget_page.py
"""
Halaman Budget — Form pembuatan budget mingguan + tabel riwayat
Sesuai PRD §4.2, Design System §4.2, dan Tahap 6

Layout:
  - Form card di tengah (max 520px), tanggal mulai & selesai berdampingan
  - Tabel riwayat penuh lebar di bawah, tidak terpotong
"""

import sqlite3
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime

from controllers.budget_controller import BudgetController
from views.components.toast_notification import tampilkan_toast
from utils.theme_helper import (
    BG_WINDOW, BG_SURFACE, BG_INPUT, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER_COLOR, ACCENT_PRIMARY, ACCENT_HOVER, COLOR_DANGER,
    BG_TABLE_ROW_ALT,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL, SPACE_3XL,
    RADIUS_CARD, HEIGHT_INPUT, HEIGHT_BTN_PRIMARY, HEIGHT_TABLE_ROW,
    get_font
)


class BudgetPage(ctk.CTkFrame):
    def __init__(self, master, koneksi: sqlite3.Connection, navigasi_ke):
        super().__init__(master, fg_color=BG_WINDOW, corner_radius=0)

        self._koneksi = koneksi
        self._navigasi = navigasi_ke
        self._controller = BudgetController(koneksi)

        # Grid utama: baris 0 = header, baris 1 = konten scroll
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._buat_header()
        self._buat_konten()

    # ------------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------------

    def _buat_header(self):
        """Header halaman dengan judul dan garis pemisah."""
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.grid(row=0, column=0, sticky="ew",
                          padx=SPACE_XL, pady=(SPACE_XL, 0))
        frame_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_header,
            text="Budget",
            font=get_font("heading_1"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=0, column=0, sticky="w")

        # Garis tipis di bawah header
        ctk.CTkFrame(
            frame_header,
            fg_color=BORDER_COLOR,
            height=1,
            corner_radius=0
        ).grid(row=1, column=0, sticky="ew", pady=(SPACE_SM, 0))

    # ------------------------------------------------------------------
    # KONTEN UTAMA (scrollable)
    # ------------------------------------------------------------------

    def _buat_konten(self):
        """Area scroll yang memuat form + riwayat."""
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        scroll.grid(row=1, column=0, sticky="nsew",
                    padx=SPACE_XL, pady=SPACE_XL)
        # Satu kolom penuh; form akan di-center via inner frame
        scroll.grid_columnconfigure(0, weight=1)

        self._scroll = scroll

        self._buat_form_card()
        self._buat_riwayat_section()

    # ------------------------------------------------------------------
    # FORM CARD
    # ------------------------------------------------------------------

    def _buat_form_card(self):
        """Card form pembuatan budget — terpusat, lebar maks 520 px."""

        # Wrapper untuk centering horizontal
        wrapper = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="ew",
                     pady=(0, SPACE_3XL))
        # Kolom 0 & 2 elastis → card (kolom 1) tetap di tengah
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=0, minsize=520)
        wrapper.grid_columnconfigure(2, weight=1)

        card = ctk.CTkFrame(
            wrapper,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=BORDER_COLOR
        )
        card.grid(row=0, column=1, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        # ── Judul form ──────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="Buat Budget Mingguan",
            font=get_font("heading_2"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="w",
               padx=SPACE_XL, pady=(SPACE_XL, SPACE_LG))

        # ── Baris tanggal: Mulai (kiri) | Selesai (kanan) ───────────
        # Label Tanggal Mulai
        ctk.CTkLabel(
            card,
            text="Tanggal Mulai",
            font=get_font("body"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=1, column=0, sticky="w",
               padx=(SPACE_XL, SPACE_SM), pady=(0, SPACE_SM))

        # Label Tanggal Selesai
        ctk.CTkLabel(
            card,
            text="Tanggal Selesai",
            font=get_font("body"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=1, column=1, sticky="w",
               padx=(SPACE_SM, SPACE_XL), pady=(0, SPACE_SM))

        # DateEntry Tanggal Mulai
        aksen = ACCENT_PRIMARY[0] if isinstance(ACCENT_PRIMARY, list) else ACCENT_PRIMARY
        self.entry_tgl_mulai = DateEntry(
            card,
            width=18,
            background=aksen,
            foreground="white",
            borderwidth=1,
            date_pattern="dd-mm-yyyy",
            font=get_font("body")
        )
        self.entry_tgl_mulai.grid(row=2, column=0, sticky="ew",
                                   padx=(SPACE_XL, SPACE_SM), pady=(0, SPACE_SM))
        self.entry_tgl_mulai.bind("<<DateEntrySelected>>",
                                   self._auto_isi_tanggal_selesai)

        # DateEntry Tanggal Selesai
        self.entry_tgl_selesai = DateEntry(
            card,
            width=18,
            background=aksen,
            foreground="white",
            borderwidth=1,
            date_pattern="dd-mm-yyyy",
            font=get_font("body")
        )
        self.entry_tgl_selesai.grid(row=2, column=1, sticky="ew",
                                     padx=(SPACE_SM, SPACE_XL), pady=(0, SPACE_SM))

        # Label error tanggal (span 2 kolom)
        self.label_error_tgl = ctk.CTkLabel(
            card,
            text="",
            font=get_font("small"),
            text_color=COLOR_DANGER,
            anchor="w"
        )
        self.label_error_tgl.grid(row=3, column=0, columnspan=2, sticky="w",
                                   padx=SPACE_XL, pady=(0, SPACE_SM))

        # ── Nominal Budget ───────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="Nominal Budget",
            font=get_font("body"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=4, column=0, columnspan=2, sticky="w",
               padx=SPACE_XL, pady=(SPACE_MD, SPACE_SM))

        frame_currency = ctk.CTkFrame(card, fg_color="transparent")
        frame_currency.grid(row=5, column=0, columnspan=2, sticky="ew",
                            padx=SPACE_XL, pady=(0, SPACE_SM))
        frame_currency.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_currency,
            text="Rp",
            font=get_font("body"),
            text_color=TEXT_PRIMARY
        ).grid(row=0, column=0, padx=(0, SPACE_SM))

        self.entry_nominal = ctk.CTkEntry(
            frame_currency,
            fg_color=BG_INPUT,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_PRIMARY,
            font=get_font("body"),
            height=HEIGHT_INPUT
        )
        self.entry_nominal.grid(row=0, column=1, sticky="ew")
        self.entry_nominal.bind("<FocusOut>", self._format_nominal)

        self.label_error_nominal = ctk.CTkLabel(
            card,
            text="",
            font=get_font("small"),
            text_color=COLOR_DANGER,
            anchor="w"
        )
        self.label_error_nominal.grid(row=6, column=0, columnspan=2, sticky="w",
                                      padx=SPACE_XL, pady=(0, SPACE_SM))

        # ── Tombol Simpan ────────────────────────────────────────────
        ctk.CTkButton(
            card,
            text="Simpan",
            font=get_font("body_bold"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            height=HEIGHT_BTN_PRIMARY,
            command=self._handle_simpan
        ).grid(row=7, column=0, columnspan=2, sticky="ew",
               padx=SPACE_XL, pady=(SPACE_LG, SPACE_XL))

    # ------------------------------------------------------------------
    # RIWAYAT BUDGET
    # ------------------------------------------------------------------

    def _buat_riwayat_section(self):
        """Tabel riwayat budget (FR-BG-3) — penuh lebar, tidak terpotong."""

        # Judul section
        ctk.CTkLabel(
            self._scroll,
            text="Riwayat Budget",
            font=get_font("heading_2"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=1, column=0, sticky="w",
               pady=(0, SPACE_MD))

        # Card tabel — stretch penuh
        card_tabel = ctk.CTkFrame(
            self._scroll,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=BORDER_COLOR
        )
        card_tabel.grid(row=2, column=0, sticky="nsew",
                        pady=(0, SPACE_XL))

        # Tiga kolom: Minggu ke (fixed) | Tanggal (expand) | Budget (fixed)
        card_tabel.grid_columnconfigure(0, weight=0, minsize=110)
        card_tabel.grid_columnconfigure(1, weight=1)
        card_tabel.grid_columnconfigure(2, weight=0, minsize=140)

        # ── Header kolom ─────────────────────────────────────────────
        header_data = [("Minggu ke", "center"), ("Tanggal", "w"), ("Budget", "e")]
        for i, (teks, align) in enumerate(header_data):
            pad_x = (SPACE_XL, SPACE_MD) if i == 0 else \
                    (SPACE_MD, SPACE_XL) if i == 2 else \
                    (SPACE_MD, SPACE_MD)
            ctk.CTkLabel(
                card_tabel,
                text=teks,
                font=get_font("body_bold"),
                text_color=TEXT_PRIMARY,
                anchor=align
            ).grid(row=0, column=i, sticky="ew",
                   padx=pad_x, pady=(SPACE_LG, SPACE_SM))

        # Garis pemisah header
        ctk.CTkFrame(
            card_tabel,
            fg_color=BORDER_COLOR,
            height=1,
            corner_radius=0
        ).grid(row=1, column=0, columnspan=3, sticky="ew",
               padx=SPACE_MD, pady=0)

        # Container baris data — kolom mengikuti card_tabel
        self.frame_baris = ctk.CTkFrame(card_tabel, fg_color="transparent")
        self.frame_baris.grid(row=2, column=0, columnspan=3,
                              sticky="nsew", pady=(0, SPACE_SM))
        self.frame_baris.grid_columnconfigure(0, weight=0, minsize=110)
        self.frame_baris.grid_columnconfigure(1, weight=1)
        self.frame_baris.grid_columnconfigure(2, weight=0, minsize=140)

        self._muat_riwayat()

    def _muat_riwayat(self):
        """Ambil data riwayat dari controller dan render ke tabel."""
        # Bersihkan baris lama
        for w in self.frame_baris.winfo_children():
            w.destroy()

        riwayat = self._controller.muat_riwayat_budget()

        if not riwayat:
            ctk.CTkLabel(
                self.frame_baris,
                text="Belum ada riwayat budget.",
                font=get_font("body"),
                text_color=TEXT_SECONDARY
            ).grid(row=0, column=0, columnspan=3, pady=SPACE_2XL)
            return

        for idx, row in enumerate(riwayat):
            # Warna baris alternating
            warna_baris = "transparent" if idx % 2 == 0 else BG_TABLE_ROW_ALT

            # Baris wrapper (span 3 kolom agar warna penuh)
            baris_frame = ctk.CTkFrame(
                self.frame_baris,
                fg_color=warna_baris,
                corner_radius=0,
                height=HEIGHT_TABLE_ROW
            )
            baris_frame.grid(row=idx, column=0, columnspan=3,
                             sticky="nsew")
            baris_frame.grid_columnconfigure(0, weight=0, minsize=110)
            baris_frame.grid_columnconfigure(1, weight=1)
            baris_frame.grid_columnconfigure(2, weight=0, minsize=140)
            baris_frame.grid_propagate(False)

            # Kolom Minggu ke
            ctk.CTkLabel(
                baris_frame,
                text=str(row["minggu_ke"]),
                font=get_font("body"),
                text_color=TEXT_PRIMARY,
                anchor="center"
            ).grid(row=0, column=0, sticky="nsew",
                   padx=(SPACE_XL, SPACE_MD))

            # Kolom Tanggal
            ctk.CTkLabel(
                baris_frame,
                text=row["tanggal"],
                font=get_font("body"),
                text_color=TEXT_PRIMARY,
                anchor="w"
            ).grid(row=0, column=1, sticky="nsew",
                   padx=SPACE_MD)

            # Kolom Budget
            ctk.CTkLabel(
                baris_frame,
                text=row["nominal"],
                font=get_font("currency_sm"),
                text_color=TEXT_PRIMARY,
                anchor="e"
            ).grid(row=0, column=2, sticky="nsew",
                   padx=(SPACE_MD, SPACE_XL))

    # ------------------------------------------------------------------
    # EVENT HANDLERS
    # ------------------------------------------------------------------

    def _auto_isi_tanggal_selesai(self, event=None):
        """FR-BG-4: Otomatis isi tanggal selesai = tanggal mulai + 6 hari."""
        tgl_mulai_str = self.entry_tgl_mulai.get()
        tgl_selesai_str = self._controller.hitung_tanggal_selesai(tgl_mulai_str)
        if tgl_selesai_str:
            try:
                sep = "-" if "-" in tgl_selesai_str else "/"
                d, m, y = tgl_selesai_str.split(sep)
                self.entry_tgl_selesai.set_date(datetime(int(y), int(m), int(d)))
            except Exception:
                pass

    def _format_nominal(self, event=None):
        """Format nominal dengan titik ribuan saat focus out."""
        try:
            nilai_str = self.entry_nominal.get().replace(".", "").replace(",", "").strip()
            if not nilai_str:
                return
            nilai = int(float(nilai_str))
            self.entry_nominal.delete(0, "end")
            self.entry_nominal.insert(0, f"{nilai:,}".replace(",", "."))
        except Exception:
            pass

    def _reset_error_labels(self):
        """Sembunyikan semua label error."""
        self.label_error_tgl.configure(text="")
        self.label_error_nominal.configure(text="")

    def _handle_simpan(self):
        """Validasi dan simpan budget baru."""
        self._reset_error_labels()

        tgl_mulai_str = self.entry_tgl_mulai.get()
        tgl_selesai_str = self.entry_tgl_selesai.get()

        # Tambahkan prefix Rp agar konsisten dengan controller
        nominal_str = self.entry_nominal.get()
        if nominal_str and not nominal_str.startswith("Rp"):
            nominal_str = "Rp" + nominal_str

        sukses, pesan = self._controller.simpan_budget_baru(
            tgl_mulai_str, tgl_selesai_str, nominal_str
        )

        if not sukses:
            # Arahkan error ke label yang sesuai
            if "nominal" in pesan.lower():
                self.label_error_nominal.configure(text=pesan)
            else:
                self.label_error_tgl.configure(text=pesan)
            return

        # Berhasil: toast → reset form → update tabel → redirect
        tampilkan_toast(self.master, pesan, tipe="sukses")

        self.entry_tgl_mulai.set_date(datetime.now())
        self.entry_tgl_selesai.set_date(datetime.now())
        self.entry_nominal.delete(0, "end")

        self._muat_riwayat()

        # FR-BG-5: pindah ke Dashboard setelah 800 ms
        self.after(800, lambda: self._navigasi("dashboard"))