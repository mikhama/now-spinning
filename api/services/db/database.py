import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "now-spinning.db")


def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS stylus (
                id TEXT PRIMARY KEY,
                name TEXT,
                distance_hours REAL,
                capacity_min_hours REAL,
                capacity_max_hours REAL,
                active INTEGER
            );
            CREATE TABLE IF NOT EXISTS record (
                id TEXT PRIMARY KEY,
                release_id TEXT,
                master_id TEXT,
                title TEXT,
                artist TEXT,
                sides TEXT,
                linked INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS status (
                updated_at TEXT
            );
        """)
        conn.commit()
    finally:
        conn.close()


def get_last_sync_date():
    conn = _get_connection()
    try:
        row = conn.execute("SELECT updated_at FROM status LIMIT 1").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def upsert_styli(styli_list):
    conn = _get_connection()
    try:
        for s in styli_list:
            cap_min = s.get("capacity_min_hours") or s.get("capacity_min_hours:") or s.get("capacity_min", 0)
            cap_max = s.get("capacity_max_hours") or s.get("capacity_max_hours:") or s.get("capacity_max", 0)
            active = s.get("active", 1)
            conn.execute(
                "INSERT OR IGNORE INTO stylus (id, name, distance_hours, capacity_min_hours, capacity_max_hours, active) VALUES (?, ?, ?, ?, ?, ?)",
                (s["id"], s["name"], s.get("distance_hours", 0), cap_min, cap_max, active),
            )
        conn.commit()
    finally:
        conn.close()


def upsert_records(records_list):
    import json as _json
    conn = _get_connection()
    try:
        for r in records_list:
            sides_json = r["sides"] if isinstance(r["sides"], str) else _json.dumps(r["sides"])
            conn.execute(
                """INSERT INTO record (id, release_id, master_id, title, artist, sides) VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET release_id=excluded.release_id, master_id=excluded.master_id, title=excluded.title, artist=excluded.artist, sides=excluded.sides""",
                (r["id"], r["release_id"], r["master_id"], r["title"], r["artist"], sides_json),
            )
        conn.commit()
    finally:
        conn.close()


def update_sync_date():
    from datetime import date
    conn = _get_connection()
    try:
        today = date.today().isoformat()
        row = conn.execute("SELECT updated_at FROM status LIMIT 1").fetchone()
        if row:
            conn.execute("UPDATE status SET updated_at = ?", (today,))
        else:
            conn.execute("INSERT INTO status (updated_at) VALUES (?)", (today,))
        conn.commit()
    finally:
        conn.close()


def get_all_records():
    conn = _get_connection()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, release_id, master_id, title, artist, sides, linked FROM record").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def mark_record_linked(record_id):
    conn = _get_connection()
    try:
        cursor = conn.execute("UPDATE record SET linked = 1 WHERE id = ?", (str(record_id),))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
