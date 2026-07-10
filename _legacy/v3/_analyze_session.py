"""Analyze Seven's last session from data files"""
import sqlite3, json, os
from datetime import datetime

DATA = r"C:\Users\USER-PC\.chatbot"

# 1. Memory DB
print("=" * 60)
print("MEMORY DATABASE")
print("=" * 60)
conn = sqlite3.connect(os.path.join(DATA, "memory.db"))
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print(f"Tables: {tables}")
for t in tables:
    c.execute(f'SELECT COUNT(*) FROM "{t}"')
    count = c.fetchone()[0]
    print(f"  {t}: {count} rows")
    if count > 0 and count < 500:
        c.execute(f'SELECT * FROM "{t}" ORDER BY rowid DESC LIMIT 10')
        cols = [d[0] for d in c.description]
        print(f"    Columns: {cols}")
        for row in c.fetchall():
            # Print compact
            d = dict(zip(cols, row))
            # Truncate long values
            for k in d:
                if isinstance(d[k], str) and len(d[k]) > 120:
                    d[k] = d[k][:120] + "..."
            print(f"    {d}")
conn.close()

# 2. Emotional Memory
print("\n" + "=" * 60)
print("EMOTIONAL MEMORY")
print("=" * 60)
with open(os.path.join(DATA, "emotional_memory.json"), "r", encoding="utf-8", errors="replace") as f:
    em = json.load(f)
if isinstance(em, dict):
    for k, v in em.items():
        if isinstance(v, list):
            print(f"{k}: {len(v)} entries")
            for item in v[-5:]:
                if isinstance(item, dict):
                    ts = item.get("timestamp", "?")
                    txt = str(item)[:200]
                    print(f"  [{ts}] {txt}")
        elif isinstance(v, dict):
            print(f"{k}: {json.dumps(v, default=str)[:200]}")
        else:
            print(f"{k}: {v}")

# 3. Knowledge Graph
print("\n" + "=" * 60)
print("KNOWLEDGE GRAPH")
print("=" * 60)
with open(os.path.join(DATA, "knowledge_graph.json"), "r", encoding="utf-8", errors="replace") as f:
    kg = json.load(f)
if isinstance(kg, dict):
    for k, v in kg.items():
        if isinstance(v, list):
            print(f"{k}: {len(v)} entries")
            for item in v[-10:]:
                print(f"  {json.dumps(item, default=str)[:200]}")
        else:
            print(f"{k}: {str(v)[:200]}")

# 4. Learned Knowledge
print("\n" + "=" * 60)
print("LEARNED KNOWLEDGE")
print("=" * 60)
with open(os.path.join(DATA, "learned_knowledge.json"), "r", encoding="utf-8", errors="replace") as f:
    lk = json.load(f)
if isinstance(lk, dict):
    for k, v in lk.items():
        if isinstance(v, list):
            print(f"{k}: {len(v)} entries")
            for item in v[:10]:
                print(f"  {json.dumps(item, default=str)[:200]}")
        else:
            print(f"{k}: {str(v)[:200]}")

# 5. User Profile
print("\n" + "=" * 60)
print("USER PROFILE")
print("=" * 60)
with open(os.path.join(DATA, "user_profile.json"), "r", encoding="utf-8", errors="replace") as f:
    up = json.load(f)
print(json.dumps(up, indent=2, default=str)[:2000])

# 6. Corrections
print("\n" + "=" * 60)
print("CORRECTIONS LEARNED")
print("=" * 60)
with open(os.path.join(DATA, "corrections.json"), "r", encoding="utf-8", errors="replace") as f:
    corr = json.load(f)
print(json.dumps(corr, indent=2, default=str)[:2000])

# 7. Identity files
print("\n" + "=" * 60)
print("IDENTITY FILES")
print("=" * 60)
identity_dir = os.path.join(DATA, "identity")
if os.path.isdir(identity_dir):
    for fname in os.listdir(identity_dir):
        fpath = os.path.join(identity_dir, fname)
        if os.path.isfile(fpath):
            sz = os.path.getsize(fpath)
            mod = datetime.fromtimestamp(os.path.getmtime(fpath))
            print(f"  {fname} ({sz} bytes, modified {mod})")
            if sz < 5000 and fname.endswith(('.md', '.txt', '.json')):
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                print(content[:1000])
                print("---")

# 8. Learned preferences
print("\n" + "=" * 60)
print("LEARNED PREFERENCES")
print("=" * 60)
with open(os.path.join(DATA, "learned_preferences.json"), "r", encoding="utf-8", errors="replace") as f:
    lp = json.load(f)
print(json.dumps(lp, indent=2, default=str)[:2000])

# 9. LLM calls DB
print("\n" + "=" * 60)
print("LLM CALLS DATABASE")
print("=" * 60)
try:
    conn2 = sqlite3.connect(os.path.join(DATA, "llm_calls.db"))
    c2 = conn2.cursor()
    c2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for t in c2.fetchall():
        c2.execute(f'SELECT COUNT(*) FROM "{t[0]}"')
        cnt = c2.fetchone()[0]
        print(f"  {t[0]}: {cnt} rows")
        if cnt > 0:
            c2.execute(f'SELECT * FROM "{t[0]}" ORDER BY rowid DESC LIMIT 5')
            cols = [d[0] for d in c2.description]
            print(f"    Columns: {cols}")
            for row in c2.fetchall():
                d = dict(zip(cols, row))
                for k in d:
                    if isinstance(d[k], str) and len(d[k]) > 100:
                        d[k] = d[k][:100] + "..."
                print(f"    {d}")
    conn2.close()
except Exception as e:
    print(f"Error: {e}")
