"""
format_helper.py — Fungsi-fungsi bantu format angka dan mata uang Rupiah
Digunakan oleh: semua view, export_helper.py, currency_entry.py

Aturan format (Design System §5.2 & PRD §7 poin 1):
- Format: Rp30.000 (titik sebagai pemisah ribuan, tanpa spasi)
- Nilai 0: Rp0 (bukan Rp0,00 atau Rp-)
- Nilai negatif: -Rp30.000
- TIDAK ADA PENGECUALIAN di seluruh aplikasi
"""


def format_rupiah(nilai: float) -> str:
    """
    Format angka ke string Rupiah tanpa spasi dan tanpa desimal.
    Contoh: 30000 → 'Rp30.000', 0 → 'Rp0', -30000 → '-Rp30.000'
    """
    # Tangani nilai negatif secara terpisah agar tanda minus di depan 'Rp'
    if nilai < 0:
        return f"-Rp{int(abs(nilai)):,}".replace(",", ".")

    # Nilai 0 atau positif: format langsung tanpa desimal
    return f"Rp{int(nilai):,}".replace(",", ".")


def parse_rupiah(teks: str) -> float:
    """
    Bersihkan string format Rupiah ke nilai float untuk kalkulasi dan simpan ke DB.
    Contoh: 'Rp30.000' → 30000.0, '-Rp1.500.000' → -1500000.0
    """
    # Hapus semua karakter non-numerik kecuali tanda minus
    teks_bersih = teks.replace("Rp", "").replace(".", "").strip()

    # Kembalikan 0 jika string kosong setelah dibersihkan
    if not teks_bersih or teks_bersih == "-":
        return 0.0

    return float(teks_bersih)


def format_rupiah_ringkas(nilai: float) -> str:
    """
    Format angka ke Rupiah ringkas untuk label sumbu Y grafik matplotlib.
    Contoh: 25000 → 'Rp25rb', 1500000 → 'Rp1.5jt', 0 → 'Rp0'
    """
    if nilai == 0:
        return "Rp0"

    # Nilai jutaan: tampilkan dengan satuan 'jt'
    if abs(nilai) >= 1_000_000:
        angka_juta = nilai / 1_000_000
        # Tampilkan satu desimal hanya jika nilainya tidak bulat
        if angka_juta == int(angka_juta):
            return f"Rp{int(angka_juta)}jt"
        return f"Rp{angka_juta:.1f}jt"

    # Nilai ribuan: tampilkan dengan satuan 'rb'
    if abs(nilai) >= 1_000:
        angka_ribu = nilai / 1_000
        if angka_ribu == int(angka_ribu):
            return f"Rp{int(angka_ribu)}rb"
        return f"Rp{angka_ribu:.1f}rb"

    # Nilai di bawah 1000: tampilkan langsung
    return f"Rp{int(nilai)}"


def format_jumlah(nilai: float) -> str:
    """
    Format angka jumlah barang — tampilkan desimal hanya jika ada.
    Contoh: 5.0 → '5', 2.5 → '2.5', 0.75 → '0.75'
    Digunakan untuk kolom Jumlah di tabel dan ekspor Excel.
    """
    # Jika nilai bulat, tampilkan tanpa desimal
    if nilai == int(nilai):
        return str(int(nilai))

    # Jika ada desimal, tampilkan apa adanya (bersihkan trailing zero)
    return str(nilai).rstrip("0").rstrip(".")


def hitung_harga_total(jumlah: float, harga_satuan: float) -> float:
    """
    Hitung harga total dari jumlah barang dan harga satuan.
    Nilai ini tidak disimpan ke DB — selalu dihitung dinamis (PRD §4.5 Catatan).
    """
    return jumlah * harga_satuan


def validasi_angka_positif(teks: str) -> bool:
    """
    Cek apakah string dapat dikonversi ke angka dan nilainya lebih dari 0.
    Digunakan untuk validasi form sebelum simpan ke database.
    """
    try:
        nilai = float(teks.replace("Rp", "").replace(".", "").strip())
        return nilai > 0
    except (ValueError, AttributeError):
        return False


def validasi_angka_non_negatif(teks: str) -> bool:
    """
    Cek apakah string dapat dikonversi ke angka dan nilainya >= 0.
    Digunakan untuk validasi harga satuan (boleh 0, tidak boleh negatif).
    """
    try:
        nilai = float(teks.replace("Rp", "").replace(".", "").strip())
        return nilai >= 0
    except (ValueError, AttributeError):
        return False