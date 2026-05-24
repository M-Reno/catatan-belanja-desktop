# views/daftar_belanja_page.py
"""
Halaman Daftar Belanja — State A (seleksi periode) + State B (daftar item).
Sesuai PRD §5.3 FR-DL-0 s.d. FR-DL-6, Design System §4.3.
"""

import sqlite3
from datetime import date
from typing import Callable, Optional
import customtkinter as ctk

from controllers.belanja_controller import BelanjaController
from views.components.confirm_dialog import tampilkan_konfirmasi_hapus
from views.components.toast_notification import tampilkan_toast_sukses, tampilkan_toast_error
from utils.format_helper import format_rupiah, format_jumlah, hitung_harga_total
from utils.theme_helper import (
    BG_WINDOW, BG_SURFACE, BG_INPUT, BG_TABLE_ROW_ALT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_PLACEHOLDER,
    ACCENT_PRIMARY, ACCENT_HOVER,
    BTN_SECONDARY_BG, BTN_SECONDARY_TEXT,
    COLOR_DANGER, BORDER_COLOR,
    SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL,
    RADIUS_CARD, RADIUS_BTN, RADIUS_INPUT,
    HEIGHT_INPUT, HEIGHT_BTN_PRIMARY, HEIGHT_BTN_SECONDARY, HEIGHT_TABLE_ROW,
    get_font,
)

# Nama bulan untuk dropdown dan label
NAMA_BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def _c(token):
    """Ambil warna sesuai mode aktif. Dipanggil saat dibutuhkan, bukan saat init."""
    if isinstance(token, (list, tuple)):
        return token[1] if ctk.get_appearance_mode() == "Dark" else token[0]
    return token


# =============================================================================
# KOMPONEN AUTOCOMPLETE ENTRY
# =============================================================================

class _AutocompleteEntry(ctk.CTkFrame):
    """
    Entry dengan dropdown saran nama barang dari master data.
    Saat pengguna mengetik, saran muncul di bawah field.
    Saat saran dipilih, callback dipanggil dengan data barang yang dipilih.
    """

    def __init__(self, master, controller: BelanjaController,
                 callback_pilih, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._controller = controller
        self._callback   = callback_pilih
        self._dropdown   = None

        # Field input nama barang
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Ketik nama barang...",
            font=get_font("body"),
            fg_color=BG_INPUT,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_PLACEHOLDER,
            height=HEIGHT_INPUT,
            corner_radius=RADIUS_INPUT,
        )
        self.entry.pack(fill="x")

        self.entry.bind("<KeyRelease>", self._pada_ketik)
        self.entry.bind("<FocusOut>", self._tutup_dropdown_terlambat)
        self.entry.bind("<Escape>", lambda e: self._tutup_dropdown())

        # Callback Enter yang bisa diset dari luar untuk submit form
        self._callback_enter: Optional[Callable[[], None]] = None
        self.entry.bind("<Return>", lambda e: self._submit_jika_enter())

    def _pada_ketik(self, event=None) -> None:
        """Setiap ketukan: cari saran dan perbarui dropdown."""
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return

        kata = self.entry.get().strip()

        # Beritahu parent bahwa teks berubah (untuk cek auto-fill kategori)
        if self._callback:
            self._callback(kata, None)

        if len(kata) < 1:
            self._tutup_dropdown()
            return

        saran = self._controller.cari_nama_barang(kata)
        if saran:
            self._tampilkan_dropdown(saran)
        else:
            self._tutup_dropdown()

    def _tampilkan_dropdown(self, saran: list) -> None:
        """Tampilkan dropdown saran di bawah field menggunakan place overlay."""
        self._tutup_dropdown()

        self._dropdown = ctk.CTkFrame(
            self.winfo_toplevel(),
            fg_color=_c(BG_SURFACE),
            border_width=1,
            border_color=_c(BORDER_COLOR),
            corner_radius=RADIUS_INPUT,
        )

        self.update_idletasks()
        x = self.entry.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
        y = (self.entry.winfo_rooty() - self.winfo_toplevel().winfo_rooty()
             + self.entry.winfo_height())
        lebar = self.entry.winfo_width()
        self._dropdown.place(x=x, y=y, width=lebar)

        # Batasi 6 saran agar tidak terlalu panjang
        for baris in saran[:6]:
            nama = baris["nama_barang"]
            ctk.CTkButton(
                self._dropdown,
                text=nama,
                font=get_font("body"),
                fg_color="transparent",
                hover_color=_c(BTN_SECONDARY_BG),
                text_color=_c(TEXT_PRIMARY),
                anchor="w",
                height=32,
                corner_radius=0,
                command=lambda b=baris: self._pilih_saran(b),
            ).pack(fill="x", padx=SPACE_XS, pady=1)

    def _pilih_saran(self, baris) -> None:
        """Isi entry dengan nama yang dipilih dan panggil callback."""
        self.entry.delete(0, "end")
        self.entry.insert(0, baris["nama_barang"])
        self._tutup_dropdown()
        if self._callback:
            self._callback(baris["nama_barang"], baris)

    def _tutup_dropdown(self) -> None:
        """Hancurkan widget dropdown."""
        if self._dropdown:
            try:
                self._dropdown.destroy()
            except Exception:
                pass
            self._dropdown = None

    def _tutup_dropdown_terlambat(self, event=None) -> None:
        """Tutup dropdown dengan jeda agar klik item sempat diproses."""
        self.after(150, self._tutup_dropdown)

    def _submit_jika_enter(self) -> None:
        """Panggil callback Enter dari luar jika dropdown tertutup."""
        if self._dropdown is None and self._callback_enter:
            self._callback_enter()

    def get(self) -> str:
        return self.entry.get()

    def set(self, teks: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, teks)

    def reset(self) -> None:
        self.entry.delete(0, "end")
        self._tutup_dropdown()

    def fokus(self) -> None:
        self.entry.focus_set()


