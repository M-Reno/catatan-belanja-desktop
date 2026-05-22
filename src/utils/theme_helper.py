# utils/theme_helper.py
# Seluruh token UI: warna, font, spacing, radius, dan dimensi
# Sumber: Design System v1.5 §1 (Palet Warna, Tipografi, Skala Spacing, Ukuran & Radius)

import customtkinter as ctk


# =============================================================================
# WARNA — Format tuple [light, dark] sesuai konvensi CTk
# =============================================================================

# --- Background ---
BG_WINDOW        = ["#F0FDFA", "#0D1B1A"]   # Background jendela utama — putih teal / gelap teal
BG_SURFACE       = ["#FFFFFF", "#1A2E2C"]   # Card, panel, frame isi
BG_SIDEBAR       = ["#134E4A", "#0A1F1E"]   # Sidebar navigasi (selalu gelap teal)
BG_INPUT         = ["#F0FDFA", "#1E3533"]   # Background input field
BG_TABLE_ROW_ALT = ["#F0FDFA", "#1E3533"]   # Baris tabel alternating

# --- Teks ---
TEXT_PRIMARY     = ["#0F2421", "#E8FAF8"]   # Teks utama — gelap teal / hampir putih teal
TEXT_SECONDARY   = ["#4B7A75", "#7BBFBA"]   # Label, keterangan — teal medium
TEXT_SIDEBAR     = "#FFFFFF"                 # Teks di sidebar (selalu putih)
TEXT_PLACEHOLDER = ["#80C4BE", "#4B7A75"]   # Placeholder input

# --- Aksen & Tombol ---
ACCENT_PRIMARY     = ["#0D9488", "#14B8A6"]   # Tombol utama, elemen aktif — teal-600 / teal-500
ACCENT_HOVER       = ["#0F766E", "#0D9488"]   # Hover tombol utama — teal-700 / teal-600
ACCENT_SIDEBAR     = "#14B8A6"                 # Item aktif di sidebar — teal-500
BTN_SECONDARY_BG   = ["#CCFBF1", "#1E3533"]   # Background tombol sekunder
BTN_SECONDARY_TEXT = ["#0F2421", "#E8FAF8"]   # Teks tombol sekunder

# --- Status ---
COLOR_SUCCESS = ["#059669", "#34D399"]   # Konfirmasi sukses — hijau emerald
COLOR_WARNING = ["#D97706", "#FBBF24"]   # Peringatan budget < 20%
COLOR_DANGER  = ["#DC2626", "#F87171"]   # Budget negatif, hapus
COLOR_INFO    = ["#0891B2", "#22D3EE"]   # Informasi netral — cyan

# --- Border & Divider ---
BORDER_COLOR  = ["#99F6E4", "#1E3533"]   # Border komponen — teal-200 / gelap teal
DIVIDER_COLOR = ["#CCFBF1", "#162E2C"]   # Garis pemisah — teal-100 / lebih gelap

# --- Chart (matplotlib) ---
CHART_BAR        = "#0D9488"   # Warna bar default — teal-600
CHART_BAR_EMPTY  = "#CCFBF1"   # Bar hari tanpa transaksi — teal-100
CHART_BG_LIGHT   = "#FFFFFF"
CHART_BG_DARK    = "#1A2E2C"
CHART_GRID_LIGHT = "#99F6E4"   # Garis grid — teal-200
CHART_GRID_DARK  = "#1E3533"
CHART_TEXT_LIGHT = "#4B7A75"   # Label sumbu — teal medium
CHART_TEXT_DARK  = "#7BBFBA"


# =============================================================================
# TIPOGRAFI — CTkFont dipanggil saat runtime, bukan saat import
# Gunakan fungsi get_fonts() untuk mendapatkan semua font setelah CTk terinisialisasi
# =============================================================================

def get_fonts() -> dict:
    """
    Buat dan kembalikan semua definisi font sebagai dictionary.
    Harus dipanggil setelah CTk terinisialisasi (setelah CTk() dibuat).
    """
    return {
        "APP_TITLE":    ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        "HEADING_1":    ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        "HEADING_2":    ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        "BODY":         ctk.CTkFont(family="Segoe UI", size=12),
        "BODY_BOLD":    ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        "SMALL":        ctk.CTkFont(family="Segoe UI", size=11),
        "SMALL_BOLD":   ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        "CURRENCY_LG":  ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        "CURRENCY_SM":  ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        "NAV_ITEM":     ctk.CTkFont(family="Segoe UI", size=12),
        "PERIOD_LABEL": ctk.CTkFont(family="Segoe UI", size=11),
        "CAPTION":      ctk.CTkFont(family="Segoe UI", size=10),
    }


# Placeholder font — diisi oleh main.py setelah CTk terinisialisasi
FONT_APP_TITLE   = None
FONT_HEADING_1   = None
FONT_HEADING_2   = None
FONT_BODY        = None
FONT_BODY_BOLD   = None
FONT_SMALL       = None
FONT_SMALL_BOLD  = None
FONT_CURRENCY_LG = None
FONT_CURRENCY_SM = None
FONT_NAV_ITEM    = None
FONT_PERIOD_LABEL= None
FONT_CAPTION     = None


def init_fonts():
    """
    Inisialisasi semua variabel font global.
    Dipanggil dari main.py tepat setelah CTk() dibuat.
    """
    global FONT_APP_TITLE, FONT_HEADING_1, FONT_HEADING_2
    global FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD
    global FONT_CURRENCY_LG, FONT_CURRENCY_SM
    global FONT_NAV_ITEM, FONT_PERIOD_LABEL, FONT_CAPTION

    fonts = get_fonts()
    FONT_APP_TITLE   = fonts["APP_TITLE"]
    FONT_HEADING_1   = fonts["HEADING_1"]
    FONT_HEADING_2   = fonts["HEADING_2"]
    FONT_BODY        = fonts["BODY"]
    FONT_BODY_BOLD   = fonts["BODY_BOLD"]
    FONT_SMALL       = fonts["SMALL"]
    FONT_SMALL_BOLD  = fonts["SMALL_BOLD"]
    FONT_CURRENCY_LG = fonts["CURRENCY_LG"]
    FONT_CURRENCY_SM = fonts["CURRENCY_SM"]
    FONT_NAV_ITEM    = fonts["NAV_ITEM"]
    FONT_PERIOD_LABEL= fonts["PERIOD_LABEL"]
    FONT_CAPTION     = fonts["CAPTION"]


# =============================================================================
# SPACING — Dalam pixel
# =============================================================================

SPACE_XS  = 4
SPACE_SM  = 8
SPACE_MD  = 12
SPACE_LG  = 16
SPACE_XL  = 24
SPACE_2XL = 32
SPACE_3XL = 48


# =============================================================================
# UKURAN & RADIUS
# =============================================================================

# Dimensi komponen
SIDEBAR_WIDTH      = 200
MIN_WINDOW_WIDTH   = 900
MIN_WINDOW_HEIGHT  = 600
TOPBAR_HEIGHT      = 50

# Tinggi komponen
HEIGHT_BTN_PRIMARY   = 38
HEIGHT_BTN_SECONDARY = 34
HEIGHT_INPUT         = 36
HEIGHT_TABLE_ROW     = 40
HEIGHT_NAV_ITEM      = 40
HEIGHT_TOAST         = 40

# Corner radius
RADIUS_CARD   = 10
RADIUS_BTN    = 8
RADIUS_INPUT  = 8
RADIUS_DIALOG = 12
RADIUS_TOAST  = 8
