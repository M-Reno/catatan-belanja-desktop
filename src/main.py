# main.py — Entry point aplikasi Catatan Belanja
# Langkah: inisialisasi database -> buat window -> tampilkan Dashboard

import sys
from pathlib import Path

# Tambahkan src/ ke sys.path agar semua import antar modul berfungsi
_DIREKTORI_SRC = Path(__file__).resolve().parent
if str(_DIREKTORI_SRC) not in sys.path:
    sys.path.insert(0, str(_DIREKTORI_SRC))

import customtkinter as ctk
import matplotlib.pyplot as plt

from config.database import inisialisasi_database, tutup_koneksi
from utils.theme_helper import (
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
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

    # Set ukuran window — 80% layar, di-center
    lebar_layar  = window.winfo_screenwidth()
    tinggi_layar = window.winfo_screenheight()
    lebar_window  = int(lebar_layar  * 0.8)
    tinggi_window = int(tinggi_layar * 0.8)
    pos_x = int((lebar_layar  - lebar_window)  / 2)
    pos_y = int((tinggi_layar - tinggi_window) / 2)
    window.geometry(f"{lebar_window}x{tinggi_window}+{pos_x}+{pos_y}")
    window.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    # Impor dan buat AppShell setelah window siap
    from views.app_shell import AppShell
    app = AppShell(window, koneksi)
    app.pack(fill="both", expand=True)

    def on_close() -> None:
        """
        Tutup aplikasi dengan bersih tanpa TclError sisa after-callback matplotlib.
        Urutan penting:
          1. Tutup semua figure matplotlib (batalkan internal update callbacks)
          2. Cancel SEMUA pending after() callbacks di window ini
          3. Tutup koneksi database
          4. Quit mainloop lalu destroy window
        """
        # Tutup semua figure matplotlib — ini menghentikan _update dan check_dpi_scaling
        plt.close("all")

        # Cancel semua pending after() callback yang masih terdaftar di Tk root
        # Cara ini lebih menyeluruh daripada unbind per-widget
        try:
            for after_id in window.tk.call("after", "info").split():
                try:
                    window.after_cancel(after_id)
                except Exception:
                    pass
        except Exception:
            pass

        # Tutup koneksi SQLite
        tutup_koneksi(koneksi)

        # Hentikan mainloop lalu destroy window
        window.quit()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)

    # Jalankan event loop
    window.mainloop()


if __name__ == "__main__":
    main()