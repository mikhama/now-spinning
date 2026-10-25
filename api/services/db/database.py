import math
import os
import sqlite3
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "now-spinning.db")


def _get_connection(*, existing_only=False):
    if existing_only:
        conn = sqlite3.connect(Path(DB_PATH).resolve().as_uri() + "?mode=rw", uri=True)
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
    except sqlite3.Error:
        conn.close()
        raise
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
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            _normalize_active_stylus(conn)
    finally:
        conn.close()


def _selected_stylus_id(conn):
    row = conn.execute(
        "SELECT id FROM stylus ORDER BY CASE WHEN active = 1 THEN 0 ELSE 1 END, id LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def _normalize_active_stylus(conn):
    selected_id = _selected_stylus_id(conn)
    if selected_id is not None:
        conn.execute(
            "UPDATE stylus SET active = (id = ?) WHERE active IS NOT (id = ?)",
            (selected_id, selected_id),
        )


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
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            _normalize_active_stylus(conn)
            for s in styli_list:
                cap_min = s.get("capacity_min_hours") or s.get("capacity_min_hours:") or s.get("capacity_min", 0)
                cap_max = s.get("capacity_max_hours") or s.get("capacity_max_hours:") or s.get("capacity_max", 0)
                conn.execute(
                    "INSERT OR IGNORE INTO stylus (id, name, distance_hours, capacity_min_hours, capacity_max_hours, active) VALUES (?, ?, ?, ?, ?, ?)",
                    (s["id"], s["name"], 0, cap_min, cap_max, 0),
                )
            _normalize_active_stylus(conn)
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


def get_all_styli(*, existing_only=False):
    conn = _get_connection(existing_only=existing_only)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                id,
                name,
                distance_hours AS hours,
                capacity_min_hours AS capacity_min,
                capacity_max_hours AS capacity_max,
                active
            FROM stylus
            ORDER BY id
            """
        ).fetchall()
        return [dict(row, active=bool(row["active"])) for row in rows]
    finally:
        conn.close()


def get_active_stylus_hours():
    conn = _get_connection()
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, distance_hours AS hours
            FROM stylus
            WHERE active = 1
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def increment_stylus_hours(stylus_id, delta_hours):
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "UPDATE stylus SET distance_hours = distance_hours + ? WHERE id = ?",
            (delta_hours, str(stylus_id)),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def activate_stylus(stylus_id):
    """Commit one selection and return its saved hours, or None for a missing ID."""
    conn = _get_connection(existing_only=True)
    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT id, distance_hours FROM stylus WHERE id = ?", (str(stylus_id),)
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE stylus SET active = (id = ?) WHERE active IS NOT (id = ?)",
                (str(stylus_id), str(stylus_id)),
            )
        return {"id": row[0], "hours": row[1]}
    finally:
        conn.close()


def delete_stylus(stylus_id):
    """Delete an inactive local row, checking selection within the write transaction."""
    conn = _get_connection(existing_only=True)
    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT id FROM stylus WHERE id = ?", (str(stylus_id),)
            ).fetchone()
            if row is None:
                return False
            if row[0] == _selected_stylus_id(conn):
                raise ValueError(f"Stylus {stylus_id} is active; select another stylus in the stopped player first")
            conn.execute("DELETE FROM stylus WHERE id = ?", (str(stylus_id),))
            _normalize_active_stylus(conn)
        return True
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


def is_record_linked(record_id):
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM record WHERE id = ? AND linked = 1",
            (str(record_id),),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def set_stylus_hours(stylus_id, hours):
    """Replace a saved total; return (previous, new), or None for a missing ID."""
    try:
        hours = float(hours)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Hours must be finite and zero or more") from error
    if not math.isfinite(hours) or hours < 0:
        raise ValueError("Hours must be finite and zero or more")

    conn = _get_connection(existing_only=True)
    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT distance_hours FROM stylus WHERE id = ?", (str(stylus_id),)
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE stylus SET distance_hours = ? WHERE id = ?",
                (hours, str(stylus_id)),
            )
        return row[0], hours
    finally:
        conn.close()


def reset_stylus_hours(stylus_id):
    return set_stylus_hours(stylus_id, 0) is not None
