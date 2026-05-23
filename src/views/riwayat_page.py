# views/riwayat_page.py — Placeholder Riwayat (Tahap 4)
import sqlite3
import customtkinter as ctk
from utils.theme_helper import (
    BG_WINDOW, TEXT_PRIMARY, TEXT_SECONDARY,
    SPACE_SM, SPACE_XL, get_font
)

class RiwayatPage(ctk.CTkFrame):
    def __init__(self, master, koneksi: sqlite3.Connection, navigasi_ke):
        super().__init__(master, fg_color=BG_WINDOW, corner_radius=0)
        self._koneksi  = koneksi
        self._navigasi = navigasi_ke
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._buat_header()
        self._buat_konten()

    def _buat_header(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="ew", padx=SPACE_XL, pady=(SPACE_XL, SPACE_SM))
        ctk.CTkLabel(frame, text="Riwayat", font=get_font("heading_1"),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")

    def _buat_konten(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0)
        ctk.CTkLabel(frame, text="Riwayat belanja akan diimplementasi di Tahap 9.",
                     font=get_font("body"), text_color=TEXT_SECONDARY).pack()
