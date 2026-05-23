# fix_db.py — jalankan sekali dari root folder proyek
import sqlite3
conn = sqlite3.connect("catatan_belanja.db")
conn.execute(
    "UPDATE tb_periode_budget SET tgl_selesai='2026-05-29', is_active=1 WHERE id_periode=1"
)
conn.commit()
conn.close()
print("Fixed.")