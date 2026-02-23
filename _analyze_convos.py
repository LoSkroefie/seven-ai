import sqlite3, os
conn = sqlite3.connect(os.path.join(r"C:\Users\USER-PC\.chatbot", "memory.db"))
c = conn.cursor()
c.execute("SELECT id, timestamp, user_input, bot_response, emotion FROM session_memory WHERE timestamp LIKE '2026-02-22%' ORDER BY id")
rows = c.fetchall()
print(f"Today's conversations: {len(rows)}")
for r in rows:
    uid, ts, user, bot, emo = r
    user = (user or "")[:120]
    bot = (bot or "")[:200]
    print(f"\n[{ts}] emotion={emo}")
    print(f"  USER: {user}")
    print(f"  SEVEN: {bot}")
conn.close()
