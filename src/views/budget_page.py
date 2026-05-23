# views/budget_page.py
"""
Halaman Budget — Form pembuatan budget mingguan + tabel riwayat
Sesuai PRD §4.2, Design System §4.2
"""

import sqlite3
import calendar
import customtkinter as ctk
from datetime import date, timedelta

from controllers.budget_controller import BudgetController
from views.components.toast_notification import tampilkan_toast
from utils.theme_helper import (
    BG_WINDOW, BG_SURFACE, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER_COLOR, DIVIDER_COLOR,
    ACCENT_PRIMARY, ACCENT_HOVER, COLOR_DANGER, COLOR_WARNING,
    BG_TABLE_ROW_ALT,
    BTN_SECONDARY_BG,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL, SPACE_3XL,
    RADIUS_CARD, RADIUS_BTN, RADIUS_INPUT, RADIUS_DIALOG,
    HEIGHT_INPUT, HEIGHT_BTN_PRIMARY, HEIGHT_BTN_SECONDARY, HEIGHT_TABLE_ROW,
    get_font
)


def _c(token):
    """Ambil warna sesuai mode aktif saat ini. Selalu dipanggil saat dibutuhkan, bukan saat init."""
    if isinstance(token, (list, tuple)):
        return token[1] if ctk.get_appearance_mode() == "Dark" else token[0]
    return token


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CALENDAR POPUP
# ─────────────────────────────────────────────────────────────────────────────

