import sqlite3, os
DATA = r"C:\Users\USER-PC\.chatbot"

conn = sqlite3.connect(os.path.join(DATA, "memory.db"))
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print("Tables:", tables)
for t in tables:
    c.execute(f'SELECT COUNT(*) FROM "{t}"')
    count = c.fetchone()[0]
    print(f"  {t}: {count} rows")
    if count > 0:
        c.execute(f'SELECT * FROM "{t}" ORDER BY rowid DESC LIMIT 5')
        cols = [d[0] for d in c.description]
        print(f"    Columns: {cols}")
        for row in c.fetchall():
            d = dict(zip(cols, row))
            for k in d:
                if isinstance(d[k], str) and len(d[k]) > 150:
                    d[k] = d[k][:150] + "..."
            print(f"    {d}")
conn.close()

# Emotional memory
print("\n=== EMOTIONAL MEMORY ===")
import json
with open(os.path.join(DATA, "emotional_memory.json"), "r", encoding="utf-8", errors="replace") as f:
    em = json.load(f)
for k, v in em.items():
    if isinstance(v, list):
        print(f"{k}: {len(v)} entries")
        for item in v[-8:]:
            print(f"  {str(item)[:200]}")
    else:
        print(f"{k}: {str(v)[:200]}")
