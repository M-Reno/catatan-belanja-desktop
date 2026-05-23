# views/app_shell.py — Shell utama: sidebar kiri + area konten kanan
# Mengelola navigasi antar halaman dan toggle dark/light mode

import sqlite3
import customtkinter as ctk

from utils.theme_helper import (
    BG_WINDOW, BG_SURFACE, BG_SIDEBAR,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_SIDEBAR,
    ACCENT_PRIMARY, ACCENT_SIDEBAR,
    BORDER_COLOR, DIVIDER_COLOR,
    FONT_APP_TITLE, FONT_NAV_ITEM, FONT_SMALL,
    SIDEBAR_WIDTH, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
    HEIGHT_NAV_ITEM
)


class AppShell(ctk.CTkFrame):
    """
    Frame utama yang membagi layar menjadi sidebar (kiri) dan konten (kanan).
    Mengelola navigasi antar halaman dan status halaman aktif.
    """

    # Daftar item navigasi: (label_tampil, nama_internal, kelas_halaman)
    _MENU_ITEMS = [
        ("Dashboard",       "dashboard",       "views.dashboard_page",       "DashboardPage"),
        ("Budget",          "budget",           "views.budget_page",           "BudgetPage"),
        ("Daftar Belanja",  "daftar_belanja",  "views.daftar_belanja_page",  "DaftarBelanjaPage"),
        ("Riwayat",         "riwayat",         "views.riwayat_page",         "RiwayatPage"),
        ("Pengaturan",      "pengaturan",       "views.pengaturan_page",      "PengaturanPage"),
    ]

    def __init__(self, master: ctk.CTk, koneksi: sqlite3.Connection):
        super().__init__(master, fg_color=BG_WINDOW, corner_radius=0)

        self._koneksi    = koneksi
        self._halaman_aktif: str = ""

        # Cache instance halaman agar tidak dibuat ulang saat navigasi balik
        self._cache_halaman: dict = {}

        self._buat_layout()
        self._buat_sidebar()
        self._buat_area_konten()

        # Tampilkan halaman Dashboard sebagai default
        self.navigasi_ke("dashboard")

    # ─── Layout ───────────────────────────────────────────────────────────────

    def _buat_layout(self) -> None:
        """Setup grid utama: kolom 0 = sidebar fixed, kolom 1 = konten expand."""
        self.grid_columnconfigure(0, weight=0, minsize=SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    # ─── Sidebar ──────────────────────────────────────────────────────────────

    def _buat_sidebar(self) -> None:
        """Buat sidebar navigasi di kolom kiri."""

        # Frame sidebar — selalu gelap teal di kedua mode
        self._frame_sidebar = ctk.CTkFrame(
            self,
            fg_color=BG_SIDEBAR,
            corner_radius=0,
            width=SIDEBAR_WIDTH
        )
        self._frame_sidebar.grid(row=0, column=0, sticky="nsew")
        self._frame_sidebar.grid_propagate(False)
        self._frame_sidebar.grid_rowconfigure(1, weight=1)

        # Nama aplikasi di atas sidebar
        label_judul = ctk.CTkLabel(
            self._frame_sidebar,
            text="Catatan Belanja",
            font=FONT_APP_TITLE,
            text_color=TEXT_SIDEBAR,
            anchor="w"
        )
        label_judul.grid(
            row=0, column=0, sticky="ew",
            padx=SPACE_LG, pady=(SPACE_XL, SPACE_LG)
        )

        # Frame untuk item-item navigasi — bisa di-scroll jika layar pendek
        self._frame_nav = ctk.CTkFrame(
            self._frame_sidebar,
            fg_color="transparent"
        )
        self._frame_nav.grid(row=1, column=0, sticky="nsew")
        self._frame_sidebar.grid_columnconfigure(0, weight=1)

        # Buat tombol navigasi untuk setiap menu item
        self._tombol_nav: dict[str, ctk.CTkButton] = {}
        for label, nama, _, _ in self._MENU_ITEMS:
            btn = self._buat_tombol_nav(label, nama)
            self._tombol_nav[nama] = btn

        # Divider tipis sebelum toggle mode
        divider = ctk.CTkFrame(
            self._frame_sidebar,
            fg_color=("#1A4440", "#1A4440"),
            height=1,
            corner_radius=0
        )
        divider.grid(row=2, column=0, sticky="ew", padx=SPACE_MD, pady=SPACE_SM)

        # Tombol toggle dark/light mode di bawah sidebar
        self._btn_toggle_mode = ctk.CTkButton(
            self._frame_sidebar,
            text="🌙  Dark Mode",
            font=FONT_SMALL,
            fg_color="transparent",
            hover_color=("#1A4440", "#1A4440"),
            text_color=TEXT_SIDEBAR,
            anchor="w",
            height=HEIGHT_NAV_ITEM,
            corner_radius=0,
            command=self._toggle_mode
        )
        self._btn_toggle_mode.grid(
            row=3, column=0, sticky="ew",
            padx=0, pady=(0, SPACE_MD)
        )

    def _buat_tombol_nav(self, label: str, nama: str) -> ctk.CTkButton:
        """Buat satu tombol navigasi dan tambahkan ke frame nav."""

        btn = ctk.CTkButton(
            self._frame_nav,
            text=f"  {label}",
            font=FONT_NAV_ITEM,
            anchor="w",
            height=HEIGHT_NAV_ITEM,
            corner_radius=0,

            # State normal: transparan
            fg_color="transparent",
            hover_color=("#1A4440", "#1A4440"),
            text_color=TEXT_SIDEBAR,

            # Border kiri untuk state aktif — diatur manual di _set_state_nav
            border_width=0,
            command=lambda n=nama: self.navigasi_ke(n)
        )
        btn.pack(fill="x", padx=0, pady=0)
        return btn

    def _set_state_nav(self, nama_aktif: str) -> None:
        """
        Update tampilan semua tombol navigasi.
        Tombol aktif: background teal + border kiri putih 3px.
        Tombol lain: kembali ke transparan.
        """
        for nama, btn in self._tombol_nav.items():
            if nama == nama_aktif:
                # State aktif
                btn.configure(
                    fg_color=ACCENT_SIDEBAR,
                    border_width=0,
                    text_color="#FFFFFF"
                )
            else:
                # State normal
                btn.configure(
                    fg_color="transparent",
                    border_width=0,
                    text_color=TEXT_SIDEBAR
                )

    # ─── Area Konten ──────────────────────────────────────────────────────────

    def _buat_area_konten(self) -> None:
        """Buat frame area konten di kolom kanan."""

        self._frame_konten = ctk.CTkFrame(
            self,
            fg_color=BG_WINDOW,
            corner_radius=0
        )
        self._frame_konten.grid(row=0, column=1, sticky="nsew")
        self._frame_konten.grid_columnconfigure(0, weight=1)
        self._frame_konten.grid_rowconfigure(0, weight=1)

    # ─── Navigasi ─────────────────────────────────────────────────────────────

    def navigasi_ke(self, nama_halaman: str) -> None:
        """
        Tampilkan halaman yang diminta dan sembunyikan halaman sebelumnya.
        Halaman di-cache agar tidak dibuat ulang setiap navigasi.
        """
        if nama_halaman == self._halaman_aktif:
            return

        # Sembunyikan halaman yang sedang aktif
        if self._halaman_aktif and self._halaman_aktif in self._cache_halaman:
            self._cache_halaman[self._halaman_aktif].grid_remove()

        # Buat halaman baru jika belum ada di cache
        if nama_halaman not in self._cache_halaman:
            halaman = self._buat_halaman(nama_halaman)
            if halaman is None:
                return
            self._cache_halaman[nama_halaman] = halaman

        # Tampilkan halaman yang diminta
        self._cache_halaman[nama_halaman].grid(
            row=0, column=0, sticky="nsew"
        )

        # Update state tombol navigasi dan status aktif
        self._halaman_aktif = nama_halaman
        self._set_state_nav(nama_halaman)

    def _buat_halaman(self, nama_halaman: str) -> ctk.CTkFrame | None:
        """
        Import modul halaman secara dinamis dan buat instance-nya.
        Pendekatan lazy-import mencegah circular import dan mempercepat startup.
        """
        import importlib

        # Cari definisi halaman dari daftar menu
        for _, nama, modul_path, nama_kelas in self._MENU_ITEMS:
            if nama == nama_halaman:
                try:
                    modul = importlib.import_module(modul_path)
                    kelas = getattr(modul, nama_kelas)

                    # Setiap halaman menerima master frame, koneksi db, dan fungsi navigasi
                    return kelas(
                        master=self._frame_konten,
                        koneksi=self._koneksi,
                        navigasi_ke=self.navigasi_ke
                    )
                except Exception as e:
                    # Halaman placeholder jika modul belum ada
                    return self._buat_placeholder(nama_halaman, str(e))

        return None

    def _buat_placeholder(self, nama: str, pesan_error: str = "") -> ctk.CTkFrame:
        """
        Placeholder sementara untuk halaman yang belum diimplementasi.
        Ditampilkan selama development Tahap 4.
        """
        frame = ctk.CTkFrame(
            self._frame_konten,
            fg_color=BG_WINDOW,
            corner_radius=0
        )
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # Frame tengah untuk isi placeholder
        frame_tengah = ctk.CTkFrame(frame, fg_color="transparent")
        frame_tengah.grid(row=0, column=0)

        # Nama halaman
        ctk.CTkLabel(
            frame_tengah,
            text=f"📄  {nama.replace('_', ' ').title()}",
            font=FONT_APP_TITLE,
            text_color=TEXT_PRIMARY
        ).pack(pady=(0, SPACE_SM))

        # Status
        ctk.CTkLabel(
            frame_tengah,
            text="Halaman ini sedang dalam pengembangan.",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY
        ).pack()

        # Error detail jika ada (untuk debugging)
        if pesan_error:
            ctk.CTkLabel(
                frame_tengah,
                text=f"({pesan_error})",
                font=FONT_SMALL,
                text_color=TEXT_SECONDARY,
                wraplength=400
            ).pack(pady=(SPACE_SM, 0))

        return frame

    # ─── Toggle Mode ──────────────────────────────────────────────────────────

    def _toggle_mode(self) -> None:
        """
        Toggle antara Light dan Dark mode.
        Update label tombol dan redraw chart jika Dashboard aktif.
        """
        mode_sekarang = ctk.get_appearance_mode()

        if mode_sekarang == "Light":
            ctk.set_appearance_mode("Dark")
            self._btn_toggle_mode.configure(text="☀️  Light Mode")
        else:
            ctk.set_appearance_mode("Light")
            self._btn_toggle_mode.configure(text="🌙  Dark Mode")

        # Jika dashboard aktif, minta redraw chart matplotlib
        if self._halaman_aktif == "dashboard":
            halaman = self._cache_halaman.get("dashboard")
            if halaman and hasattr(halaman, "redraw_chart"):
                halaman.redraw_chart()