class _CustomCalendar(ctk.CTkToplevel):
    """Popup kalender custom — warna selalu sinkron dengan mode aktif."""

    NAMA_HARI  = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    NAMA_BULAN = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    # Indeks hari libur (Sabtu=5, Minggu=6) dalam list calendar.monthcalendar
    HARI_LIBUR = {5, 6}

    def __init__(self, master, tanggal_awal: date, callback):
        super().__init__(master)

        self._callback      = callback
        self._tampil_tahun  = tanggal_awal.year
        self._tampil_bulan  = tanggal_awal.month
        self._terpilih      = tanggal_awal

        self.title("")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.overrideredirect(True)
        self.after(10, self._posisikan)

        self._buat_ui()
        self._render_kalender()

    def _posisikan(self):
        try:
            mx = self.master.winfo_rootx()
            my = self.master.winfo_rooty() + self.master.winfo_height() + 4
            self.geometry(f"+{mx}+{my}")
        except Exception:
            pass

    def _buat_ui(self):
        self._container = ctk.CTkFrame(
            self,
            fg_color=_c(BG_SURFACE),
            corner_radius=RADIUS_DIALOG,
            border_width=1,
            border_color=_c(BORDER_COLOR)
        )
        self._container.pack(padx=0, pady=0)

        # Header navigasi bulan
        header = ctk.CTkFrame(self._container, fg_color="transparent")
        header.pack(fill="x", padx=SPACE_MD, pady=(SPACE_MD, SPACE_SM))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            header, text="‹", width=32, height=32,
            corner_radius=RADIUS_BTN,
            fg_color=_c(BTN_SECONDARY_BG), hover_color=_c(BORDER_COLOR),
            text_color=_c(TEXT_PRIMARY), font=get_font("body_bold"),
            command=self._bulan_sebelumnya
        ).grid(row=0, column=0, sticky="w")

        self._label_bulan_tahun = ctk.CTkLabel(
            header, text="",
            font=get_font("body_bold"), text_color=_c(TEXT_PRIMARY)
        )
        self._label_bulan_tahun.grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            header, text="›", width=32, height=32,
            corner_radius=RADIUS_BTN,
            fg_color=_c(BTN_SECONDARY_BG), hover_color=_c(BORDER_COLOR),
            text_color=_c(TEXT_PRIMARY), font=get_font("body_bold"),
            command=self._bulan_berikutnya
        ).grid(row=0, column=2, sticky="e")

        # Divider
        ctk.CTkFrame(
            self._container, fg_color=_c(DIVIDER_COLOR), height=1, corner_radius=0
        ).pack(fill="x", padx=SPACE_MD, pady=(0, SPACE_SM))

        # Header nama hari
        frame_nama_hari = ctk.CTkFrame(self._container, fg_color="transparent")
        frame_nama_hari.pack(fill="x", padx=SPACE_MD)
        for i, nama in enumerate(self.NAMA_HARI):
            # Sabtu (5) dan Minggu (6) merah
            warna = _c(COLOR_DANGER) if i in self.HARI_LIBUR else _c(TEXT_SECONDARY)
            ctk.CTkLabel(
                frame_nama_hari, text=nama, width=36,
                font=get_font("small"), text_color=warna, anchor="center"
            ).grid(row=0, column=i, padx=1)

        # Grid tanggal — di-rebuild setiap navigasi
        self._frame_grid = ctk.CTkFrame(self._container, fg_color="transparent")
        self._frame_grid.pack(fill="x", padx=SPACE_MD, pady=(SPACE_SM, SPACE_MD))

        # Footer: tombol Hari Ini
        ctk.CTkFrame(
            self._container, fg_color=_c(DIVIDER_COLOR), height=1, corner_radius=0
        ).pack(fill="x", padx=SPACE_MD, pady=(0, SPACE_SM))

        ctk.CTkButton(
            self._container, text="Hari Ini",
            height=HEIGHT_BTN_SECONDARY, corner_radius=RADIUS_BTN,
            fg_color=_c(ACCENT_PRIMARY), hover_color=_c(ACCENT_HOVER),
            text_color="#FFFFFF", font=get_font("small"),
            command=self._pilih_hari_ini
        ).pack(padx=SPACE_MD, pady=(0, SPACE_MD), fill="x")

    def _render_kalender(self):
        for w in self._frame_grid.winfo_children():
            w.destroy()

        self._label_bulan_tahun.configure(
            text=f"{self.NAMA_BULAN[self._tampil_bulan - 1]} {self._tampil_tahun}"
        )

        cal      = calendar.monthcalendar(self._tampil_tahun, self._tampil_bulan)
        hari_ini = date.today()

        for minggu_idx, minggu in enumerate(cal):
            for hari_idx, tgl in enumerate(minggu):
                if tgl == 0:
                    ctk.CTkFrame(
                        self._frame_grid, width=36, height=32, fg_color="transparent"
                    ).grid(row=minggu_idx, column=hari_idx, padx=1, pady=1)
                    continue

                tanggal_ini     = date(self._tampil_tahun, self._tampil_bulan, tgl)
                adalah_terpilih = tanggal_ini == self._terpilih
                adalah_hari_ini = tanggal_ini == hari_ini
                adalah_libur    = hari_idx in self.HARI_LIBUR

                if adalah_terpilih:
                    fg    = _c(ACCENT_PRIMARY)
                    hover = _c(ACCENT_HOVER)
                    txt   = "#FFFFFF"
                    fw    = "bold"
                elif adalah_hari_ini:
                    fg    = _c(BTN_SECONDARY_BG)
                    hover = _c(BORDER_COLOR)
                    # Hari ini AND hari libur → warna libur lebih kuat
                    txt   = _c(COLOR_DANGER) if adalah_libur else _c(ACCENT_PRIMARY)
                    fw    = "bold"
                else:
                    fg    = "transparent"
                    hover = _c(BTN_SECONDARY_BG)
                    txt   = _c(COLOR_DANGER) if adalah_libur else _c(TEXT_PRIMARY)
                    fw    = "normal"

                ctk.CTkButton(
                    self._frame_grid,
                    text=str(tgl), width=36, height=32,
                    corner_radius=RADIUS_BTN,
                    fg_color=fg, hover_color=hover, text_color=txt,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight=fw),
                    command=lambda d=tanggal_ini: self._pilih_tanggal(d)
                ).grid(row=minggu_idx, column=hari_idx, padx=1, pady=1)

    def _bulan_sebelumnya(self):
        if self._tampil_bulan == 1:
            self._tampil_bulan = 12; self._tampil_tahun -= 1
        else:
            self._tampil_bulan -= 1
        self._render_kalender()

    def _bulan_berikutnya(self):
        if self._tampil_bulan == 12:
            self._tampil_bulan = 1; self._tampil_tahun += 1
        else:
            self._tampil_bulan += 1
        self._render_kalender()

    def _pilih_hari_ini(self):
        self._pilih_tanggal(date.today())

    def _pilih_tanggal(self, tanggal: date):
        self._callback(tanggal)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# DATE INPUT WIDGET
