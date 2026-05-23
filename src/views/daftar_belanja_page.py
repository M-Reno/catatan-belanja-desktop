# views/daftar_belanja_page.py — Placeholder Daftar Belanja (Tahap 4)
import sqlite3
import customtkinter as ctk
from utils.theme_helper import (
    BG_WINDOW, TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_HEADING_1, FONT_BODY, SPACE_SM, SPACE_XL
)

class DaftarBelanjaPage(ctk.CTkFrame):
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
        ctk.CTkLabel(frame, text="Daftar Belanja", font=FONT_HEADING_1,
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")

    def _buat_konten(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0)
        ctk.CTkLabel(frame, text="Fitur daftar belanja akan diimplementasi di Tahap 8.",
                     font=FONT_BODY, text_color=TEXT_SECONDARY).pack()
