"""
dashboard_page.py — Halaman Dashboard
Sesuai PRD §5.1 (FR-DB-1 s.d. FR-DB-5) dan Design System §4.1

Dua state:
  - Empty State : belum ada budget minggu berjalan → pesan + tombol CTA
  - Normal State: ada budget → 2 stat card + bar chart harian
"""

import sqlite3
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

from controllers.dashboard_controller import DashboardController
from utils.theme_helper import (
    BG_WINDOW, BG_SURFACE,
    TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_PRIMARY, ACCENT_HOVER,
    COLOR_WARNING, COLOR_DANGER,
    BORDER_COLOR,
    CHART_BAR, CHART_BAR_EMPTY,
    CHART_BG_LIGHT, CHART_BG_DARK,
    CHART_GRID_LIGHT, CHART_GRID_DARK,
    CHART_TEXT_LIGHT, CHART_TEXT_DARK,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL,
    RADIUS_CARD, HEIGHT_BTN_PRIMARY,
    get_font
)
from utils.format_helper import format_rupiah_ringkas


# Urutan hari sesuai PRD FR-DB-2
URUTAN_HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]


class DashboardPage(ctk.CTkFrame):
    """Halaman utama yang tampil pertama kali saat aplikasi dibuka."""

    def __init__(self, master, koneksi: sqlite3.Connection, navigasi_ke):
        super().__init__(master, fg_color=BG_WINDOW, corner_radius=0)

        self._koneksi     = koneksi
        self._navigasi    = navigasi_ke
        self._controller  = DashboardController(koneksi)

        # Referensi canvas chart — untuk di-destroy saat redraw
        self._canvas_chart = None
        self._fig          = None

        # Data terakhir yang di-load — dipakai ulang saat redraw chart
        self._data_dashboard = None

        # Grid utama: baris 0 = header, baris 1 = konten
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._buat_header()

        # Frame konten — area yang diganti antara empty state dan normal state
        self._frame_konten = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_konten.grid(row=1, column=0, sticky="nsew")
        self._frame_konten.grid_columnconfigure(0, weight=1)
        self._frame_konten.grid_rowconfigure(0, weight=1)

        # Muat dan render data
        self._muat_dan_render()

    # ──────────────────────────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────────────────────────

    def _buat_header(self):
        """Header halaman: judul, sub-label periode, dan garis pemisah."""
        self._frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_header.grid(row=0, column=0, sticky="ew",
                                padx=SPACE_XL, pady=(SPACE_XL, 0))
        self._frame_header.grid_columnconfigure(0, weight=1)

        self._label_judul = ctk.CTkLabel(
            self._frame_header,
            text="Dashboard",
            font=get_font("heading_1"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )
        self._label_judul.grid(row=0, column=0, sticky="w")

        # Sub-label periode — dikosongkan saat empty state
        self._label_periode = ctk.CTkLabel(
            self._frame_header,
            text="",
            font=get_font("period_label"),
            text_color=TEXT_SECONDARY,
            anchor="w"
        )
        self._label_periode.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Garis pemisah tipis
        ctk.CTkFrame(
            self._frame_header,
            fg_color=BORDER_COLOR,
            height=1,
            corner_radius=0
        ).grid(row=2, column=0, sticky="ew", pady=(SPACE_SM, 0))

    # ──────────────────────────────────────────────────────────────────────────
    # LOAD & RENDER
    # ──────────────────────────────────────────────────────────────────────────

    def _muat_dan_render(self):
        """Ambil data dari controller dan pilih state yang sesuai untuk di-render."""
        # Tutup figure matplotlib lebih dulu agar after-callback tidak tertinggal
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
        self._canvas_chart = None

        # Bersihkan semua widget konten sebelumnya
        for widget in self._frame_konten.winfo_children():
            widget.destroy()

        data = self._controller.muat_data_dashboard()
        self._data_dashboard = data

        if data is None:
            # Tidak ada budget minggu ini — tampilkan empty state (FR-DB-5)
            self._label_periode.configure(text="")
            self._render_empty_state()
        else:
            # Ada budget — tampilkan stat card dan chart (FR-DB-1, FR-DB-2, FR-DB-3)
            self._label_periode.configure(text=data["label_periode"])
            self._render_normal_state(data)

    def refresh(self):
        """Muat ulang seluruh data Dashboard. Dipanggil dari luar setelah ada perubahan."""
        self._muat_dan_render()

    # ──────────────────────────────────────────────────────────────────────────
    # EMPTY STATE (FR-DB-5)
    # ──────────────────────────────────────────────────────────────────────────

    def _render_empty_state(self):
        """
        Tampilkan pesan kosong dan tombol CTA saat belum ada budget minggu ini.
        Grafik dan stat card TIDAK ditampilkan dalam kondisi ini.
        """
        # Tempatkan konten di tengah-tengah frame
        frame = ctk.CTkFrame(self._frame_konten, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Ikon kalender 64px
        ctk.CTkLabel(
            frame,
            text="📅",
            font=ctk.CTkFont(size=64),
            text_color=TEXT_SECONDARY
        ).pack(pady=(0, SPACE_LG))

        # Judul empty state
        ctk.CTkLabel(
            frame,
            text="Belum ada budget minggu ini",
            font=get_font("heading_2"),
            text_color=TEXT_SECONDARY
        ).pack()

        # Keterangan tambahan
        ctk.CTkLabel(
            frame,
            text="Buat budget untuk mulai mencatat belanja",
            font=get_font("body"),
            text_color=TEXT_SECONDARY
        ).pack(pady=(SPACE_SM, SPACE_2XL))

        # Tombol CTA — langsung navigasi ke halaman Budget
        ctk.CTkButton(
            frame,
            text="Buat Budget Mingguan Anda Sekarang",
            font=get_font("body_bold"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            height=HEIGHT_BTN_PRIMARY,
            width=300,
            corner_radius=8,
            command=lambda: self._navigasi("budget")
        ).pack()

    # ──────────────────────────────────────────────────────────────────────────
    # NORMAL STATE
    # ──────────────────────────────────────────────────────────────────────────

    def _render_normal_state(self, data: dict):
        """Tampilkan dua stat card di atas dan grafik batang harian di bawah."""
        # Wrapper scroll agar konten tidak terpotong di layar kecil
        scroll = ctk.CTkScrollableFrame(
            self._frame_konten,
            fg_color="transparent",
            corner_radius=0
        )
        scroll.grid(row=0, column=0, sticky="nsew",
                    padx=SPACE_XL, pady=SPACE_XL)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)
        scroll.grid_rowconfigure(1, weight=1)

        self._render_stat_cards(scroll, data)
        self._render_chart_card(scroll, data)

    # ── Stat Cards ────────────────────────────────────────────────────────────

    def _render_stat_cards(self, parent, data: dict):
        """Buat dua stat card: Total Pengeluaran (kiri) dan Sisa Budget (kanan)."""

        # Card kiri — Total Pengeluaran (warna selalu normal)
        self._buat_stat_card(
            parent,
            kolom=0,
            label="Total Pengeluaran",
            nilai=data["str_total"],
            warna_nilai=TEXT_PRIMARY
        )

        # Pilih warna sisa budget berdasarkan status (normal / warning / danger)
        warna_sisa = {
            "danger" : COLOR_DANGER,
            "warning": COLOR_WARNING,
            "normal" : TEXT_PRIMARY,
        }.get(data["status_sisa"], TEXT_PRIMARY)

        # Card kanan — Sisa Budget
        self._buat_stat_card(
            parent,
            kolom=1,
            label="Sisa Budget",
            nilai=data["str_sisa"],
            warna_nilai=warna_sisa
        )

    def _buat_stat_card(self, parent, kolom: int, label: str,
                        nilai: str, warna_nilai):
        """Buat satu stat card dengan label keterangan dan angka besar."""
        # Padding kiri-kanan antar card supaya ada jarak di tengah
        pad_x = (0, SPACE_MD // 2) if kolom == 0 else (SPACE_MD // 2, 0)

        card = ctk.CTkFrame(
            parent,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=BORDER_COLOR
        )
        card.grid(row=0, column=kolom, sticky="nsew",
                  padx=pad_x, pady=(0, SPACE_LG))
        card.grid_columnconfigure(0, weight=1)

        # Label keterangan kecil di atas
        ctk.CTkLabel(
            card,
            text=label,
            font=get_font("small"),
            text_color=TEXT_SECONDARY,
            anchor="w"
        ).grid(row=0, column=0, sticky="w",
               padx=SPACE_XL, pady=(SPACE_XL, SPACE_SM))

        # Angka utama — font besar, warna dinamis
        ctk.CTkLabel(
            card,
            text=nilai,
            font=get_font("currency_lg"),
            text_color=warna_nilai,
            anchor="w"
        ).grid(row=1, column=0, sticky="w",
               padx=SPACE_XL, pady=(0, SPACE_XL))

    # ── Chart Card ────────────────────────────────────────────────────────────

    def _render_chart_card(self, parent, data: dict):
        """Buat card yang memuat grafik batang pengeluaran harian."""
        card = ctk.CTkFrame(
            parent,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=BORDER_COLOR
        )
        card.grid(row=1, column=0, columnspan=2, sticky="nsew",
                  pady=(0, SPACE_LG))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        # Judul section grafik
        ctk.CTkLabel(
            card,
            text="Pengeluaran Harian",
            font=get_font("heading_2"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=0, column=0, sticky="w",
               padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        # Frame embed matplotlib
        self._frame_chart = ctk.CTkFrame(card, fg_color="transparent")
        self._frame_chart.grid(row=1, column=0, sticky="nsew",
                               padx=SPACE_MD, pady=(0, SPACE_MD))
        self._frame_chart.grid_columnconfigure(0, weight=1)

        # Ambil data harian dari controller lalu render
        data_grafik = self._controller.muat_data_grafik(data["id_periode"])
        self._buat_matplotlib_chart(self._frame_chart, data_grafik)

    def _buat_matplotlib_chart(self, parent, data_grafik: dict):
        """
        Render grafik batang vertikal matplotlib dan embed ke CTk frame.
        Bar teal untuk hari dengan transaksi, abu-teal untuk hari kosong.
        """
        # Tutup figure dulu agar semua after-callback matplotlib dibatalkan,
        # baru destroy widget Tk-nya — urutan ini mencegah TclError focus/update
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
        if self._canvas_chart is not None:
            try:
                self._canvas_chart.get_tk_widget().destroy()
            except Exception:
                pass
            self._canvas_chart = None

        # Sesuaikan warna dengan mode tampilan (light / dark)
        is_dark    = ctk.get_appearance_mode() == "Dark"
        bg_color   = CHART_BG_DARK   if is_dark else CHART_BG_LIGHT
        grid_color = CHART_GRID_DARK if is_dark else CHART_GRID_LIGHT
        text_color = CHART_TEXT_DARK if is_dark else CHART_TEXT_LIGHT

        # Susun nilai harian sesuai urutan Sen–Min
        nilai_per_hari = [data_grafik.get(hari, 0.0) for hari in URUTAN_HARI]

        # Warna bar: teal jika ada pengeluaran, abu-teal jika hari kosong
        warna_bar = [
            CHART_BAR if nilai > 0 else CHART_BAR_EMPTY
            for nilai in nilai_per_hari
        ]

        # Buat figure dan axes
        fig, ax = plt.subplots(figsize=(8, 3.2))
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        # Gambar bar vertikal
        ax.bar(URUTAN_HARI, nilai_per_hari,
               color=warna_bar, width=0.5, zorder=3)

        # Grid horizontal di belakang bar
        ax.yaxis.grid(True, color=grid_color, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)

        # Bersihkan border yang tidak perlu
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(grid_color)

        # Format label sumbu Y ke Rupiah ringkas
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, _: format_rupiah_ringkas(x))
        )

        # Warna teks label sumbu
        ax.tick_params(colors=text_color, labelsize=9)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_color(text_color)

        fig.tight_layout(pad=1.2)

        # Embed canvas matplotlib ke dalam frame CTk
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()

        # Nonaktifkan semua binding mouse/focus bawaan matplotlib
        # agar tidak terjadi TclError saat widget sudah di-destroy
        tk_widget = canvas.get_tk_widget()
        for seq in ["<ButtonPress>", "<ButtonRelease>", "<Button-1>",
                    "<Button-2>", "<Button-3>", "<Motion>",
                    "<Enter>", "<Leave>", "<FocusIn>", "<FocusOut>",
                    "<Key>", "<KeyPress>", "<KeyRelease>"]:
            try:
                tk_widget.unbind(seq)
            except Exception:
                pass

        tk_widget.pack(fill="both", expand=True)

        # Simpan referensi untuk keperluan redraw saat toggle mode
        self._canvas_chart = canvas
        self._fig          = fig

    # ──────────────────────────────────────────────────────────────────────────
    # REDRAW CHART
    # ──────────────────────────────────────────────────────────────────────────

    def redraw_chart(self):
        """
        Gambar ulang chart dengan warna mode yang baru (light/dark).
        Dipanggil oleh AppShell._toggle_mode() saat pengguna mengganti mode.
        """
        # Tidak ada yang perlu di-redraw jika sedang di empty state
        if self._data_dashboard is None or self._canvas_chart is None:
            return

        # Render ulang chart di frame yang sama dengan warna mode baru
        data_grafik = self._controller.muat_data_grafik(
            self._data_dashboard["id_periode"]
        )
        self._buat_matplotlib_chart(self._frame_chart, data_grafik)