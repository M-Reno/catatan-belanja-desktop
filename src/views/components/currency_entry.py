"""
currency_entry.py — Komponen input field dengan format Rupiah otomatis
Digunakan oleh: budget_page.py, daftar_belanja_page.py

Spesifikasi (Design System §3.3):
- Prefix label 'Rp' di sebelah kiri entry
- Hanya menerima angka
- Auto-format titik ribuan saat FocusOut
- Strip semua non-digit sebelum simpan ke DB
"""

import customtkinter as ctk

from utils.theme_helper import (
    BG_INPUT, BORDER_COLOR, TEXT_PRIMARY, TEXT_PLACEHOLDER,
    TEXT_SECONDARY, ACCENT_PRIMARY, COLOR_DANGER,
    HEIGHT_INPUT, RADIUS_INPUT,
    get_font,
    SPACE_XS, SPACE_SM
)
from utils.format_helper import format_rupiah, parse_rupiah


class CurrencyEntry(ctk.CTkFrame):
    """
    Komponen input Rupiah dengan prefix 'Rp', auto-format titik ribuan,
    dan get_value() untuk mengambil nilai float murni tanpa format visual.
    """

    def __init__(self, master, label_teks: str = "", lebar: int = 200,
                 placeholder: str = "0", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Simpan state validasi untuk tampilan error
        self._ada_error = False

        # Label di atas field (opsional)
        if label_teks:
            self.label = ctk.CTkLabel(
                self,
                text=label_teks,
                font=get_font("body"),
                text_color=TEXT_PRIMARY
            )
            self.label.pack(anchor="w", pady=(0, SPACE_XS))

        # Frame pembungkus agar prefix 'Rp' dan entry sejajar horizontal
        self.frame_input = ctk.CTkFrame(
            self,
            fg_color=BG_INPUT,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=RADIUS_INPUT,
            height=HEIGHT_INPUT
        )
        self.frame_input.pack(fill="x")
        self.frame_input.pack_propagate(False)

        # Label prefix 'Rp' di kiri
        self.label_prefix = ctk.CTkLabel(
            self.frame_input,
            text="Rp",
            font=get_font("body_bold"),
            text_color=TEXT_SECONDARY,
            width=28
        )
        self.label_prefix.pack(side="left", padx=(SPACE_SM, 0))

        # Field input angka — tanpa border (frame sudah punya border)
        self.entry = ctk.CTkEntry(
            self.frame_input,
            placeholder_text=placeholder,
            font=get_font("body"),
            fg_color="transparent",
            border_width=0,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_PLACEHOLDER
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, SPACE_SM))

        # Label error di bawah field — tersembunyi sampai validasi gagal
        self.label_error = ctk.CTkLabel(
            self,
            text="",
            font=get_font("small"),
            text_color=COLOR_DANGER
        )
        self.label_error.pack(anchor="w")

        # Binding event — saring non-angka, format titik ribuan, warna border
        self.entry.bind("<KeyRelease>", self._saring_input)
        self.entry.bind("<FocusOut>", self._format_saat_keluar)
        self.entry.bind("<FocusIn>", self._bersihkan_format_saat_masuk)

        # add=True menambahkan binding tanpa menggantikan binding sebelumnya
        self.entry.bind("<FocusIn>", self._aktifkan_border_fokus, add=True)
        self.entry.bind("<FocusOut>", self._nonaktifkan_border_fokus, add=True)

    def _saring_input(self, event=None) -> None:
        """Buang semua karakter bukan digit — hanya angka yang diizinkan."""
        teks_sekarang = self.entry.get()
        hanya_angka = "".join(c for c in teks_sekarang if c.isdigit())

        if hanya_angka != teks_sekarang:
            self.entry.delete(0, "end")
            self.entry.insert(0, hanya_angka)

        # Hapus pesan error saat pengguna mulai mengetik ulang
        if self._ada_error:
            self.sembunyikan_error()

    def _format_saat_keluar(self, event=None) -> None:
        """Format angka dengan titik ribuan saat fokus berpindah keluar."""
        teks = self.entry.get().strip()
        if not teks:
            return
        try:
            nilai = int(teks.replace(".", ""))
            teks_terformat = f"{nilai:,}".replace(",", ".")
            self.entry.delete(0, "end")
            self.entry.insert(0, teks_terformat)
        except ValueError:
            self.entry.delete(0, "end")

    def _bersihkan_format_saat_masuk(self, event=None) -> None:
        """Hapus titik ribuan saat fokus masuk agar pengguna mudah edit."""
        teks = self.entry.get()
        hanya_angka = teks.replace(".", "")
        if hanya_angka != teks:
            self.entry.delete(0, "end")
            self.entry.insert(0, hanya_angka)

    def _aktifkan_border_fokus(self, event=None) -> None:
        """Ubah border ke warna aksen teal saat field mendapat fokus."""
        self.frame_input.configure(border_color=ACCENT_PRIMARY)

    def _nonaktifkan_border_fokus(self, event=None) -> None:
        """Kembalikan border ke warna default saat fokus berpindah."""
        if not self._ada_error:
            self.frame_input.configure(border_color=BORDER_COLOR)

    def get_value(self) -> float:
        """
        Ambil nilai float dari field — tanpa format visual.
        Kembalikan 0.0 jika field kosong atau tidak valid.
        Gunakan metode ini (bukan .get()) sebelum simpan ke DB.
        """
        teks = self.entry.get().replace(".", "").strip()
        try:
            return float(teks) if teks else 0.0
        except ValueError:
            return 0.0

    def set_value(self, nilai: float) -> None:
        """Isi field dengan nilai float, langsung diformat titik ribuan."""
        self.entry.delete(0, "end")
        if nilai > 0:
            teks_terformat = f"{int(nilai):,}".replace(",", ".")
            self.entry.insert(0, teks_terformat)

    def reset(self) -> None:
        """Kosongkan field dan hapus error. Dipanggil setelah form disimpan."""
        self.entry.delete(0, "end")
        self.sembunyikan_error()

    def tampilkan_error(self, pesan: str = "Field ini wajib diisi.") -> None:
        """Tampilkan pesan error di bawah field dan ubah border ke merah."""
        self._ada_error = True
        self.frame_input.configure(border_color=COLOR_DANGER)
        self.label_error.configure(text=pesan)

    def sembunyikan_error(self) -> None:
        """Hapus pesan error dan kembalikan border ke warna normal."""
        self._ada_error = False
        self.frame_input.configure(border_color=BORDER_COLOR)
        self.label_error.configure(text="")

    def configure_state(self, state: str) -> None:
        """
        Ubah state: 'normal' untuk input aktif, 'readonly' untuk tampil saja.
        Digunakan untuk field Harga Total yang tidak bisa diedit.
        """
        self.entry.configure(state=state)
        if state == "readonly":
            self.entry.configure(text_color=TEXT_SECONDARY)
        else:
            self.entry.configure(text_color=TEXT_PRIMARY)