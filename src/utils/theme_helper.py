"""
theme_helper.py — Token desain terpusat untuk seluruh UI Catatan Belanja
Semua konstanta warna, font, spacing, radius, dan dimensi ada di sini.

Sumber: Design System v1.5 §1, §9
PENTING: Warna light/dark menggunakan Tuple[str, str], bukan list,
agar kompatibel dengan type checker Pylance di VS Code.
CTk menerima keduanya saat runtime, tapi Tuple lebih type-safe.

CATATAN FONT: CTkFont harus dibuat SETELAH Tk root window ada.
Gunakan fungsi get_font() — bukan variabel FONT_* langsung.
Contoh: font=get_font("app_title")  bukan  font=FONT_APP_TITLE
"""

import customtkinter as ctk
from typing import Optional

# ─── Background ───────────────────────────────────────────────────────────────
BG_WINDOW        : tuple = ("#F0FDFA", "#0D1B1A")   # Jendela utama — putih teal / gelap teal
BG_SURFACE       : tuple = ("#FFFFFF", "#1A2E2C")   # Card, panel, frame isi
BG_SIDEBAR       : tuple = ("#134E4A", "#0A1F1E")   # Sidebar (selalu gelap teal)
BG_INPUT         : tuple = ("#F0FDFA", "#1E3533")   # Background input field
BG_TABLE_ROW_ALT : tuple = ("#F0FDFA", "#1E3533")   # Baris tabel alternating

# ─── Teks ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY     : tuple = ("#0F2421", "#E8FAF8")   # Teks utama
TEXT_SECONDARY   : tuple = ("#4B7A75", "#7BBFBA")   # Label, keterangan
TEXT_SIDEBAR     : str   = "#FFFFFF"                 # Teks sidebar (selalu putih)
TEXT_PLACEHOLDER : tuple = ("#80C4BE", "#4B7A75")   # Placeholder input

# ─── Aksen & Tombol ───────────────────────────────────────────────────────────
ACCENT_PRIMARY    : tuple = ("#0D9488", "#14B8A6")   # Tombol utama, elemen aktif
ACCENT_HOVER      : tuple = ("#0F766E", "#0D9488")   # Hover tombol utama
ACCENT_SIDEBAR    : str   = "#14B8A6"                 # Item aktif di sidebar
BTN_SECONDARY_BG  : tuple = ("#CCFBF1", "#1E3533")   # Background tombol sekunder
BTN_SECONDARY_TEXT: tuple = ("#0F2421", "#E8FAF8")   # Teks tombol sekunder

# ─── Status ───────────────────────────────────────────────────────────────────
COLOR_SUCCESS    : tuple = ("#059669", "#34D399")   # Sukses — hijau emerald
COLOR_WARNING    : tuple = ("#D97706", "#FBBF24")   # Peringatan budget < 20%
COLOR_DANGER     : tuple = ("#DC2626", "#F87171")   # Budget negatif, hapus
COLOR_INFO       : tuple = ("#0891B2", "#22D3EE")   # Informasi netral — cyan

# ─── Border & Divider ─────────────────────────────────────────────────────────
BORDER_COLOR     : tuple = ("#99F6E4", "#1E3533")   # Border komponen
DIVIDER_COLOR    : tuple = ("#CCFBF1", "#162E2C")   # Garis pemisah

# ─── Chart (matplotlib — selalu string tunggal, tidak ada dark/light tuple) ───
CHART_BAR        : str = "#0D9488"   # Bar default — teal-600
CHART_BAR_EMPTY  : str = "#CCFBF1"  # Bar hari tanpa transaksi — teal-100
CHART_BG_LIGHT   : str = "#FFFFFF"
CHART_BG_DARK    : str = "#1A2E2C"
CHART_GRID_LIGHT : str = "#99F6E4"
CHART_GRID_DARK  : str = "#1E3533"
CHART_TEXT_LIGHT : str = "#4B7A75"
CHART_TEXT_DARK  : str = "#7BBFBA"

