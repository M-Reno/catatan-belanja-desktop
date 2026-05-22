"""
theme_helper.py — Token desain terpusat untuk seluruh UI Catatan Belanja
Semua konstanta warna, font, spacing, radius, dan dimensi ada di sini.

Sumber: Design System v1.5 §1, §9
PENTING: Warna light/dark menggunakan Tuple[str, str], bukan list,
agar kompatibel dengan type checker Pylance di VS Code.
CTk menerima keduanya saat runtime, tapi Tuple lebih type-safe.
"""

import customtkinter as ctk

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
ACCENT_PRIMARY   : tuple = ("#0D9488", "#14B8A6")   # Tombol utama, elemen aktif
ACCENT_HOVER     : tuple = ("#0F766E", "#0D9488")   # Hover tombol utama
ACCENT_SIDEBAR   : str   = "#14B8A6"                 # Item aktif di sidebar
BTN_SECONDARY_BG : tuple = ("#CCFBF1", "#1E3533")   # Background tombol sekunder
BTN_SECONDARY_TEXT: tuple = ("#0F2421", "#E8FAF8")  # Teks tombol sekunder

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

# ─── Tipografi ────────────────────────────────────────────────────────────────
FONT_APP_TITLE   = ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
FONT_HEADING_1   = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
FONT_HEADING_2   = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
FONT_BODY        = ctk.CTkFont(family="Segoe UI", size=12)
FONT_BODY_BOLD   = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
FONT_SMALL       = ctk.CTkFont(family="Segoe UI", size=11)
FONT_SMALL_BOLD  = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
FONT_CURRENCY_LG = ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
FONT_CURRENCY_SM = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
FONT_NAV_ITEM    = ctk.CTkFont(family="Segoe UI", size=12)
FONT_PERIOD_LABEL= ctk.CTkFont(family="Segoe UI", size=11)
FONT_CAPTION     = ctk.CTkFont(family="Segoe UI", size=10)

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