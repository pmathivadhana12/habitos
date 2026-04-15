"""
database.py — HabitOS SQLite backend
Handles users, households, habits, and daily logs.
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, date

DB_PATH = "habitos.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        email       TEXT    UNIQUE NOT NULL,
        password    TEXT    NOT NULL,
        created_at  TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS households (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        invite_code TEXT    UNIQUE NOT NULL,
        owner_id    INTEGER NOT NULL REFERENCES users(id),
        created_at  TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS household_members (
        household_id INTEGER NOT NULL REFERENCES households(id),
        user_id      INTEGER NOT NULL REFERENCES users(id),
        joined_at    TEXT    DEFAULT (datetime('now')),
        PRIMARY KEY (household_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS habits (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL REFERENCES users(id),
        name         TEXT    NOT NULL,
        icon         TEXT    DEFAULT '✅',
        unit         TEXT    DEFAULT 'times',
        target       REAL    DEFAULT 1.0,
        habit_type   TEXT    DEFAULT 'binary',
        is_active    INTEGER DEFAULT 1,
        created_at   TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS logs (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id),
        habit_id   INTEGER NOT NULL REFERENCES habits(id),
        log_date   TEXT    NOT NULL,
        status     INTEGER DEFAULT 0,
        value      REAL    DEFAULT 0.0,
        notes      TEXT    DEFAULT '',
        logged_at  TEXT    DEFAULT (datetime('now')),
        UNIQUE(user_id, habit_id, log_date)
    );
    """)

    conn.commit()
    conn.close()


# ── Auth helpers ──────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = "habitos_salt_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def register_user(name: str, email: str, password: str) -> dict:
    """Returns {'ok': True, 'user': {...}} or {'ok': False, 'error': '...'}"""
    conn = get_conn()
    try:
        hashed = hash_password(password)
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?,?,?)",
            (name.strip(), email.strip().lower(), hashed)
        )
        conn.commit()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?", (email.strip().lower(),)
        ).fetchone()
        return {"ok": True, "user": dict(user)}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "Email already registered."}
    finally:
        conn.close()


def login_user(email: str, password: str) -> dict:
    """Returns {'ok': True, 'user': {...}} or {'ok': False, 'error': '...'}"""
    conn = get_conn()
    hashed = hash_password(password)
    user = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email.strip().lower(), hashed)
    ).fetchone()
    conn.close()
    if user:
        return {"ok": True, "user": dict(user)}
    return {"ok": False, "error": "Invalid email or password."}


# ── Household helpers ─────────────────────────────────────────────────────────

