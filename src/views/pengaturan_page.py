# src/views/pengaturan_page.py
"""
Halaman Pengaturan - Manajemen Master Data (Satuan & Kategori).
Layout: 2 kolom simetris (bukan tab).
"""

import customtkinter as ctk
import sqlite3
from utils.theme_helper import (
    BG_SURFACE, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_PRIMARY, ACCENT_HOVER, BTN_SECONDARY_BG, BTN_SECONDARY_TEXT,
    COLOR_DANGER, BORDER_COLOR,
    RADIUS_CARD, RADIUS_BTN, RADIUS_DIALOG,
    HEIGHT_BTN_PRIMARY, HEIGHT_BTN_SECONDARY, HEIGHT_INPUT,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
    get_font
)
from controllers.master_data_controller import MasterDataController
from views.components.toast_notification import tampilkan_toast


def _pusatkan_dialog(dialog: ctk.CTkToplevel, lebar: int, tinggi: int) -> None:
    """Posisikan dialog di tengah layar — tunggu sampai window benar-benar muncul."""
    def _terapkan():
        dialog.withdraw()  # sembunyikan sementara
        dialog.update_idletasks()
        lebar_layar = dialog.winfo_screenwidth()
        tinggi_layar = dialog.winfo_screenheight()
        x = (lebar_layar - lebar) // 2
        y = (tinggi_layar - tinggi) // 2
        dialog.geometry(f"{lebar}x{tinggi}+{x}+{y}")
        dialog.deiconify()  # tampilkan di posisi yang benar
    dialog.after(50, _terapkan)


