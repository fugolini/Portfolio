import sqlite3
from pathlib import Path

HTML_DIR = Path("/path/to/your/html/dir")        # directory with HTML files
DB_PATH = Path("/path/to/your/db/mockdb.sqlite")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    headword TEXT NOT NULL,
    filename TEXT NOT NULL
)
""")

cur.execute("CREATE INDEX IF NOT EXISTS idx_headword ON entries(headword)")

for path in HTML_DIR.iterdir():
    if path.suffix != ".html":
        continue

    name = path.name  # e.g. 00269_ab_intestato.html

    id_part, rest = name.split("_", 1)
    entry_part = rest[:-5]  # remove ".html"

    entry_id = int(id_part)
    headword = entry_part.replace("_", " ")

    cur.execute(
        "INSERT INTO entries (id, headword, filename) VALUES (?, ?, ?)",
        (entry_id, headword, name)
    )

conn.commit()
conn.close()