# ─── Spacing (pixel) ──────────────────────────────────────────────────────────
SPACE_XS  : int = 4
SPACE_SM  : int = 8
SPACE_MD  : int = 12
SPACE_LG  : int = 16
SPACE_XL  : int = 24
SPACE_2XL : int = 32
SPACE_3XL : int = 48

# ─── Dimensi ──────────────────────────────────────────────────────────────────
SIDEBAR_WIDTH      : int = 200
MIN_WINDOW_WIDTH   : int = 900
MIN_WINDOW_HEIGHT  : int = 600
TOPBAR_HEIGHT      : int = 50

HEIGHT_BTN_PRIMARY   : int = 38
HEIGHT_BTN_SECONDARY : int = 34
HEIGHT_INPUT         : int = 36
HEIGHT_TABLE_ROW     : int = 40
HEIGHT_NAV_ITEM      : int = 40
HEIGHT_TOAST         : int = 40

# ─── Radius ───────────────────────────────────────────────────────────────────
RADIUS_CARD   : int = 10
RADIUS_BTN    : int = 8
RADIUS_INPUT  : int = 8
RADIUS_DIALOG : int = 12
RADIUS_TOAST  : int = 8


# ─── Tipografi — Lazy Singleton ───────────────────────────────────────────────
#
# CTkFont WAJIB dibuat setelah Tk root window ada.
# Jika dibuat saat module di-import (level modul), akan error:
#   RuntimeError: Too early to use font: no default root window
#
# Solusi: simpan di dict _font_cache, buat saat pertama kali dipanggil.
# Gunakan: get_font("app_title")  bukan  FONT_APP_TITLE
#
# Nama font yang tersedia:
#   app_title, heading_1, heading_2,
#   body, body_bold, small, small_bold,
#   currency_lg, currency_sm,
#   nav_item, period_label, caption

_font_cache: dict[str, ctk.CTkFont] = {}

# Definisi font: nama → (family, size, weight)
_FONT_DEFS: dict[str, tuple] = {
    "app_title"    : ("Segoe UI", 16, "bold"),
    "heading_1"    : ("Segoe UI", 15, "bold"),
    "heading_2"    : ("Segoe UI", 13, "bold"),
    "body"         : ("Segoe UI", 12, "normal"),
    "body_bold"    : ("Segoe UI", 12, "bold"),
    "small"        : ("Segoe UI", 11, "normal"),
    "small_bold"   : ("Segoe UI", 11, "bold"),
    "currency_lg"  : ("Segoe UI", 22, "bold"),
    "currency_sm"  : ("Segoe UI", 13, "bold"),
    "nav_item"     : ("Segoe UI", 12, "normal"),
    "period_label" : ("Segoe UI", 11, "normal"),
    "caption"      : ("Segoe UI", 10, "normal"),
}


def get_font(nama: str) -> ctk.CTkFont:
    """
    Kembalikan CTkFont berdasarkan nama token.
    Font dibuat satu kali saat pertama dipanggil (lazy singleton).
    Wajib dipanggil SETELAH Tk root window dibuat.

    Contoh pemakaian:
        ctk.CTkLabel(..., font=get_font("heading_1"))
        ctk.CTkButton(..., font=get_font("body_bold"))
    """
    # Kembalikan dari cache jika sudah pernah dibuat
    if nama in _font_cache:
        return _font_cache[nama]

    # Cek nama font valid
    if nama not in _FONT_DEFS:
        raise ValueError(
            f"Font '{nama}' tidak dikenal. "
            f"Pilihan: {', '.join(_FONT_DEFS.keys())}"
        )

    # Buat CTkFont baru dan simpan ke cache
    family, size, weight = _FONT_DEFS[nama]
    font = ctk.CTkFont(family=family, size=size, weight=weight)
    _font_cache[nama] = font
    return font


def reset_font_cache() -> None:
    """
    Kosongkan cache font. Dipanggil jika Tk root window di-destroy
    dan dibuat ulang (jarang terjadi, tapi aman untuk testing).
    """
    _font_cache.clear()