def create_household(name: str, owner_id: int) -> dict:
    code = secrets.token_hex(4).upper()  # e.g. "A3F9B2C1"
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO households (name, invite_code, owner_id) VALUES (?,?,?)",
            (name.strip(), code, owner_id)
        )
        conn.commit()
        hh = conn.execute(
            "SELECT * FROM households WHERE owner_id=? ORDER BY id DESC LIMIT 1",
            (owner_id,)
        ).fetchone()
        # Auto-add owner as member
        conn.execute(
            "INSERT OR IGNORE INTO household_members (household_id, user_id) VALUES (?,?)",
            (hh["id"], owner_id)
        )
        conn.commit()
        return {"ok": True, "household": dict(hh)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def join_household(invite_code: str, user_id: int) -> dict:
    conn = get_conn()
    hh = conn.execute(
        "SELECT * FROM households WHERE invite_code=?",
        (invite_code.strip().upper(),)
    ).fetchone()
    if not hh:
        conn.close()
        return {"ok": False, "error": "Invalid invite code."}
    try:
        conn.execute(
            "INSERT OR IGNORE INTO household_members (household_id, user_id) VALUES (?,?)",
            (hh["id"], user_id)
        )
        conn.commit()
        conn.close()
        return {"ok": True, "household": dict(hh)}
    except Exception as e:
        conn.close()
        return {"ok": False, "error": str(e)}


def get_user_household(user_id: int):
    """Returns the household dict the user belongs to, or None."""
    conn = get_conn()
    hh = conn.execute("""
        SELECT h.* FROM households h
        JOIN household_members hm ON h.id = hm.household_id
        WHERE hm.user_id = ?
        ORDER BY hm.joined_at ASC LIMIT 1
    """, (user_id,)).fetchone()
    conn.close()
    return dict(hh) if hh else None


def get_household_members(household_id: int) -> list:
    conn = get_conn()
    members = conn.execute("""
        SELECT u.id, u.name, u.email FROM users u
        JOIN household_members hm ON u.id = hm.user_id
        WHERE hm.household_id = ?
    """, (household_id,)).fetchall()
    conn.close()
    return [dict(m) for m in members]


# ── Habit helpers ─────────────────────────────────────────────────────────────

DEFAULT_HABITS = [
    ("🏋️", "Gym",     "mins",  30.0, "duration"),
    ("💧", "Water",   "liters", 2.5, "quantity"),
    ("🌙", "Sleep",   "hours",  7.0, "duration"),
    ("💊", "Vitamins","times",  1.0, "binary"),
]

def seed_default_habits(user_id: int):
    """Give new users the 4 default habits."""
    conn = get_conn()
    for icon, name, unit, target, htype in DEFAULT_HABITS:
        conn.execute("""
            INSERT OR IGNORE INTO habits (user_id, name, icon, unit, target, habit_type)
            VALUES (?,?,?,?,?,?)
        """, (user_id, name, icon, unit, target, htype))
    conn.commit()
    conn.close()


def get_habits(user_id: int) -> list:
    conn = get_conn()
    habits = conn.execute(
        "SELECT * FROM habits WHERE user_id=? AND is_active=1 ORDER BY id",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(h) for h in habits]


def add_habit(user_id: int, name: str, icon: str, unit: str,
              target: float, habit_type: str) -> dict:
    conn = get_conn()
    conn.execute("""
        INSERT INTO habits (user_id, name, icon, unit, target, habit_type)
        VALUES (?,?,?,?,?,?)
    """, (user_id, name.strip(), icon, unit.strip(), target, habit_type))
    conn.commit()
    conn.close()
    return {"ok": True}


def delete_habit(habit_id: int, user_id: int):
    conn = get_conn()
    conn.execute(
        "UPDATE habits SET is_active=0 WHERE id=? AND user_id=?",
        (habit_id, user_id)
    )
    conn.commit()
    conn.close()


# ── Log helpers ───────────────────────────────────────────────────────────────

def log_habit(user_id: int, habit_id: int, log_date: str,
              status: int, value: float, notes: str = "") -> dict:
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO logs (user_id, habit_id, log_date, status, value, notes)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(user_id, habit_id, log_date)
            DO UPDATE SET status=excluded.status, value=excluded.value, notes=excluded.notes
        """, (user_id, habit_id, log_date, status, value, notes))
        conn.commit()
        conn.close()
        return {"ok": True}
    except Exception as e:
        conn.close()
        return {"ok": False, "error": str(e)}


def get_logs(user_id: int, days: int = 30) -> list:
    """Return last N days of logs for a user, joined with habit info."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT l.*, h.name as habit_name, h.icon, h.unit, h.target, h.habit_type
        FROM logs l
        JOIN habits h ON l.habit_id = h.id
        WHERE l.user_id = ?
          AND l.log_date >= date('now', ? || ' days')
        ORDER BY l.log_date DESC
    """, (user_id, f"-{days}")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_household_logs(household_id: int, days: int = 30) -> list:
    """All logs for all members of a household."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT l.*, h.name as habit_name, h.icon, h.unit, h.target, h.habit_type,
               u.name as user_name, u.id as uid
        FROM logs l
        JOIN habits h ON l.habit_id = h.id
        JOIN users u ON l.user_id = u.id
        JOIN household_members hm ON hm.user_id = u.id
        WHERE hm.household_id = ?
          AND l.log_date >= date('now', ? || ' days')
        ORDER BY l.log_date DESC
    """, (household_id, f"-{days}")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_streak(user_id: int, habit_id: int) -> int:
    """Current consecutive-day streak for a habit."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT log_date, status FROM logs
        WHERE user_id=? AND habit_id=?
        ORDER BY log_date DESC
    """, (user_id, habit_id)).fetchall()
    conn.close()
    count = 0
    for r in rows:
        if r["status"] == 1:
            count += 1
        else:
            break
    return count

# ── Demo seed from house_1.csv ────────────────────────────────────────────────

DEMO_HABIT_ICONS = {"gym": "🏋️", "water": "💧", "sleep": "🌙", "vitamins": "💊"}
DEMO_HABIT_UNITS = {"gym": "mins", "water": "liters", "sleep": "hours", "vitamins": "times"}
DEMO_HABIT_TARGETS = {"gym": 30.0, "water": 2.5, "sleep": 7.0, "vitamins": 1.0}
DEMO_HABIT_TYPES = {"gym": "duration", "water": "quantity", "sleep": "duration", "vitamins": "binary"}


def seed_demo_data(csv_path: str = "house_1.csv"):
    """
    Load house_1.csv into the DB as a demo household (Ram, Mathi, Guna).
    Safe to call multiple times — skips if demo already loaded.
    """
    import pandas as pd
    import os

    if not os.path.exists(csv_path):
        return  # No CSV, skip silently

    conn = get_conn()

    # Check if demo already seeded
    existing = conn.execute(
        "SELECT id FROM users WHERE email='ram@demo.habitos'"
    ).fetchone()
    if existing:
        conn.close()
        return  # Already done

    try:
        df = pd.read_csv(csv_path, parse_dates=["date"])

        demo_password = hash_password("demo1234")
        demo_members = {
            "Ram":   "ram@demo.habitos",
            "Mathi": "mathi@demo.habitos",
            "Guna":  "guna@demo.habitos",
        }

        # Create demo users
        user_ids = {}
        for name, email in demo_members.items():
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password) VALUES (?,?,?)",
                (name, email, demo_password)
            )
            uid = conn.execute(
                "SELECT id FROM users WHERE email=?", (email,)
            ).fetchone()["id"]
            user_ids[name] = uid

        # Create demo household (owner = Ram)
        conn.execute(
            "INSERT OR IGNORE INTO households (name, invite_code, owner_id) VALUES (?,?,?)",
            ("Demo House 🏠", "DEMO0001", user_ids["Ram"])
        )
        hh = conn.execute(
            "SELECT id FROM households WHERE invite_code='DEMO0001'"
        ).fetchone()
        hh_id = hh["id"]

        # Add all 3 as members
        for uid in user_ids.values():
            conn.execute(
                "INSERT OR IGNORE INTO household_members (household_id, user_id) VALUES (?,?)",
                (hh_id, uid)
            )

        # Create habits per user
        habit_ids = {}  # (user_name, habit_name) -> habit_id
        for name, uid in user_ids.items():
            for habit in ["gym", "water", "sleep", "vitamins"]:
                conn.execute("""
                    INSERT OR IGNORE INTO habits
                    (user_id, name, icon, unit, target, habit_type)
                    VALUES (?,?,?,?,?,?)
                """, (
                    uid, habit,
                    DEMO_HABIT_ICONS[habit],
                    DEMO_HABIT_UNITS[habit],
                    DEMO_HABIT_TARGETS[habit],
                    DEMO_HABIT_TYPES[habit],
                ))
                hid = conn.execute(
                    "SELECT id FROM habits WHERE user_id=? AND name=?", (uid, habit)
                ).fetchone()["id"]
                habit_ids[(name, habit)] = hid

        # Insert all log rows
        for _, row in df.iterrows():
            uname = row["user_name"]
            habit = row["habit"]
            if uname not in user_ids or (uname, habit) not in habit_ids:
                continue
            uid = user_ids[uname]
            hid = habit_ids[(uname, habit)]
            log_date = str(row["date"].date())
            status = int(row["status"])
            value = float(row["value"]) if "value" in row else 0.0
            conn.execute("""
                INSERT OR IGNORE INTO logs
                (user_id, habit_id, log_date, status, value)
                VALUES (?,?,?,?,?)
            """, (uid, hid, log_date, status, value))

        conn.commit()
        print("✅ Demo data seeded from house_1.csv")

    except Exception as e:
        print(f"Demo seed error: {e}")
    finally:
        conn.close()


def get_demo_credentials() -> list:
    """Return demo login hints for the login page."""
    return [
        {"name": "Ram",   "email": "ram@demo.habitos",   "password": "demo1234"},
        {"name": "Mathi", "email": "mathi@demo.habitos", "password": "demo1234"},
        {"name": "Guna",  "email": "guna@demo.habitos",  "password": "demo1234"},
    ]