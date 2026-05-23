# main.py — Entry point aplikasi Catatan Belanja
# Langkah: inisialisasi database -> buat window -> tampilkan Dashboard

import sys
from pathlib import Path

# Tambahkan src/ ke sys.path agar semua import antar modul berfungsi
_DIREKTORI_SRC = Path(__file__).resolve().parent
if str(_DIREKTORI_SRC) not in sys.path:
    sys.path.insert(0, str(_DIREKTORI_SRC))

import customtkinter as ctk

from config.database import inisialisasi_database, tutup_koneksi
from utils.theme_helper import (
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, SIDEBAR_WIDTH,
    BG_WINDOW
)


def main() -> None:
    """Titik masuk utama aplikasi."""

    # Inisialisasi database — buat tabel dan seeder jika belum ada
    koneksi = inisialisasi_database()

    # Jika database gagal, inisialisasi_database sudah menampilkan error & exit
    if koneksi is None:
        sys.exit(1)

    # Set tema default sebelum window dibuat
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("green")

    # Buat jendela utama
    window = ctk.CTk()
    window.title("Catatan Belanja")
    window.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    # Buka dalam kondisi full-size (maximize) — §7 Aturan UX
    window.state("zoomed")

    # Impor dan buat AppShell setelah window siap
    from views.app_shell import AppShell
    app = AppShell(window, koneksi)
    app.pack(fill="both", expand=True)

    # Pastikan koneksi database ditutup saat aplikasi ditutup
    def on_close() -> None:
        tutup_koneksi(koneksi)
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)

    # Jalankan event loop
    window.mainloop()


if __name__ == "__main__":
    main()
