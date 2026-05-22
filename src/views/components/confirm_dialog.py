"""
confirm_dialog.py — Dialog konfirmasi modal untuk aksi hapus dan konfirmasi kritis
Digunakan oleh: semua page yang memiliki aksi hapus data

Spesifikasi (Design System §3.7):
- CTkToplevel, ukuran 360×160px, tidak bisa di-resize
- grab_set() wajib dipanggil (modal)
- Tombol kiri: Sekunder (Batal), tombol kanan: Bahaya atau Primer
- Binding Escape = Batal, Enter = Konfirmasi
"""

import customtkinter as ctk
from typing import Callable, Optional

from utils.theme_helper import (
    BG_SURFACE, TEXT_PRIMARY,
    COLOR_DANGER, ACCENT_PRIMARY, ACCENT_HOVER,
    BTN_SECONDARY_BG, BTN_SECONDARY_TEXT, BORDER_COLOR,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL,
    HEIGHT_BTN_SECONDARY,
    RADIUS_BTN,
    SPACE_MD, SPACE_LG, SPACE_XL
)


class ConfirmDialog(ctk.CTkToplevel):
    """
    Dialog konfirmasi modal yang memblokir interaksi ke jendela utama.
    Tipe 'hapus': tombol konfirmasi merah (outline).
    Tipe 'konfirmasi': tombol konfirmasi teal (filled).
    """

    def __init__(self, master, pesan: str, label_konfirmasi: str = "Hapus",
                 tipe: str = "hapus", callback_konfirmasi=None):
        super().__init__(master)

        self._callback = callback_konfirmasi
        self._dikonfirmasi = False

        # Konfigurasi jendela
        self.title("Konfirmasi")
        self.geometry("360x160")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)

        # Modal — blokir interaksi ke jendela induk sampai dialog ditutup
        self.grab_set()

        # Posisikan di tengah jendela induk
        self._pusatkan_dialog(master)

        # Keyboard shortcut: Escape = Batal, Enter = Konfirmasi
        self.bind("<Escape>", lambda e: self._klik_batal())
        self.bind("<Return>", lambda e: self._klik_konfirmasi())

        self._bangun_ui(pesan, label_konfirmasi, tipe)

        # Fokus ke tombol Batal secara default (lebih aman dari hapus tidak sengaja)
        self.after(100, self.tombol_batal.focus_set)

    def _pusatkan_dialog(self, master) -> None:
        """Posisikan dialog tepat di tengah jendela induk."""
        self.update_idletasks()
        try:
            x = master.winfo_rootx() + (master.winfo_width() // 2) - 180
            y = master.winfo_rooty() + (master.winfo_height() // 2) - 80
            self.geometry(f"360x160+{x}+{y}")
        except Exception:
            pass

    def _bangun_ui(self, pesan: str, label_konfirmasi: str, tipe: str) -> None:
        """Bangun semua widget di dalam dialog."""

        frame_utama = ctk.CTkFrame(self, fg_color="transparent")
        frame_utama.pack(fill="both", expand=True, padx=SPACE_XL, pady=SPACE_LG)

        # Baris atas: ikon + pesan
        frame_pesan = ctk.CTkFrame(frame_utama, fg_color="transparent")
        frame_pesan.pack(fill="x", pady=(0, SPACE_LG))

        # Warna ikon menyesuaikan tipe aksi — gunakan string hex langsung
        # agar Pylance tidak komplain soal tuple vs str
        warna_ikon = "#DC2626" if tipe == "hapus" else "#0D9488"

        label_ikon = ctk.CTkLabel(
            frame_pesan,
            text="⚠",
            font=ctk.CTkFont(family="Segoe UI", size=20),
            text_color=warna_ikon,
            width=30
        )
        label_ikon.pack(side="left", padx=(0, SPACE_MD))

        # Teks pesan konfirmasi, rata kiri, maks 2 baris
        label_pesan = ctk.CTkLabel(
            frame_pesan,
            text=pesan,
            font=FONT_BODY,
            text_color=TEXT_PRIMARY,
            wraplength=270,
            justify="left"
        )
        label_pesan.pack(side="left", fill="x", expand=True)

        # Baris bawah: tombol Batal (kiri) dan Konfirmasi (kanan)
        frame_tombol = ctk.CTkFrame(frame_utama, fg_color="transparent")
        frame_tombol.pack(fill="x")

        # Tombol Batal — selalu sekunder
        self.tombol_batal = ctk.CTkButton(
            frame_tombol,
            text="Batal",
            font=FONT_BODY,
            fg_color=BTN_SECONDARY_BG,
            hover_color=BORDER_COLOR,
            text_color=BTN_SECONDARY_TEXT,
            height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            width=100,
            command=self._klik_batal
        )
        self.tombol_batal.pack(side="left")

        # Tombol Konfirmasi — merah outline jika hapus, teal filled jika konfirmasi
        if tipe == "hapus":
            self.tombol_konfirmasi = ctk.CTkButton(
                frame_tombol,
                text=label_konfirmasi,
                font=FONT_BODY_BOLD,
                fg_color="transparent",
                hover_color="#FEE2E2",    # merah muda saat hover
                text_color="#DC2626",    # teks merah
                border_width=1,
                border_color="#DC2626",
                height=HEIGHT_BTN_SECONDARY,
                corner_radius=RADIUS_BTN,
                width=120,
                command=self._klik_konfirmasi
            )
        else:
            self.tombol_konfirmasi = ctk.CTkButton(
                frame_tombol,
                text=label_konfirmasi,
                font=FONT_BODY_BOLD,
                fg_color=ACCENT_PRIMARY,
                hover_color=ACCENT_HOVER,
                text_color="#FFFFFF",
                height=HEIGHT_BTN_SECONDARY,
                corner_radius=RADIUS_BTN,
                width=120,
                command=self._klik_konfirmasi
            )

        self.tombol_konfirmasi.pack(side="right")

    def _klik_batal(self) -> None:
        """Tutup dialog tanpa menjalankan aksi."""
        self._dikonfirmasi = False
        self.destroy()

    def _klik_konfirmasi(self) -> None:
        """Tutup dialog lalu jalankan callback konfirmasi."""
        self._dikonfirmasi = True
        self.destroy()
        if self._callback:
            self._callback()

    def dikonfirmasi(self) -> bool:
        """Kembalikan True jika pengguna memilih konfirmasi."""
        return self._dikonfirmasi


# ── Fungsi pintasan ───────────────────────────────────────────────────────────

def tampilkan_konfirmasi_hapus(master, nama_item: str,
                                callback: Callable) -> None:
    """
    Pintasan dialog hapus — otomatis format pesan dengan nama item.
    Digunakan oleh semua controller yang punya aksi hapus.
    """
    pesan = (
        f"Apakah Anda yakin ingin menghapus '{nama_item}'?\n"
        "Data yang dihapus tidak dapat dikembalikan."
    )
    ConfirmDialog(
        master,
        pesan=pesan,
        label_konfirmasi="Hapus",
        tipe="hapus",
        callback_konfirmasi=callback
    )


def tampilkan_konfirmasi_umum(master, pesan: str, label: str,
                               callback: Callable) -> None:
    """
    Pintasan dialog konfirmasi non-hapus, misalnya 'Ya, Simpan'.
    """
    ConfirmDialog(
        master,
        pesan=pesan,
        label_konfirmasi=label,
        tipe="konfirmasi",
        callback_konfirmasi=callback
    )