class PengaturanPage(ctk.CTkFrame):
    """
    Halaman Pengaturan dengan 2 kolom:
    - Kolom kiri: CRUD Satuan
    - Kolom kanan: CRUD Kategori
    """

    def __init__(self, master, koneksi: sqlite3.Connection, navigasi_ke):
        super().__init__(master, fg_color="transparent")

        self.koneksi = koneksi
        self.controller = MasterDataController(koneksi)
        self._navigasi = navigasi_ke

        # Setup grid untuk 2 kolom simetris
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Buat panel kiri (Satuan) dan kanan (Kategori)
        self._buat_panel_satuan()
        self._buat_panel_kategori()

        # Muat data awal
        self._refresh_satuan()
        self._refresh_kategori()

    # ========== PANEL SATUAN (Kiri) ==========

    def _buat_panel_satuan(self):
        """Buat panel kiri untuk CRUD Satuan."""
        panel = ctk.CTkFrame(
            self,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=BORDER_COLOR
        )
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE_LG // 2), pady=0)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            panel,
            text="Satuan",
            font=get_font("heading_2"),
            text_color=TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w", padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        # Scrollable list satuan
        self.frame_list_satuan = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", height=200
        )
        self.frame_list_satuan.grid(row=1, column=0, sticky="nsew", padx=SPACE_XL, pady=(0, SPACE_MD))
        self.frame_list_satuan.grid_columnconfigure(0, weight=1)

        # Divider
        ctk.CTkFrame(panel, height=1, fg_color=BORDER_COLOR).grid(
            row=2, column=0, sticky="ew", padx=SPACE_XL, pady=SPACE_MD
        )

        # Entry tambah
        self.entry_satuan = ctk.CTkEntry(
            panel,
            placeholder_text="Masukkan nama satuan...",
            font=get_font("body"),
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT
        )
        self.entry_satuan.grid(row=3, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_SM))
        self.entry_satuan.bind("<Return>", lambda e: self._handle_tambah_satuan())

        # Tombol Tambah
        self.btn_tambah_satuan = ctk.CTkButton(
            panel,
            text="Tambah",
            font=get_font("body"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            text_color="white",
            height=HEIGHT_BTN_PRIMARY,
            command=self._handle_tambah_satuan
        )
        self.btn_tambah_satuan.grid(row=4, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_XL))

    def _refresh_satuan(self):
        """Muat ulang list satuan dari database."""
        for widget in self.frame_list_satuan.winfo_children():
            widget.destroy()
        for idx, (id_satuan, nama_satuan) in enumerate(self.controller.muat_semua_satuan()):
            self._buat_item_satuan(id_satuan, nama_satuan, idx)

    def _buat_item_satuan(self, id_satuan: int, nama_satuan: str, row: int):
        """Buat satu baris item satuan dengan tombol Edit dan Hapus."""
        item_frame = ctk.CTkFrame(self.frame_list_satuan, fg_color="transparent")
        item_frame.grid(row=row, column=0, sticky="ew", pady=SPACE_SM)
        item_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            item_frame,
            text=nama_satuan,
            font=get_font("body"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=(0, SPACE_SM))

        ctk.CTkButton(
            item_frame,
            text="Edit",
            font=get_font("small"),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BORDER_COLOR,
            text_color=BTN_SECONDARY_TEXT,
            height=HEIGHT_BTN_SECONDARY - 4,
            width=60,
            command=lambda: self._handle_edit_satuan(id_satuan, nama_satuan)
        ).grid(row=0, column=1, padx=SPACE_SM)

        ctk.CTkButton(
            item_frame,
            text="Hapus",
            font=get_font("small"),
            fg_color="transparent",
            hover_color=("#FEE2E2", "#3D1515"),
            text_color=COLOR_DANGER,
            border_width=1,
            border_color=COLOR_DANGER,
            height=HEIGHT_BTN_SECONDARY - 4,
            width=60,
            command=lambda: self._handle_hapus_satuan(id_satuan, nama_satuan)
        ).grid(row=0, column=2)

    def _handle_tambah_satuan(self):
        """Handle klik tombol Tambah — simpan satuan baru dari entry."""
        nama = self.entry_satuan.get().strip()
        success, message = self.controller.simpan_satuan_baru(nama)
        tampilkan_toast(self, message, "sukses" if success else "error")
        if success:
            self.entry_satuan.delete(0, "end")
            self._refresh_satuan()

    def _handle_edit_satuan(self, id_satuan: int, nama_lama: str):
        """Buka dialog edit satuan — window baru mirip dialog hapus."""
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Edit Satuan")
        dialog.resizable(False, False)
        dialog.grab_set()
        _pusatkan_dialog(dialog, 360, 180)

        # Ikon + label
        frame_atas = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_atas.pack(fill="x", padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        ctk.CTkLabel(
            frame_atas, text="✏", font=get_font("heading_1"),
            text_color="#0D9488", width=30
        ).pack(side="left", padx=(0, SPACE_MD))

        ctk.CTkLabel(
            frame_atas,
            text=f"Ubah nama satuan '{nama_lama}':",
            font=get_font("body"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        # Entry nama baru
        entry_baru = ctk.CTkEntry(
            dialog,
            font=get_font("body"),
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT
        )
        entry_baru.pack(fill="x", padx=SPACE_XL, pady=(0, SPACE_MD))
        entry_baru.insert(0, nama_lama)
        entry_baru.select_range(0, "end")
        entry_baru.focus_set()

        def simpan():
            nama_baru = entry_baru.get().strip()
            success, message = self.controller.perbarui_satuan(id_satuan, nama_baru)
            tampilkan_toast(self, message, "sukses" if success else "error")
            if success:
                self._refresh_satuan()
                dialog.destroy()

        # Binding Enter untuk simpan
        entry_baru.bind("<Return>", lambda e: simpan())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Tombol
        frame_tombol = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_tombol.pack(fill="x", padx=SPACE_XL, pady=(0, SPACE_XL))

        ctk.CTkButton(
            frame_tombol, text="Batal",
            font=get_font("body"),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BORDER_COLOR,
            text_color=BTN_SECONDARY_TEXT,
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=100,
            command=dialog.destroy
        ).pack(side="left")

        ctk.CTkButton(
            frame_tombol, text="Simpan",
            font=get_font("body_bold"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=120,
            command=simpan
        ).pack(side="right")

    def _handle_hapus_satuan(self, id_satuan: int, nama_satuan: str):
        """Buka dialog konfirmasi hapus satuan."""
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Konfirmasi Hapus")
        dialog.resizable(False, False)
        dialog.grab_set()
        _pusatkan_dialog(dialog, 360, 160)

        frame_pesan = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_pesan.pack(fill="x", padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        ctk.CTkLabel(
            frame_pesan, text="⚠",
            font=ctk.CTkFont(family="Segoe UI", size=20),
            text_color="#DC2626", width=30
        ).pack(side="left", padx=(0, SPACE_MD))

        ctk.CTkLabel(
            frame_pesan,
            text=f"Apakah Anda yakin ingin menghapus\nsatuan '{nama_satuan}'?",
            font=get_font("body"),
            text_color=TEXT_PRIMARY,
            justify="left"
        ).pack(side="left")

        def konfirmasi():
            success, message = self.controller.hapus_satuan_dengan_proteksi(id_satuan, nama_satuan)
            tampilkan_toast(self, message, "sukses" if success else "error")
            if success:
                self._refresh_satuan()
            dialog.destroy()

        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.bind("<Return>", lambda e: konfirmasi())

        frame_tombol = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_tombol.pack(fill="x", padx=SPACE_XL, pady=(0, SPACE_XL))

        btn_batal = ctk.CTkButton(
            frame_tombol, text="Batal",
            font=get_font("body"),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BORDER_COLOR,
            text_color=BTN_SECONDARY_TEXT,
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=100,
            command=dialog.destroy
        )
        btn_batal.pack(side="left")
        # Fokus ke Batal sebagai default aman
        dialog.after(100, btn_batal.focus_set)

        ctk.CTkButton(
            frame_tombol, text="Hapus",
            font=get_font("body_bold"),
            fg_color="transparent",
            hover_color="#FEE2E2",
            text_color="#DC2626",
            border_width=1,
            border_color="#DC2626",
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=120,
            command=konfirmasi
        ).pack(side="right")

    # ========== PANEL KATEGORI (Kanan) ==========

    def _buat_panel_kategori(self):
        """Buat panel kanan untuk CRUD Kategori."""
        panel = ctk.CTkFrame(
            self,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=BORDER_COLOR
        )
        panel.grid(row=0, column=1, sticky="nsew", padx=(SPACE_LG // 2, 0), pady=0)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            panel,
            text="Kategori",
            font=get_font("heading_2"),
            text_color=TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w", padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        # Scrollable list kategori
        self.frame_list_kategori = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", height=200
        )
        self.frame_list_kategori.grid(row=1, column=0, sticky="nsew", padx=SPACE_XL, pady=(0, SPACE_MD))
        self.frame_list_kategori.grid_columnconfigure(0, weight=1)

        # Divider
        ctk.CTkFrame(panel, height=1, fg_color=BORDER_COLOR).grid(
            row=2, column=0, sticky="ew", padx=SPACE_XL, pady=SPACE_MD
        )

        # Entry tambah
        self.entry_kategori = ctk.CTkEntry(
            panel,
            placeholder_text="Masukkan nama kategori...",
            font=get_font("body"),
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT
        )
        self.entry_kategori.grid(row=3, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_SM))
        self.entry_kategori.bind("<Return>", lambda e: self._handle_tambah_kategori())

        # Tombol Tambah
        self.btn_tambah_kategori = ctk.CTkButton(
            panel,
            text="Tambah",
            font=get_font("body"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            text_color="white",
            height=HEIGHT_BTN_PRIMARY,
            command=self._handle_tambah_kategori
        )
        self.btn_tambah_kategori.grid(row=4, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_XL))

    def _refresh_kategori(self):
        """Muat ulang list kategori dari database."""
        for widget in self.frame_list_kategori.winfo_children():
            widget.destroy()
        for idx, (id_kategori, nama_kategori) in enumerate(self.controller.muat_semua_kategori()):
            self._buat_item_kategori(id_kategori, nama_kategori, idx)

    def _buat_item_kategori(self, id_kategori: int, nama_kategori: str, row: int):
        """Buat satu baris item kategori dengan tombol Edit dan Hapus."""
        item_frame = ctk.CTkFrame(self.frame_list_kategori, fg_color="transparent")
        item_frame.grid(row=row, column=0, sticky="ew", pady=SPACE_SM)
        item_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            item_frame,
            text=nama_kategori,
            font=get_font("body"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=(0, SPACE_SM))

        ctk.CTkButton(
            item_frame,
            text="Edit",
            font=get_font("small"),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BORDER_COLOR,
            text_color=BTN_SECONDARY_TEXT,
            height=HEIGHT_BTN_SECONDARY - 4,
            width=60,
            command=lambda: self._handle_edit_kategori(id_kategori, nama_kategori)
        ).grid(row=0, column=1, padx=SPACE_SM)

        ctk.CTkButton(
            item_frame,
            text="Hapus",
            font=get_font("small"),
            fg_color="transparent",
            hover_color=("#FEE2E2", "#3D1515"),
            text_color=COLOR_DANGER,
            border_width=1,
            border_color=COLOR_DANGER,
            height=HEIGHT_BTN_SECONDARY - 4,
            width=60,
            command=lambda: self._handle_hapus_kategori(id_kategori, nama_kategori)
        ).grid(row=0, column=2)

    def _handle_tambah_kategori(self):
        """Handle klik tombol Tambah — simpan kategori baru dari entry."""
        nama = self.entry_kategori.get().strip()
        success, message = self.controller.simpan_kategori_baru(nama)
        tampilkan_toast(self, message, "sukses" if success else "error")
        if success:
            self.entry_kategori.delete(0, "end")
            self._refresh_kategori()

    def _handle_edit_kategori(self, id_kategori: int, nama_lama: str):
        """Buka dialog edit kategori — window baru mirip dialog hapus."""
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Edit Kategori")
        dialog.resizable(False, False)
        dialog.grab_set()
        _pusatkan_dialog(dialog, 360, 180)

        # Ikon + label
        frame_atas = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_atas.pack(fill="x", padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        ctk.CTkLabel(
            frame_atas, text="✏", font=get_font("heading_1"),
            text_color="#0D9488", width=30
        ).pack(side="left", padx=(0, SPACE_MD))

        ctk.CTkLabel(
            frame_atas,
            text=f"Ubah nama kategori '{nama_lama}':",
            font=get_font("body"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        # Entry nama baru
        entry_baru = ctk.CTkEntry(
            dialog,
            font=get_font("body"),
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT
        )
        entry_baru.pack(fill="x", padx=SPACE_XL, pady=(0, SPACE_MD))
        entry_baru.insert(0, nama_lama)
        entry_baru.select_range(0, "end")
        entry_baru.focus_set()

        def simpan():
            nama_baru = entry_baru.get().strip()
            success, message = self.controller.perbarui_kategori(id_kategori, nama_baru)
            tampilkan_toast(self, message, "sukses" if success else "error")
            if success:
                self._refresh_kategori()
                dialog.destroy()

        entry_baru.bind("<Return>", lambda e: simpan())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Tombol
        frame_tombol = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_tombol.pack(fill="x", padx=SPACE_XL, pady=(0, SPACE_XL))

        ctk.CTkButton(
            frame_tombol, text="Batal",
            font=get_font("body"),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BORDER_COLOR,
            text_color=BTN_SECONDARY_TEXT,
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=100,
            command=dialog.destroy
        ).pack(side="left")

        ctk.CTkButton(
            frame_tombol, text="Simpan",
            font=get_font("body_bold"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=120,
            command=simpan
        ).pack(side="right")

    def _handle_hapus_kategori(self, id_kategori: int, nama_kategori: str):
        """Buka dialog konfirmasi hapus kategori."""
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Konfirmasi Hapus")
        dialog.resizable(False, False)
        dialog.grab_set()
        _pusatkan_dialog(dialog, 360, 160)

        frame_pesan = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_pesan.pack(fill="x", padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        ctk.CTkLabel(
            frame_pesan, text="⚠",
            font=ctk.CTkFont(family="Segoe UI", size=20),
            text_color="#DC2626", width=30
        ).pack(side="left", padx=(0, SPACE_MD))

        ctk.CTkLabel(
            frame_pesan,
            text=f"Apakah Anda yakin ingin menghapus\nkategori '{nama_kategori}'?",
            font=get_font("body"),
            text_color=TEXT_PRIMARY,
            justify="left"
        ).pack(side="left")

        def konfirmasi():
            success, message = self.controller.hapus_kategori_dengan_proteksi(id_kategori, nama_kategori)
            tampilkan_toast(self, message, "sukses" if success else "error")
            if success:
                self._refresh_kategori()
            dialog.destroy()

        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.bind("<Return>", lambda e: konfirmasi())

        frame_tombol = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_tombol.pack(fill="x", padx=SPACE_XL, pady=(0, SPACE_XL))

        btn_batal = ctk.CTkButton(
            frame_tombol, text="Batal",
            font=get_font("body"),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BORDER_COLOR,
            text_color=BTN_SECONDARY_TEXT,
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=100,
            command=dialog.destroy
        )
        btn_batal.pack(side="left")
        dialog.after(100, btn_batal.focus_set)

        ctk.CTkButton(
            frame_tombol, text="Hapus",
            font=get_font("body_bold"),
            fg_color="transparent",
            hover_color="#FEE2E2",
            text_color="#DC2626",
            border_width=1,
            border_color="#DC2626",
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=120,
            command=konfirmasi
        ).pack(side="right")