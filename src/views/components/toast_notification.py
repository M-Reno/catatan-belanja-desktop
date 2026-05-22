"""
toast_notification.py — Notifikasi singkat yang muncul otomatis dan hilang sendiri
Digunakan oleh: semua page setelah aksi simpan, hapus, atau ekspor berhasil

Spesifikasi (Design System §3.8):
- Muncul di pojok kanan bawah area konten, 24px dari tepi
- Durasi tampil: 2500ms, lalu hilang otomatis
- Sukses: COLOR_SUCCESS, ikon ✓
- Error: COLOR_DANGER, ikon ✕
- Teks singkat, maks 50 karakter
"""

import customtkinter as ctk

from utils.theme_helper import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_INFO,
    FONT_BODY,
    HEIGHT_TOAST, RADIUS_TOAST,
    SPACE_LG
)

# Durasi toast tampil dalam milidetik sebelum hilang otomatis
DURASI_TOAST_MS = 2500


class ToastNotification(ctk.CTkLabel):
    """
    Label notifikasi singkat yang muncul di pojok kanan bawah area konten.
    Hilang otomatis setelah DURASI_TOAST_MS milidetik.
    """

    def __init__(self, master, pesan: str, tipe: str = "sukses"):
        """
        Inisialisasi toast dan langsung tampilkan.

        Parameter:
            master  — frame konten tempat toast ditampilkan (bukan jendela utama)
            pesan   — teks singkat yang ditampilkan (maks 50 karakter)
            tipe    — 'sukses', 'error', atau 'info'
        """
        # Pilih ikon dan warna berdasarkan tipe notifikasi
        ikon, warna_bg = self._ambil_konfigurasi(tipe)

        super().__init__(
            master,
            text=f"{ikon}  {pesan}",
            font=FONT_BODY,
            fg_color=warna_bg,
            text_color="#FFFFFF",
            corner_radius=RADIUS_TOAST,
            height=HEIGHT_TOAST,
            padx=SPACE_LG
        )

        # Tampilkan di pojok kanan bawah area konten — 24px dari tepi
        self.place(relx=1.0, rely=1.0, anchor="se", x=-24, y=-24)

        # Jadwalkan penghapusan toast setelah durasi habis
        self.after(DURASI_TOAST_MS, self._hilangkan)

    def _ambil_konfigurasi(self, tipe: str) -> tuple:
        """Kembalikan tuple (ikon, warna_background) berdasarkan tipe toast."""
        if tipe == "sukses":
            return "✓", COLOR_SUCCESS
        elif tipe == "error":
            return "✕", COLOR_DANGER
        else:
            # Tipe 'info' atau tipe lain yang tidak dikenal
            return "ℹ", COLOR_INFO

    def _hilangkan(self):
        """
        Hapus widget toast dari tampilan.
        Gunakan try-except untuk mengantisipasi jika widget sudah hancur
        (misalnya pengguna menutup halaman sebelum durasi habis).
        """
        try:
            self.destroy()
        except Exception:
            pass


def tampilkan_toast(master, pesan: str, tipe: str = "sukses") -> ToastNotification:
    """
    Fungsi pintasan untuk membuat dan menampilkan toast notifikasi.
    Kembalikan instance toast agar caller bisa menyimpan referensinya jika perlu.

    Parameter:
        master  — frame konten tempat toast ditampilkan
        pesan   — teks yang ditampilkan
        tipe    — 'sukses', 'error', atau 'info'
    """
    return ToastNotification(master, pesan, tipe)


def tampilkan_toast_sukses(master, pesan: str = "Data berhasil disimpan") -> ToastNotification:
    """Pintasan untuk toast sukses — paling sering digunakan setelah simpan."""
    return tampilkan_toast(master, pesan, tipe="sukses")


def tampilkan_toast_error(master, pesan: str = "Terjadi kesalahan") -> ToastNotification:
    """Pintasan untuk toast error — digunakan saat operasi gagal."""
    return tampilkan_toast(master, pesan, tipe="error")


def tampilkan_toast_info(master, pesan: str) -> ToastNotification:
    """Pintasan untuk toast informasi — digunakan untuk pesan netral."""
    return tampilkan_toast(master, pesan, tipe="info")