# ─────────────────────────────────────────────────────────────────────────────

class _DateInputWidget(ctk.CTkFrame):
    """
    Kotak input tanggal — klik membuka _CustomCalendar.
    readonly=True: hanya display, tidak bisa diklik.
    Warna selalu dibaca saat event terjadi (bukan saat init) → dark mode aman.
    """

    def __init__(self, master, tanggal_awal: date, on_change=None, readonly: bool = False):
        super().__init__(master, fg_color="transparent")
        self._tanggal   = tanggal_awal
        self._on_change = on_change
        self._readonly  = readonly
        self._popup     = None
        self.grid_columnconfigure(0, weight=1)
        self._buat_ui()

    def _buat_ui(self):
        self._frame_input = ctk.CTkFrame(
            self,
            fg_color=_c(BG_INPUT),
            corner_radius=RADIUS_INPUT,
            border_width=1,
            border_color=_c(BORDER_COLOR),   # warna border sesuai mode saat ini
            height=HEIGHT_INPUT
        )
        self._frame_input.grid(row=0, column=0, sticky="ew")
        self._frame_input.grid_columnconfigure(0, weight=1)
        self._frame_input.grid_propagate(False)

        txt_color = _c(TEXT_PRIMARY) if not self._readonly else _c(TEXT_SECONDARY)
        self._label_tgl = ctk.CTkLabel(
            self._frame_input,
            text=self._fmt(),
            font=get_font("body"),
            text_color=txt_color,
            anchor="w"
        )
        self._label_tgl.grid(row=0, column=0, sticky="ew",
                              padx=(SPACE_MD, SPACE_SM))

        if not self._readonly:
            self._ikon = ctk.CTkLabel(
                self._frame_input, text="📅",
                font=ctk.CTkFont(size=14),
                text_color=_c(ACCENT_PRIMARY),
                cursor="hand2", anchor="center", width=30
            )
            self._ikon.grid(row=0, column=1, sticky="e", padx=(0, SPACE_SM))

            for w in (self._frame_input, self._label_tgl, self._ikon):
                w.bind("<Button-1>", self._buka_popup)
                w.bind("<Enter>",    self._on_enter)
                w.bind("<Leave>",    self._on_leave)
        else:
            ctk.CTkLabel(
                self._frame_input, text="🔒",
                font=ctk.CTkFont(size=11),
                text_color=_c(TEXT_SECONDARY),
                anchor="center", width=26
            ).grid(row=0, column=1, sticky="e", padx=(0, SPACE_SM))

    def _on_enter(self, _=None):
        self._frame_input.configure(border_color=_c(ACCENT_PRIMARY))

    def _on_leave(self, _=None):
        self._frame_input.configure(border_color=_c(BORDER_COLOR))

    def _buka_popup(self, _=None):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy(); return
        self._popup = _CustomCalendar(
            self._frame_input, tanggal_awal=self._tanggal,
            callback=self._terima_tanggal
        )

    def _terima_tanggal(self, tanggal: date):
        self._tanggal = tanggal
        self._label_tgl.configure(text=self._fmt())
        if self._on_change:
            self._on_change(tanggal)

    def _fmt(self) -> str:
        return self._tanggal.strftime("%d-%m-%Y")

    def get_date(self) -> date:
        return self._tanggal

    def set_date(self, tanggal: date):
        self._tanggal = tanggal
        self._label_tgl.configure(text=self._fmt())

    def refresh_colors(self):
        """Dipanggil saat dark/light mode toggle — rebuild UI dengan warna baru."""
        for w in self.winfo_children():
            w.destroy()
        self._buat_ui()