# =============================================================================
# HALAMAN UTAMA
# =============================================================================

class DaftarBelanjaPage(ctk.CTkFrame):
    """
    Halaman Daftar Belanja dengan dua state:
    State A — seleksi periode (bulan + minggu)
    State B — daftar item belanja pada periode yang terpilih
    """

    def __init__(self, master, koneksi: sqlite3.Connection, navigasi_ke):
        super().__init__(master, fg_color=BG_WINDOW, corner_radius=0)

        self._koneksi  = koneksi
        self._navigasi = navigasi_ke
        self._ctrl     = BelanjaController(koneksi)

        # Status periode terpilih
        self._id_periode: int = 0
        self._periode_data    = None

        # Callback untuk refresh dashboard setelah item ditambah
        self._callback_refresh_dashboard = None

        # Status form
        self._mode_edit              = False
        self._id_edit                = 0
        self._id_kategori_terkunci   = 0

        # Tahun dan bulan aktif untuk State A
        self._tahun_aktif  = date.today().year
        self._bulan_aktif  = date.today().month
        self._minggu_aktif = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._frame_state_a = self._buat_state_a()
        self._frame_state_b = self._buat_state_b()

        self._tampilkan_state("A")

    # ─── MANAJEMEN STATE ──────────────────────────────────────────────────────

    def _tampilkan_state(self, state: str) -> None:
        """Ganti tampilan antara State A dan State B."""
        if state == "A":
            self._frame_state_b.grid_remove()
            self._frame_state_a.grid(row=0, column=0, sticky="nsew")
            self._muat_state_a()
        else:
            self._frame_state_a.grid_remove()
            self._frame_state_b.grid(row=0, column=0, sticky="nsew")
            self._muat_state_b()

    # =========================================================================
    # STATE A — SELEKSI PERIODE
    # =========================================================================

    def _buat_state_a(self) -> ctk.CTkFrame:
        """Buat widget State A. Dipanggil sekali saat init."""
        frame = ctk.CTkFrame(self, fg_color=BG_WINDOW, corner_radius=0)
        frame.grid_columnconfigure(0, weight=1)

        # Header
        fh = ctk.CTkFrame(frame, fg_color="transparent")
        fh.grid(row=0, column=0, sticky="ew", padx=SPACE_XL, pady=(SPACE_XL, SPACE_SM))
        ctk.CTkLabel(fh, text="Daftar Belanja", font=get_font("heading_1"),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(fh, text="Pilih periode untuk mulai mencatat",
                     font=get_font("small"), text_color=TEXT_SECONDARY,
                     anchor="w").pack(anchor="w", pady=(SPACE_XS, 0))

        # Divider
        ctk.CTkFrame(frame, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=1, column=0, sticky="ew", padx=SPACE_XL)

        # Card seleksi
        card = ctk.CTkFrame(frame, fg_color=BG_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=BORDER_COLOR)
        card.grid(row=2, column=0, sticky="ew", padx=SPACE_XL, pady=SPACE_XL)
        card.grid_columnconfigure(1, weight=1)

        # Baris bulan
        ctk.CTkLabel(card, text="Bulan", font=get_font("body"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w",
                            padx=(SPACE_XL, SPACE_MD), pady=(SPACE_XL, SPACE_SM))

        self._combo_bulan_a = ctk.CTkComboBox(
            card, values=NAMA_BULAN, font=get_font("body"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            button_color=ACCENT_PRIMARY, button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_SURFACE, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BTN_SECONDARY_BG, text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT, state="readonly",
            command=self._pada_ganti_bulan,
        )
        self._combo_bulan_a.grid(row=0, column=1, sticky="ew",
                                  padx=(0, SPACE_XL), pady=(SPACE_XL, SPACE_SM))

        ctk.CTkFrame(card, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=1, column=0, columnspan=2, sticky="ew",
                            padx=SPACE_XL, pady=SPACE_SM)

        # Baris pilih minggu
        ctk.CTkLabel(card, text="Minggu ke-", font=get_font("body"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=2, column=0, sticky="w",
                            padx=(SPACE_XL, SPACE_MD), pady=SPACE_SM)

        self._frame_minggu = ctk.CTkFrame(card, fg_color="transparent")
        self._frame_minggu.grid(row=2, column=1, sticky="w",
                                 padx=(0, SPACE_XL), pady=SPACE_SM)
        self._tombol_minggu: list = []
        self._buat_tombol_minggu()

        # Label rentang tanggal
        self._label_rentang_a = ctk.CTkLabel(
            card, text="", font=get_font("period_label"),
            text_color=TEXT_SECONDARY, anchor="w")
        self._label_rentang_a.grid(row=3, column=0, columnspan=2, sticky="w",
                                    padx=SPACE_XL, pady=SPACE_SM)

        # Label peringatan belum ada budget
        self._label_peringatan_a = ctk.CTkLabel(
            card, text="", font=get_font("small"),
            text_color=COLOR_DANGER, anchor="w")
        self._label_peringatan_a.grid(row=4, column=0, columnspan=2, sticky="w",
                                       padx=SPACE_XL, pady=(0, SPACE_SM))

        # Tombol Buka
        self._btn_buka = ctk.CTkButton(
            card, text="Buka", font=get_font("body_bold"),
            fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            height=HEIGHT_BTN_PRIMARY, corner_radius=RADIUS_BTN, state="disabled",
            command=self._klik_buka_periode,
        )
        self._btn_buka.grid(row=5, column=0, columnspan=2, sticky="ew",
                             padx=SPACE_XL, pady=(SPACE_SM, SPACE_XL))

        return frame

    def _buat_tombol_minggu(self) -> None:
        """Buat tombol minggu 1-4 (dan ke-5 jika perlu)."""
        for w in self._frame_minggu.winfo_children():
            w.destroy()
        self._tombol_minggu.clear()

        import calendar as _cal
        _, hari_terakhir = _cal.monthrange(self._tahun_aktif, self._bulan_aktif)
        jumlah = 5 if hari_terakhir >= 29 else 4

        for i in range(1, jumlah + 1):
            btn = ctk.CTkButton(
                self._frame_minggu, text=str(i), font=get_font("body_bold"),
                width=44, height=44, corner_radius=RADIUS_BTN,
                fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
                text_color=TEXT_PRIMARY,
                command=lambda m=i: self._pilih_minggu(m),
            )
            btn.pack(side="left", padx=(0, SPACE_SM))
            self._tombol_minggu.append(btn)

    def _pada_ganti_bulan(self, nilai: str = "") -> None:
        """Saat dropdown bulan berubah, reset pilihan minggu."""
        idx = NAMA_BULAN.index(self._combo_bulan_a.get())
        self._bulan_aktif  = idx + 1
        self._minggu_aktif = 0
        self._buat_tombol_minggu()
        self._label_rentang_a.configure(text="")
        self._label_peringatan_a.configure(text="")
        self._btn_buka.configure(state="disabled")

    def _pilih_minggu(self, minggu_ke: int) -> None:
        """Klik tombol minggu: update style dan cek ketersediaan budget."""
        self._minggu_aktif = minggu_ke

        for i, btn in enumerate(self._tombol_minggu, start=1):
            if i == minggu_ke:
                btn.configure(fg_color=ACCENT_PRIMARY, text_color="#FFFFFF",
                               hover_color=ACCENT_HOVER)
            else:
                btn.configure(fg_color=BTN_SECONDARY_BG, text_color=TEXT_PRIMARY,
                               hover_color=BORDER_COLOR)

        periode = self._ctrl.ambil_periode_by_minggu(
            minggu_ke, self._bulan_aktif, self._tahun_aktif)

        if periode:
            def _fmt(d): return "-".join(reversed(d.split("-")))
            rentang = f"{_fmt(periode['tgl_mulai'])}  –  {_fmt(periode['tgl_selesai'])}"
            self._label_rentang_a.configure(text=rentang)
            self._label_peringatan_a.configure(text="")
            self._btn_buka.configure(state="normal")
            self._periode_data = periode
        else:
            self._label_rentang_a.configure(text="")
            self._label_peringatan_a.configure(
                text="Belum ada budget untuk minggu ini.")
            self._btn_buka.configure(state="disabled")
            self._periode_data = None

    def _klik_buka_periode(self) -> None:
        """Pindah ke State B setelah periode dikonfirmasi."""
        if self._periode_data is None:
            return
        self._id_periode = self._periode_data["id_periode"]
        self._tampilkan_state("B")

    def _muat_state_a(self) -> None:
        """Sinkronkan dropdown bulan saat State A ditampilkan."""
        self._combo_bulan_a.set(NAMA_BULAN[self._bulan_aktif - 1])
        self._buat_tombol_minggu()
        if self._minggu_aktif > 0:
            self._pilih_minggu(self._minggu_aktif)

    # =========================================================================
    # STATE B — DAFTAR ITEM
    # =========================================================================

    def _buat_state_b(self) -> ctk.CTkFrame:
        """Buat widget State B. Dipanggil sekali saat init."""
        frame = ctk.CTkFrame(self, fg_color=BG_WINDOW, corner_radius=0)
        frame.grid_columnconfigure(0, weight=1)
        # Baris 0: header (compact), baris 1: divider, baris 2: isi (expand)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_rowconfigure(2, weight=1)

        # Header
        fh = ctk.CTkFrame(frame, fg_color="transparent")
        fh.grid(row=0, column=0, sticky="ew", padx=SPACE_XL, pady=(SPACE_XL, SPACE_SM))
        fh.grid_columnconfigure(0, weight=1)

        fj = ctk.CTkFrame(fh, fg_color="transparent")
        fj.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(fj, text="Daftar Belanja", font=get_font("heading_1"),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        self._label_periode_b = ctk.CTkLabel(
            fj, text="", font=get_font("period_label"),
            text_color=TEXT_SECONDARY, anchor="w")
        self._label_periode_b.pack(anchor="w")

        ctk.CTkButton(
            fh, text="← Ganti Periode", font=get_font("body"),
            fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
            corner_radius=RADIUS_BTN,
            command=lambda: self._tampilkan_state("A"),
        ).grid(row=0, column=1, sticky="e")

        # Divider
        ctk.CTkFrame(frame, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=1, column=0, sticky="ew", padx=SPACE_XL)

        # Isi utama — row 2 expand agar tabel selalu dapat ruang
        fi = ctk.CTkFrame(frame, fg_color="transparent")
        fi.grid(row=2, column=0, sticky="nsew", padx=SPACE_XL, pady=SPACE_XL)
        fi.grid_columnconfigure(0, weight=1)
        fi.grid_rowconfigure(0, weight=0)  # Form: compact, tidak expand
        fi.grid_rowconfigure(1, weight=1)  # Tabel: mengisi sisa ruang

        self._buat_form(fi)
        self._buat_tabel(fi)

        return frame

    # ── FORM ─────────────────────────────────────────────────────────────────

    def _buat_form(self, parent) -> None:
        """
        Card form input — layout grid horizontal sangat kompak.

        Baris label  : [Nama Barang]   [Kategori]      [Jumlah & Satuan]   [Harga Sat]   [Total]
        Baris input  : [entry_nama   ] [combo_kat    ] [entry_jml|combo_st] [Rp|entry_hs] [Rp|entry_ht]
        Baris bawah  : [error kiri..................................................] [Batal] [Tambah]

        Semua field dalam SATU baris grid — form hanya setinggi ~100px.
        """
        card = ctk.CTkFrame(parent, fg_color=BG_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=BORDER_COLOR)
        card.grid(row=0, column=0, sticky="ew", pady=(0, SPACE_MD))
        # card tidak punya weight row — semua row compact, tidak expand
        for r in range(5):
            card.grid_rowconfigure(r, weight=0)

        # 5 kolom konten + padding sisi
        # col 0: Nama Barang (weight 3)
        # col 1: Kategori    (weight 2)
        # col 2: Jumlah+Sat  (weight 2, fixed internal)
        # col 3: Harga Sat   (weight 2)
        # col 4: Harga Total (weight 2)
        card.grid_columnconfigure(0, weight=3)
        card.grid_columnconfigure(1, weight=2)
        card.grid_columnconfigure(2, weight=2)
        card.grid_columnconfigure(3, weight=2)
        card.grid_columnconfigure(4, weight=2)

        _PX = SPACE_SM          # gap antar kolom
        _PX_L = SPACE_LG        # padding kiri card
        _PX_R = SPACE_LG        # padding kanan card

        # ── Baris 0: judul + label field ─────────────────────────────────────
        # Judul form (span semua kolom)
        self._label_judul_form = ctk.CTkLabel(
            card, text="Tambah Barang", font=get_font("heading_2"),
            text_color=TEXT_PRIMARY, anchor="w")
        self._label_judul_form.grid(
            row=0, column=0, columnspan=5, sticky="w",
            padx=(_PX_L, 0), pady=(SPACE_MD, SPACE_XS))

        # Label tiap field
        for col, teks in enumerate(
                ["Nama Barang", "Kategori", "Jumlah & Satuan",
                 "Harga Satuan", "Harga Total"]):
            px_l = _PX_L if col == 0 else _PX
            px_r = _PX_R if col == 4 else _PX
            ctk.CTkLabel(card, text=teks, font=get_font("small"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=1, column=col, sticky="w",
                                padx=(px_l, px_r), pady=(0, SPACE_XS))

        # ── Baris 1: input field ──────────────────────────────────────────────

        # — Nama Barang (col 0) —
        self._entry_nama = _AutocompleteEntry(
            card, controller=self._ctrl,
            callback_pilih=self._pada_pilih_nama_barang)
        self._entry_nama.grid(row=2, column=0, sticky="ew",
                              padx=(_PX_L, _PX), pady=(0, SPACE_XS))
        self._entry_nama._callback_enter = self._klik_simpan

        # — Kategori (col 1) —
        self._combo_kategori = ctk.CTkComboBox(
            card, values=["-- Pilih Kategori --"], font=get_font("body"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            button_color=ACCENT_PRIMARY, button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_SURFACE, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BTN_SECONDARY_BG, text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT, state="readonly",
            command=self._pada_ganti_kategori)
        self._combo_kategori.grid(row=2, column=1, sticky="ew",
                                   padx=(_PX, _PX), pady=(0, SPACE_XS))

        # — Jumlah + Satuan dalam satu sub-frame (col 2) —
        fjs = ctk.CTkFrame(card, fg_color="transparent")
        fjs.grid(row=2, column=2, sticky="ew", padx=(_PX, _PX), pady=(0, SPACE_XS))
        fjs.grid_columnconfigure(0, weight=1)

        self._entry_jumlah = ctk.CTkEntry(
            fjs, placeholder_text="0", font=get_font("body"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_PLACEHOLDER,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT)
        self._entry_jumlah.grid(row=0, column=0, sticky="ew", padx=(0, SPACE_XS))
        self._entry_jumlah.bind("<KeyRelease>", self._hitung_total_otomatis)

        self._combo_satuan = ctk.CTkComboBox(
            fjs, values=["-- Satuan --"], font=get_font("body"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            button_color=ACCENT_PRIMARY, button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_SURFACE, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BTN_SECONDARY_BG, text_color=TEXT_PRIMARY,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT,
            width=100, state="readonly")
        self._combo_satuan.grid(row=0, column=1)

        # — Harga Satuan (col 3) —
        fhs = ctk.CTkFrame(card, fg_color="transparent")
        fhs.grid(row=2, column=3, sticky="ew", padx=(_PX, _PX), pady=(0, SPACE_XS))
        fhs.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fhs, text="Rp", font=get_font("body_bold"),
                     text_color=TEXT_SECONDARY, width=22
                     ).grid(row=0, column=0, padx=(0, SPACE_XS))
        self._entry_harga_satuan = ctk.CTkEntry(
            fhs, placeholder_text="0", font=get_font("body"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_PLACEHOLDER,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT)
        self._entry_harga_satuan.grid(row=0, column=1, sticky="ew")
        self._entry_harga_satuan.bind("<KeyRelease>", self._pada_ketik_harga)
        self._entry_harga_satuan.bind("<FocusOut>", self._format_harga_satuan)
        self._entry_harga_satuan.bind("<FocusIn>", self._bersihkan_format_harga)

        # — Harga Total readonly (col 4) —
        fht = ctk.CTkFrame(card, fg_color="transparent")
        fht.grid(row=2, column=4, sticky="ew", padx=(_PX, _PX_R), pady=(0, SPACE_XS))
        fht.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fht, text="Rp", font=get_font("body_bold"),
                     text_color=TEXT_SECONDARY, width=22
                     ).grid(row=0, column=0, padx=(0, SPACE_XS))
        self._entry_harga_total = ctk.CTkEntry(
            fht, font=get_font("currency_sm"),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_SECONDARY, height=HEIGHT_INPUT,
            corner_radius=RADIUS_INPUT, state="readonly")
        self._entry_harga_total.grid(row=0, column=1, sticky="ew")

        # ── Baris 2: error messages ───────────────────────────────────────────
        ferr = ctk.CTkFrame(card, fg_color="transparent")
        ferr.grid(row=3, column=0, columnspan=5, sticky="w",
                  padx=(_PX_L, _PX_R), pady=(SPACE_XS, 0))

        self._label_error_kategori = ctk.CTkLabel(
            ferr, text="", font=get_font("small"),
            text_color=COLOR_DANGER, anchor="w")
        self._label_error_kategori.pack(side="left", padx=(0, SPACE_MD))

        self._label_error_jumlah = ctk.CTkLabel(
            ferr, text="", font=get_font("small"),
            text_color=COLOR_DANGER, anchor="w")
        self._label_error_jumlah.pack(side="left", padx=(0, SPACE_MD))

        self._label_error_harga = ctk.CTkLabel(
            ferr, text="", font=get_font("small"),
            text_color=COLOR_DANGER, anchor="w")
        self._label_error_harga.pack(side="left")

        # ── Baris 3: tombol aksi di tengah ───────────────────────────────────
        # Frame tombol di tengah card, margin kiri-kanan 25% dari lebar card
        fbtombol = ctk.CTkFrame(card, fg_color="transparent")
        fbtombol.grid(row=4, column=0, columnspan=5, sticky="ew",
                      padx=(_PX_L, _PX_R), pady=(SPACE_SM, SPACE_MD))
        fbtombol.grid_columnconfigure(0, weight=1)  # spacer kiri
        fbtombol.grid_columnconfigure(1, weight=0)  # tombol batal
        fbtombol.grid_columnconfigure(2, weight=2)  # tombol tambah (lebih lebar)
        fbtombol.grid_columnconfigure(3, weight=1)  # spacer kanan

        # Tombol Batal (hanya muncul saat mode edit — di col 1)
        self._btn_batal_edit = ctk.CTkButton(
            fbtombol, text="Batal", font=get_font("body"),
            fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, height=HEIGHT_BTN_PRIMARY,
            corner_radius=RADIUS_BTN, width=110, command=self._reset_form)
        # Tidak di-grid dulu — muncul saat mode edit

        # Tombol Tambah di col 2, sticky ew → mengisi lebar kolom tengah
        self._btn_simpan = ctk.CTkButton(
            fbtombol, text="Tambah", font=get_font("body_bold"),
            fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            height=HEIGHT_BTN_PRIMARY, corner_radius=RADIUS_BTN,
            command=self._klik_simpan)
        self._btn_simpan.grid(row=0, column=1, columnspan=2, sticky="ew")

    # ── TABEL ─────────────────────────────────────────────────────────────────

    def _buat_tabel(self, parent) -> None:
        """Card tabel item — baris 1 di parent, mengisi sisa ruang vertikal."""
        card = ctk.CTkFrame(parent, fg_color=BG_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=BORDER_COLOR)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)  # row 1 = frame_baris scrollable

        # ── Judul tabel + search + export dalam satu baris ───────────────────
        fht = ctk.CTkFrame(card, fg_color="transparent")
        fht.grid(row=0, column=0, sticky="ew", padx=SPACE_MD, pady=(SPACE_MD, SPACE_SM))
        fht.grid_columnconfigure(1, weight=1)

        # Judul section kiri
        ctk.CTkLabel(fht, text="Daftar Barang Belanjaan",
                     font=get_font("heading_2"), text_color=TEXT_PRIMARY,
                     anchor="w").grid(row=0, column=0, sticky="w",
                                      padx=(SPACE_SM, SPACE_MD))

        # Search bar — mengisi sisa lebar
        self._entry_cari = ctk.CTkEntry(
            fht, placeholder_text="🔍  Cari nama barang...",
            font=get_font("body"), fg_color=BG_INPUT, border_color=BORDER_COLOR,
            border_width=1, text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_PLACEHOLDER,
            height=HEIGHT_INPUT, corner_radius=RADIUS_INPUT)
        self._entry_cari.grid(row=0, column=1, sticky="ew", padx=(0, SPACE_SM))
        self._entry_cari.bind("<KeyRelease>", lambda e: self._render_tabel())

        # Tombol export kanan
        fe = ctk.CTkFrame(fht, fg_color="transparent")
        fe.grid(row=0, column=2)
        ctk.CTkButton(fe, text="Export PDF", font=get_font("small"),
                       fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
                       text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
                       corner_radius=RADIUS_BTN, width=90,
                       command=self._export_pdf
                       ).pack(side="left", padx=(0, SPACE_SM))
        ctk.CTkButton(fe, text="Export Excel", font=get_font("small"),
                       fg_color=BTN_SECONDARY_BG, hover_color=BORDER_COLOR,
                       text_color=TEXT_PRIMARY, height=HEIGHT_BTN_SECONDARY,
                       corner_radius=RADIUS_BTN, width=95,
                       command=self._export_excel
                       ).pack(side="left")

        # Proporsi kolom — didefinisikan sekali, dipakai header + data
        # col: 0=No(40) 1=Nama(w4) 2=Jumlah(w1) 3=Satuan(w1) 4=Harga Satuan(w2) 5=Total(w2) 6=Aksi(70)
        COL_NO   = 40   # lebar fixed kolom nomor urut
        COL_W    = [4, 1, 1, 2, 2]   # weight kolom 1–5 (Nama s.d. Total)
        COL_AKSI = 70
        _PX = 10  # padding internal kiri-kanan setiap cell (via CTkLabel padx)

        def _set_kolom(f):
            # Kolom 0 = No, fixed minsize
            f.grid_columnconfigure(0, minsize=COL_NO, weight=0)
            # Kolom 1–5 = konten, proporsi weight
            for i, w in enumerate(COL_W, start=1):
                f.grid_columnconfigure(i, weight=w)
            # Kolom 6 = Aksi, fixed minsize
            f.grid_columnconfigure(6, minsize=COL_AKSI, weight=0)

        # Satu ScrollableFrame untuk header + data — kolom pasti sinkron
        self._frame_baris = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=ACCENT_PRIMARY)
        self._frame_baris.grid(row=1, column=0, sticky="nsew",
                                padx=SPACE_MD, pady=(0, 0))
        _set_kolom(self._frame_baris)

        # ── Baris 0: header kolom ────────────────────────────────────────────
        # No + 5 kolom konten + Aksi = 7 kolom total
        HDR = [("No","center"),("Nama Barang","center"),("Jumlah","center"),("Satuan","center"),
               ("Harga Satuan","center"),("Total","center"),("Aksi","center")]
        self._widget_header_tabel = []
        for col, (teks, anc) in enumerate(HDR):
            lbl = ctk.CTkLabel(self._frame_baris, text=teks,
                         font=get_font("body_bold"), text_color=ACCENT_PRIMARY,
                         anchor=anc, fg_color="transparent",
                         padx=_PX)
            lbl.grid(row=0, column=col, sticky="ew",
                     pady=(SPACE_SM, SPACE_XS))
            self._widget_header_tabel.append(lbl)

        # Garis bawah header — frame lebar penuh di row 1
        sep = ctk.CTkFrame(self._frame_baris, fg_color=BORDER_COLOR,
                           height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=7, sticky="ew", pady=(0, SPACE_XS))
        self._widget_header_tabel.append(sep)

        # Simpan referensi untuk _render_tabel
        self._set_kolom_tabel = _set_kolom
        self._px_cell = _PX

        # Garis atas footer
        ctk.CTkFrame(card, fg_color=BORDER_COLOR, height=1, corner_radius=0
                     ).grid(row=2, column=0, sticky="ew", padx=SPACE_MD)

        # Footer total
        ff = ctk.CTkFrame(card, fg_color="transparent")
        ff.grid(row=3, column=0, sticky="ew", padx=SPACE_MD, pady=(SPACE_XS, SPACE_MD))
        ff.grid_columnconfigure(0, weight=1)
        self._label_total = ctk.CTkLabel(
            ff, text="Total: Rp0", font=get_font("body_bold"),
            text_color=TEXT_PRIMARY, anchor="e")
        self._label_total.grid(row=0, column=0, sticky="e", padx=SPACE_MD)

    # ── RENDER TABEL ──────────────────────────────────────────────────────────

    def _render_tabel(self) -> None:
        """Hapus hanya baris data lama (row >= 2) lalu gambar ulang dari database.
        Header (row 0) dan separator (row 1) tidak dihapus karena dibuat sekali di _buat_tabel."""
        header_ids = {id(w) for w in self._widget_header_tabel}
        for widget in self._frame_baris.winfo_children():
            if id(widget) not in header_ids:
                widget.destroy()

        kata_kunci = self._entry_cari.get()
        # Ambil daftar item dengan filter kata kunci (id_kategori=0 = semua kategori)
        daftar = self._ctrl.ambil_daftar_item(self._id_periode, kata_kunci, id_kategori=0)

        if not daftar:
            ctk.CTkLabel(
                self._frame_baris,
                text="Belum ada item. Isi form di atas untuk menambahkan.",
                font=get_font("body"), text_color=TEXT_SECONDARY
            ).grid(row=2, column=0, columnspan=7, pady=SPACE_2XL)
            self._label_total.configure(text="Total: Rp0")
            return

        _PX = self._px_cell
        for idx, item in enumerate(daftar):
            baris_row = idx + 2  # row 0 = header, row 1 = separator
            # Warna alternating langsung via fg_color label — tidak pakai sub-frame
            # agar semua kolom berada dalam satu sistem grid yang sama dengan header
            warna = BG_TABLE_ROW_ALT if idx % 2 == 1 else "transparent"

            # Kolom 0: nomor urut
            ctk.CTkLabel(self._frame_baris, text=str(idx + 1), font=get_font("body"),
                         text_color=TEXT_PRIMARY, anchor="center",
                         fg_color=warna, padx=_PX
                         ).grid(row=baris_row, column=0, sticky="ew", pady=SPACE_SM)

            # Kolom 1–5: data item — padding internal via CTkLabel padx agar warna menyambung
            for col, (teks, anc) in enumerate([
                (item["nama_barang"],                  "w"),
                (format_jumlah(item["jumlah_barang"]), "e"),
                (item["nama_satuan"],                  "center"),
                (format_rupiah(item["harga_satuan"]),  "e"),
                (format_rupiah(item["harga_total"]),   "e"),
            ], start=1):
                ctk.CTkLabel(self._frame_baris, text=teks, font=get_font("body"),
                             text_color=TEXT_PRIMARY, anchor=anc,
                             fg_color=warna, padx=_PX
                             ).grid(row=baris_row, column=col, sticky="ew",
                                    pady=SPACE_SM)

            # Tombol Aksi — kolom 6, langsung di frame_baris
            id_detail = item["id_detail"]
            nama_item = item["nama_barang"]
            fa = ctk.CTkFrame(self._frame_baris, fg_color=warna, corner_radius=0)
            fa.grid(row=baris_row, column=6, sticky="nsew")
            fa.grid_rowconfigure(0, weight=1)
            fa.grid_columnconfigure(0, weight=1)
            fa.grid_columnconfigure(1, weight=1)

            ctk.CTkButton(
                fa, text="✏", font=get_font("body"),
                fg_color="transparent", hover_color=BTN_SECONDARY_BG,
                text_color=ACCENT_PRIMARY, width=28, height=28,
                corner_radius=RADIUS_BTN,
                command=lambda i=id_detail: self._klik_edit(i)
            ).grid(row=0, column=0, sticky="e")

            ctk.CTkButton(
                fa, text="✕", font=get_font("body"),
                fg_color="transparent", hover_color=("#FEE2E2", "#3D1515"),
                text_color=COLOR_DANGER, width=28, height=28,
                corner_radius=RADIUS_BTN,
                command=lambda i=id_detail, n=nama_item: self._klik_hapus(i, n)
            ).grid(row=0, column=1, sticky="w")

        total = sum(item["harga_total"] for item in daftar)
        self._label_total.configure(text=f"Total: {format_rupiah(total)}")

    # ── LOGIKA FORM ───────────────────────────────────────────────────────────

    def _muat_state_b(self) -> None:
        """Sinkronkan semua data State B."""
        if self._periode_data is None:
            return

        def _fmt(d): return "-".join(reversed(d.split("-")))
        self._label_periode_b.configure(
            text=f"{_fmt(self._periode_data['tgl_mulai'])}  –  "
                 f"{_fmt(self._periode_data['tgl_selesai'])}")

        self._muat_dropdown_satuan()
        self._muat_dropdown_kategori()
        self._reset_form()
        self._render_tabel()

    def _muat_dropdown_satuan(self) -> None:
        """Isi ComboBox satuan dari tb_satuan secara dinamis."""
        daftar = self._ctrl.ambil_daftar_satuan()
        self._daftar_satuan = daftar
        nama = [r["nama_satuan"] for r in daftar]
        self._combo_satuan.configure(values=nama if nama else ["-- Satuan --"])
        if nama:
            self._combo_satuan.set(nama[0])

    def _muat_dropdown_kategori(self) -> None:
        """Isi ComboBox kategori dari tb_kategori secara dinamis."""
        daftar = self._ctrl.ambil_daftar_kategori()
        self._daftar_kategori = daftar
        nama = [r["nama_kategori"] for r in daftar]
        semua = ["-- Pilih Kategori --"] + nama
        self._combo_kategori.configure(values=semua)
        self._combo_kategori.set("-- Pilih Kategori --")

    def _pada_pilih_nama_barang(self, nama: str, data_barang) -> None:
        """
        Callback dari _AutocompleteEntry.
        Auto-fill + kunci kategori jika barang dikenali.
        Buka kembali kategori jika nama baru diketik.
        """
        if data_barang is not None:
            # Barang dikenali dari saran dropdown
            nama_kat = data_barang.get("nama_kategori") or ""
            if nama_kat:
                self._combo_kategori.set(nama_kat)
                self._combo_kategori.configure(state="disabled")
                self._id_kategori_terkunci = data_barang["id_kategori"]
            self._label_error_kategori.configure(text="")
        else:
            # Teks berubah — cek apakah nama persis ada di master
            self._combo_kategori.configure(state="readonly")
            self._id_kategori_terkunci = 0
            if nama:
                barang = self._ctrl.ambil_barang_persis(nama)
                if barang:
                    self._combo_kategori.set(barang["nama_kategori"] or "-- Pilih Kategori --")
                    self._combo_kategori.configure(state="disabled")
                    self._id_kategori_terkunci = barang["id_kategori"]

    def _pada_ganti_kategori(self, nilai: str = "") -> None:
        """Hapus error saat pengguna memilih kategori."""
        self._label_error_kategori.configure(text="")

    def _pada_ketik_harga(self, event=None) -> None:
        """Saring non-digit dan hitung total otomatis saat mengetik harga."""
        teks = self._entry_harga_satuan.get()
        hanya_angka = "".join(c for c in teks if c.isdigit())
        if hanya_angka != teks:
            self._entry_harga_satuan.delete(0, "end")
            self._entry_harga_satuan.insert(0, hanya_angka)
        self._hitung_total_otomatis()
        self._label_error_harga.configure(text="")

    def _format_harga_satuan(self, event=None) -> None:
        """Format titik ribuan saat fokus keluar dari field harga."""
        teks = self._entry_harga_satuan.get().replace(".", "").strip()
        if teks and teks.isdigit():
            self._entry_harga_satuan.delete(0, "end")
            self._entry_harga_satuan.insert(0, f"{int(teks):,}".replace(",", "."))
        self._hitung_total_otomatis()

    def _bersihkan_format_harga(self, event=None) -> None:
        """Hapus titik ribuan saat fokus masuk agar mudah diedit."""
        teks = self._entry_harga_satuan.get()
        hanya_angka = teks.replace(".", "")
        if hanya_angka != teks:
            self._entry_harga_satuan.delete(0, "end")
            self._entry_harga_satuan.insert(0, hanya_angka)

    def _hitung_total_otomatis(self, event=None) -> None:
        """Kalkulasi harga total dari jumlah × harga satuan."""
        try:
            jumlah = float(self._entry_jumlah.get().replace(",", ".") or 0)
            harga  = float(self._entry_harga_satuan.get().replace(".", "") or 0)
            total  = hitung_harga_total(jumlah, harga)
            self._entry_harga_total.configure(state="normal")
            self._entry_harga_total.delete(0, "end")
            self._entry_harga_total.insert(0, format_rupiah(total).replace("Rp", ""))
            self._entry_harga_total.configure(state="readonly")
        except (ValueError, AttributeError):
            pass

    def _ambil_id_kategori_terpilih(self) -> int:
        """Ambil id_kategori dari dropdown atau nilai terkunci."""
        if self._id_kategori_terkunci > 0:
            return self._id_kategori_terkunci
        nama = self._combo_kategori.get()
        if not hasattr(self, "_daftar_kategori"):
            return 0
        for kat in self._daftar_kategori:
            if kat["nama_kategori"] == nama:
                return kat["id_kategori"]
        return 0

    def _ambil_id_satuan_terpilih(self) -> int:
        """Ambil id_satuan dari dropdown."""
        nama = self._combo_satuan.get()
        if not hasattr(self, "_daftar_satuan"):
            return 0
        for sat in self._daftar_satuan:
            if sat["nama_satuan"] == nama:
                return sat["id_satuan"]
        return 0

    def _klik_simpan(self) -> None:
        """Validasi form lalu simpan ke database."""
        nama        = self._entry_nama.get().strip()
        id_kategori = self._ambil_id_kategori_terpilih()
        id_satuan   = self._ambil_id_satuan_terpilih()
        jumlah_str  = self._entry_jumlah.get().replace(",", ".").strip()
        harga_str   = self._entry_harga_satuan.get().replace(".", "").strip()

        ada_error = False

        # Validasi nama
        if not nama:
            self._entry_nama.entry.configure(border_color=COLOR_DANGER)
            ada_error = True
        else:
            self._entry_nama.entry.configure(border_color=BORDER_COLOR)

        # Validasi kategori
        if id_kategori <= 0:
            self._label_error_kategori.configure(text="Kategori wajib dipilih.")
            ada_error = True
        else:
            self._label_error_kategori.configure(text="")

        # Validasi jumlah
        try:
            jumlah = float(jumlah_str) if jumlah_str else 0.0
            if jumlah <= 0:
                raise ValueError
            self._label_error_jumlah.configure(text="")
            self._entry_jumlah.configure(border_color=BORDER_COLOR)
        except ValueError:
            self._label_error_jumlah.configure(text="Jumlah harus lebih dari 0.")
            self._entry_jumlah.configure(border_color=COLOR_DANGER)
            ada_error = True
            jumlah = 0.0

        # Validasi harga
        try:
            harga = float(harga_str) if harga_str else 0.0
            if harga < 0:
                raise ValueError
            self._label_error_harga.configure(text="")
            self._entry_harga_satuan.configure(border_color=BORDER_COLOR)
        except ValueError:
            self._label_error_harga.configure(text="Harga tidak boleh negatif.")
            self._entry_harga_satuan.configure(border_color=COLOR_DANGER)
            ada_error = True
            harga = 0.0

        if ada_error:
            return

        if self._mode_edit:
            hasil = self._ctrl.ubah_item(
                self._id_edit, nama, id_kategori, id_satuan, jumlah, harga)
        else:
            hasil = self._ctrl.tambah_item(
                self._id_periode, nama, id_kategori, id_satuan, jumlah, harga)

        if hasil["berhasil"]:
            self._render_tabel()
            self._reset_form()
            tampilkan_toast_sukses(self, hasil["pesan"])
            # Refresh dashboard agar sisa budget ter-update
            if self._callback_refresh_dashboard:
                self.after(500, self._callback_refresh_dashboard)
        else:
            tampilkan_toast_error(self, hasil["pesan"])

    def _klik_edit(self, id_detail: int) -> None:
        """Isi form dengan data item yang akan diedit."""
        item = self._ctrl.ambil_item_by_id(id_detail)
        if item is None:
            return

        self._mode_edit = True
        self._id_edit   = id_detail

        self._entry_nama.set(item["nama_barang"])
        self._entry_jumlah.delete(0, "end")
        self._entry_jumlah.insert(0, format_jumlah(item["jumlah_barang"]))
        self._entry_harga_satuan.delete(0, "end")
        self._entry_harga_satuan.insert(
            0, f"{int(item['harga_satuan']):,}".replace(",", "."))
        self._hitung_total_otomatis()

        # Kunci dropdown kategori dengan nilai dari data
        self._combo_kategori.configure(state="normal")
        self._combo_kategori.set(item["nama_kategori"] or "-- Pilih Kategori --")
        self._combo_kategori.configure(state="disabled")
        self._id_kategori_terkunci = item["id_kategori"]

        self._combo_satuan.set(item["nama_satuan"])

        # Ubah tampilan form ke mode edit
        self._label_judul_form.configure(text="Edit Barang")
        self._btn_simpan.configure(text="Simpan Perubahan")
        self._btn_batal_edit.grid(row=0, column=1, sticky="ew", padx=(0, SPACE_SM))
        self._btn_simpan.grid(row=0, column=2, sticky="ew")

    # ── CALLBACK UNTUK REFRESH ────────────────────────────────────────────────

    def set_dashboard_refresh_callback(self, callback) -> None:
        """Set callback yang dipanggil setelah item berhasil ditambah/diubah/dihapus."""
        self._callback_refresh_dashboard = callback

    # ── HAPUS ─────────────────────────────────────────────────────────────────

    def _klik_hapus(self, id_detail: int, nama_item: str) -> None:
        """Tampilkan dialog konfirmasi sebelum hapus."""
        tampilkan_konfirmasi_hapus(
            self, nama_item=nama_item,
            callback=lambda: self._eksekusi_hapus(id_detail))

    def _eksekusi_hapus(self, id_detail: int) -> None:
        """Hapus item dan render ulang tabel."""
        self._ctrl.hapus_item(id_detail)
        self._render_tabel()
        tampilkan_toast_sukses(self, "Item berhasil dihapus.")
        # Refresh dashboard agar sisa budget ter-update
        if self._callback_refresh_dashboard:
            self.after(500, self._callback_refresh_dashboard)

    def _reset_form(self) -> None:
        """Kembalikan form ke state kosong / mode tambah."""
        self._mode_edit            = False
        self._id_edit              = 0
        self._id_kategori_terkunci = 0

        self._entry_nama.reset()
        self._entry_jumlah.delete(0, "end")
        self._entry_harga_satuan.delete(0, "end")
        self._entry_harga_total.configure(state="normal")
        self._entry_harga_total.delete(0, "end")
        self._entry_harga_total.configure(state="readonly")

        self._entry_nama.entry.configure(border_color=BORDER_COLOR)
        self._entry_jumlah.configure(border_color=BORDER_COLOR)
        self._entry_harga_satuan.configure(border_color=BORDER_COLOR)

        self._label_error_kategori.configure(text="")
        self._label_error_jumlah.configure(text="")
        self._label_error_harga.configure(text="")

        self._combo_kategori.configure(state="readonly")
        self._combo_kategori.set("-- Pilih Kategori --")

        self._label_judul_form.configure(text="Tambah Barang")
        self._btn_simpan.configure(text="Tambah")
        self._btn_batal_edit.grid_remove()
        self._btn_simpan.grid(row=0, column=1, columnspan=2, sticky="ew")

        self._entry_nama.fokus()

    # ── EXPORT (stub — diimplementasi Tahap 10) ───────────────────────────────

    def _export_pdf(self) -> None:
        tampilkan_toast_error(self, "Export PDF tersedia di Tahap 10.")

    def _export_excel(self) -> None:
        tampilkan_toast_error(self, "Export Excel tersedia di Tahap 10.")