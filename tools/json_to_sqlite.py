#!/usr/bin/env python3
"""
Optional one-shot migration: users.json -> db.sqlite
Schema: users(id TEXT PRIMARY KEY, data JSON)
Keeps your current bot logic (still reads JSON). Use this only if/when
you decide to move to SQLite; it won't change bot imports automatically.
"""
import os, json, sqlite3, sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
JSON_PATH = os.path.join(DATA_DIR, "users.json")
SQLITE_PATH = os.path.join(DATA_DIR, "db.sqlite")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    users = {}
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                users = json.loads(content)
    except FileNotFoundError:
        print("users.json not found, nothing to migrate")
        return
    except json.JSONDecodeError:
        print("users.json is corrupt/empty, nothing to migrate")
        return

    conn = sqlite3.connect(SQLITE_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        cur = conn.cursor()
        for uid, obj in users.items():
            cur.execute("INSERT OR REPLACE INTO users(id, data) VALUES (?, ?)", (str(uid), json.dumps(obj, ensure_ascii=False)))
        conn.commit()
        print(f"Migrated {len(users)} users to {SQLITE_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