# ─────────────────────────────────────────────────────────────────────────────
# BUDGET PAGE
# ─────────────────────────────────────────────────────────────────────────────

class BudgetPage(ctk.CTkFrame):
    def __init__(self, master, koneksi: sqlite3.Connection, navigasi_ke):
        super().__init__(master, fg_color=BG_WINDOW, corner_radius=0)

        self._koneksi    = koneksi
        self._navigasi   = navigasi_ke
        self._controller = BudgetController(koneksi)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._buat_header()
        self._buat_konten()

    def _buat_header(self):
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.grid(row=0, column=0, sticky="ew",
                          padx=SPACE_XL, pady=(SPACE_XL, 0))
        frame_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_header, text="Budget",
            font=get_font("heading_1"), text_color=TEXT_PRIMARY, anchor="w"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkFrame(
            frame_header, fg_color=BORDER_COLOR, height=1, corner_radius=0
        ).grid(row=1, column=0, sticky="ew", pady=(SPACE_SM, 0))

    def _buat_konten(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=SPACE_XL, pady=SPACE_XL)
        scroll.grid_columnconfigure(0, weight=1)
        self._scroll = scroll
        self._buat_form_card()
        self._buat_riwayat_section()

    def _buat_form_card(self):
        wrapper = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="ew", pady=(0, SPACE_3XL))
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=0, minsize=520)
        wrapper.grid_columnconfigure(2, weight=1)

        card = ctk.CTkFrame(
            wrapper, fg_color=BG_SURFACE, corner_radius=RADIUS_CARD,
            border_width=1, border_color=BORDER_COLOR
        )
        card.grid(row=0, column=1, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Buat Budget Mingguan",
            font=get_font("heading_2"), text_color=TEXT_PRIMARY, anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="w",
               padx=SPACE_XL, pady=(SPACE_XL, SPACE_LG))

        # Label tanggal
        for col, teks in enumerate(["Tanggal Mulai", "Tanggal Selesai"]):
            pad = (SPACE_XL, SPACE_SM) if col == 0 else (SPACE_SM, SPACE_XL)
            ctk.CTkLabel(
                card, text=teks,
                font=get_font("body"), text_color=TEXT_PRIMARY, anchor="w"
            ).grid(row=1, column=col, sticky="w", padx=pad, pady=(0, SPACE_SM))

        # Input tanggal mulai
        self._widget_tgl_mulai = _DateInputWidget(
            card, tanggal_awal=date.today(),
            on_change=self._saat_tanggal_mulai_berubah, readonly=False
        )
        self._widget_tgl_mulai.grid(row=2, column=0, sticky="ew",
                                    padx=(SPACE_XL, SPACE_SM), pady=(0, SPACE_SM))

        # Tanggal selesai — read-only
        self._widget_tgl_selesai = _DateInputWidget(
            card, tanggal_awal=date.today() + timedelta(days=6), readonly=True
        )
        self._widget_tgl_selesai.grid(row=2, column=1, sticky="ew",
                                       padx=(SPACE_SM, SPACE_XL), pady=(0, SPACE_SM))

        ctk.CTkLabel(
            card,
            text="Tanggal selesai dihitung otomatis (mulai + 6 hari)",
            font=get_font("small"), text_color=TEXT_SECONDARY, anchor="w"
        ).grid(row=3, column=0, columnspan=2, sticky="w",
               padx=SPACE_XL, pady=(0, SPACE_SM))

        self.label_error_tgl = ctk.CTkLabel(
            card, text="", font=get_font("small"),
            text_color=COLOR_DANGER, anchor="w"
        )
        self.label_error_tgl.grid(row=4, column=0, columnspan=2, sticky="w",
                                   padx=SPACE_XL, pady=(0, SPACE_SM))

        # Nominal budget
        ctk.CTkLabel(
            card, text="Nominal Budget",
            font=get_font("body"), text_color=TEXT_PRIMARY, anchor="w"
        ).grid(row=5, column=0, columnspan=2, sticky="w",
               padx=SPACE_XL, pady=(SPACE_MD, SPACE_SM))

        frame_currency = ctk.CTkFrame(card, fg_color="transparent")
        frame_currency.grid(row=6, column=0, columnspan=2, sticky="ew",
                            padx=SPACE_XL, pady=(0, SPACE_SM))
        frame_currency.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_currency, text="Rp",
            font=get_font("body"), text_color=TEXT_PRIMARY
        ).grid(row=0, column=0, padx=(0, SPACE_SM))

        self.entry_nominal = ctk.CTkEntry(
            frame_currency, fg_color=BG_INPUT, border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY,
            font=get_font("body"), height=HEIGHT_INPUT
        )
        self.entry_nominal.grid(row=0, column=1, sticky="ew")
        self.entry_nominal.bind("<FocusOut>", self._format_nominal)

        self.label_error_nominal = ctk.CTkLabel(
            card, text="", font=get_font("small"),
            text_color=COLOR_DANGER, anchor="w"
        )
        self.label_error_nominal.grid(row=7, column=0, columnspan=2, sticky="w",
                                       padx=SPACE_XL, pady=(0, SPACE_SM))

        ctk.CTkButton(
            card, text="Simpan",
            font=get_font("body_bold"), fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            height=HEIGHT_BTN_PRIMARY, command=self._handle_simpan
        ).grid(row=8, column=0, columnspan=2, sticky="ew",
               padx=SPACE_XL, pady=(SPACE_LG, SPACE_XL))

    def _buat_riwayat_section(self):
        ctk.CTkLabel(
            self._scroll, text="Riwayat Budget",
            font=get_font("heading_2"), text_color=TEXT_PRIMARY, anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=(0, SPACE_MD))

        card_tabel = ctk.CTkFrame(
            self._scroll, fg_color=BG_SURFACE, corner_radius=RADIUS_CARD,
            border_width=1, border_color=BORDER_COLOR
        )
        card_tabel.grid(row=2, column=0, sticky="nsew", pady=(0, SPACE_XL))
        card_tabel.grid_columnconfigure(0, weight=0, minsize=110)
        card_tabel.grid_columnconfigure(1, weight=1)
        card_tabel.grid_columnconfigure(2, weight=0, minsize=140)

        header_data = [("Minggu ke", "center"), ("Tanggal", "w"), ("Budget", "e")]
        for i, (teks, align) in enumerate(header_data):
            pad_x = (SPACE_XL, SPACE_MD) if i == 0 else \
                    (SPACE_MD, SPACE_XL) if i == 2 else (SPACE_MD, SPACE_MD)
            ctk.CTkLabel(
                card_tabel, text=teks, font=get_font("body_bold"),
                text_color=TEXT_PRIMARY, anchor=align
            ).grid(row=0, column=i, sticky="ew", padx=pad_x,
                   pady=(SPACE_LG, SPACE_SM))

        ctk.CTkFrame(
            card_tabel, fg_color=BORDER_COLOR, height=1, corner_radius=0
        ).grid(row=1, column=0, columnspan=3, sticky="ew", padx=SPACE_MD)

        self.frame_baris = ctk.CTkFrame(card_tabel, fg_color="transparent")
        self.frame_baris.grid(row=2, column=0, columnspan=3,
                              sticky="nsew", pady=(0, SPACE_SM))
        self.frame_baris.grid_columnconfigure(0, weight=0, minsize=110)
        self.frame_baris.grid_columnconfigure(1, weight=1)
        self.frame_baris.grid_columnconfigure(2, weight=0, minsize=140)

        self._muat_riwayat()

    def _muat_riwayat(self):
        for w in self.frame_baris.winfo_children():
            w.destroy()

        riwayat = self._controller.muat_riwayat_budget()
        if not riwayat:
            ctk.CTkLabel(
                self.frame_baris, text="Belum ada riwayat budget.",
                font=get_font("body"), text_color=TEXT_SECONDARY
            ).grid(row=0, column=0, columnspan=3, pady=SPACE_2XL)
            return

        for idx, row in enumerate(riwayat):
            warna = "transparent" if idx % 2 == 0 else BG_TABLE_ROW_ALT
            baris = ctk.CTkFrame(
                self.frame_baris, fg_color=warna,
                corner_radius=0, height=HEIGHT_TABLE_ROW
            )
            baris.grid(row=idx, column=0, columnspan=3, sticky="nsew")
            baris.grid_columnconfigure(0, weight=0, minsize=110)
            baris.grid_columnconfigure(1, weight=1)
            baris.grid_columnconfigure(2, weight=0, minsize=140)
            baris.grid_propagate(False)

            ctk.CTkLabel(
                baris, text=str(row["minggu_ke"]),
                font=get_font("body"), text_color=TEXT_PRIMARY, anchor="center"
            ).grid(row=0, column=0, sticky="nsew", padx=(SPACE_XL, SPACE_MD))

            ctk.CTkLabel(
                baris, text=row["tanggal"],
                font=get_font("body"), text_color=TEXT_PRIMARY, anchor="w"
            ).grid(row=0, column=1, sticky="nsew", padx=SPACE_MD)

            ctk.CTkLabel(
                baris, text=row["nominal"],
                font=get_font("currency_sm"), text_color=TEXT_PRIMARY, anchor="e"
            ).grid(row=0, column=2, sticky="nsew", padx=(SPACE_MD, SPACE_XL))

    # ── Event Handlers ───────────────────────────────────────────────────────

    def _saat_tanggal_mulai_berubah(self, tanggal: date):
        self._widget_tgl_selesai.set_date(tanggal + timedelta(days=6))
        self.label_error_tgl.configure(text="")

    def _format_nominal(self, event=None):
        try:
            nilai_str = self.entry_nominal.get().replace(".", "").replace(",", "").strip()
            if not nilai_str:
                return
            nilai = int(float(nilai_str))
            self.entry_nominal.delete(0, "end")
            self.entry_nominal.insert(0, f"{nilai:,}".replace(",", "."))
        except Exception:
            pass

    def _handle_simpan(self):
        self.label_error_tgl.configure(text="")
        self.label_error_nominal.configure(text="")

        tgl_mulai   = self._widget_tgl_mulai.get_date()
        tgl_selesai = tgl_mulai + timedelta(days=6)   # selalu hitung ulang, abaikan widget
        self._widget_tgl_selesai.set_date(tgl_selesai)

        nominal_str = self.entry_nominal.get()
        if nominal_str and not nominal_str.startswith("Rp"):
            nominal_str = "Rp" + nominal_str

        sukses, pesan = self._controller.simpan_budget_baru(
            tgl_mulai.strftime("%d-%m-%Y"),
            tgl_selesai.strftime("%d-%m-%Y"),
            nominal_str
        )

        if not sukses:
            if "nominal" in pesan.lower():
                self.label_error_nominal.configure(text=pesan)
            else:
                self.label_error_tgl.configure(text=pesan)
            return

        tampilkan_toast(self.master, pesan, tipe="sukses")
        self._widget_tgl_mulai.set_date(date.today())
        self._widget_tgl_selesai.set_date(date.today() + timedelta(days=6))
        self.entry_nominal.delete(0, "end")
        self._muat_riwayat()
        self.after(800, lambda: self._navigasi("dashboard"))

    def refresh_date_widgets(self):
        """
        Dipanggil oleh AppShell saat dark/light mode toggle.
        Rebuild _DateInputWidget agar border & warna ikut mode baru.
        """
        self._widget_tgl_mulai.refresh_colors()
        self._widget_tgl_selesai.refresh_colors()