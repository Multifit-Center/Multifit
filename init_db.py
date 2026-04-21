import sqlite3

conn = sqlite3.connect("gym.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS socios (
    dni TEXT PRIMARY KEY,
    nombre TEXT,
    vencimiento TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS ingresos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT,
    fecha TEXT,
    estado TEXT
)
""")

cur.execute("INSERT OR IGNORE INTO socios VALUES ('12345678','Juan Perez','2026-04-30')")

conn.commit()
conn.close()

print("Listo")