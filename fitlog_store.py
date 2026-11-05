"""SQLite storage and local account helpers for FitLog."""

import csv
import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_FILE = Path(os.environ.get("FITLOG_DB", BASE_DIR / "fitlog.db"))
CSV_FILE = BASE_DIR / "workouts.csv"
PASSWORD_ITERATIONS = 310_000


def _connect(db_file=DB_FILE):
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_file=DB_FILE):
    """Create account tables and migrate the old single-user schema."""
    with closing(_connect(db_file)) as conn:
        with conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                        CHECK(role IN ('admin', 'user'))
                )"""
            )
            user_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(users)").fetchall()
            }
            if "role" not in user_columns:
                conn.execute(
                    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
                )
            # Existing projects get one admin: the account created first.
            conn.execute(
                """UPDATE users SET role = 'admin'
                   WHERE id = (SELECT MIN(id) FROM users)
                   AND NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin')"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    workout TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    calories INTEGER NOT NULL
                )"""
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(workouts)").fetchall()
            }
            if "user_id" not in columns:
                conn.execute(
                    "ALTER TABLE workouts ADD COLUMN user_id INTEGER "
                    "REFERENCES users(id)"
                )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workouts_user_date "
                "ON workouts(user_id, date)"
            )


def _password_digest(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    ).hex()


def _make_password_hash(password):
    salt = secrets.token_bytes(16)
    return f"{salt.hex()}${_password_digest(password, salt)}"


def _verify_password(password, stored_hash):
    try:
        salt_hex, digest = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(_password_digest(password, salt), digest)


def _clean_legacy_record(row):
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    aliases = {
        "workout_type": "workout",
        "activity": "workout",
        "exercise": "workout",
        "duration_minutes": "duration",
        "minutes": "duration",
        "calories_burned": "calories",
        "calorie": "calories",
        "burned_calories": "calories",
        "workout_date": "date",
    }
    for alias, canonical in aliases.items():
        if alias in normalized and canonical not in normalized:
            normalized[canonical] = normalized[alias]
    try:
        workout_date = date.fromisoformat(str(normalized["date"])).isoformat()
        workout = str(normalized["workout"]).strip()
        duration = int(float(normalized["duration"]))
        calories = int(float(normalized["calories"]))
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if not workout or duration <= 0 or calories < 0:
        return None
    return workout_date, workout, duration, calories


def _migrate_legacy_csv(conn, user_id, csv_file):
    csv_file = Path(csv_file) if csv_file else None
    if not csv_file or not csv_file.exists():
        return
    try:
        with csv_file.open("r", newline="", encoding="utf-8-sig") as handle:
            rows = csv.DictReader(handle)
            for row in rows:
                clean = _clean_legacy_record(row)
                if clean is None:
                    continue
                exists = conn.execute(
                    """SELECT 1 FROM workouts WHERE user_id = ? AND date = ?
                       AND workout = ? AND duration = ? AND calories = ? LIMIT 1""",
                    (user_id, *clean),
                ).fetchone()
                if not exists:
                    conn.execute(
                        """INSERT INTO workouts
                           (user_id, date, workout, duration, calories)
                           VALUES (?, ?, ?, ?, ?)""",
                        (user_id, *clean),
                    )
    except (OSError, csv.Error, UnicodeError):
        # An unreadable legacy CSV should not prevent a new account from working.
        return


def create_user(username, password, db_file=DB_FILE, legacy_csv_file=CSV_FILE):
    username = str(username or "").strip()
    if len(username) < 3 or len(username) > 40:
        raise ValueError("Username must be between 3 and 40 characters.")
    if len(password or "") < 8:
        raise ValueError("Password must contain at least 8 characters.")

    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        try:
            with conn:
                existing_users = conn.execute(
                    "SELECT COUNT(*) AS count FROM users"
                ).fetchone()["count"]
                role = "admin" if existing_users == 0 else "user"
                cursor = conn.execute(
                    """INSERT INTO users (username, password_hash, created_at, role)
                       VALUES (?, ?, ?, ?)""",
                    (
                        username,
                        _make_password_hash(password),
                        datetime.now(timezone.utc).isoformat(),
                        role,
                    ),
                )
                user_id = cursor.lastrowid
                if existing_users == 0:
                    # Keep old workout records with the first account only.
                    conn.execute(
                        "UPDATE workouts SET user_id = ? WHERE user_id IS NULL",
                        (user_id,),
                    )
                    _migrate_legacy_csv(conn, user_id, legacy_csv_file)
        except sqlite3.IntegrityError as exc:
            raise ValueError("That username is already registered.") from exc
    return {"id": user_id, "username": username, "role": role}


def authenticate_user(username, password, db_file=DB_FILE):
    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        user = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (str(username or "").strip(),),
        ).fetchone()
    if not user or not _verify_password(str(password or ""), user["password_hash"]):
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }


def reset_first_admin_password(recovery_code, new_password, configured_code, db_file=DB_FILE):
    """Reset the first administrator's password using a private deployment secret."""
    expected = str(configured_code or "")
    supplied = str(recovery_code or "")
    if len(expected) < 32 or not secrets.compare_digest(supplied, expected):
        return None
    if len(new_password or "") < 8:
        raise ValueError("Password must contain at least 8 characters.")

    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        with conn:
            admin = conn.execute(
                "SELECT id, username FROM users WHERE role = 'admin' ORDER BY id LIMIT 1"
            ).fetchone()
            if not admin:
                return None
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (_make_password_hash(new_password), admin["id"]),
            )
    return {"username": admin["username"]}


def get_user_role(user_id, db_file=DB_FILE):
    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return user["role"] if user else None


def list_users_for_admin(actor_user_id, db_file=DB_FILE):
    """Return account metadata only, and only to a current administrator."""
    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        actor = conn.execute(
            "SELECT role FROM users WHERE id = ?", (actor_user_id,)
        ).fetchone()
        if not actor or actor["role"] != "admin":
            raise PermissionError("Administrator access is required.")
        rows = conn.execute(
            """SELECT users.id, users.username, users.role, users.created_at,
                      COUNT(workouts.id) AS workout_count
               FROM users LEFT JOIN workouts ON workouts.user_id = users.id
               GROUP BY users.id ORDER BY users.id"""
        ).fetchall()
    return [dict(row) for row in rows]


def set_user_role(actor_user_id, target_user_id, role, db_file=DB_FILE):
    """Let an administrator change another user's role without removing the last admin."""
    if role not in {"admin", "user"}:
        raise ValueError("Role must be 'admin' or 'user'.")
    if actor_user_id == target_user_id:
        raise ValueError("You cannot change your own role.")

    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        with conn:
            actor = conn.execute(
                "SELECT role FROM users WHERE id = ?", (actor_user_id,)
            ).fetchone()
            if not actor or actor["role"] != "admin":
                raise PermissionError("Administrator access is required.")
            target = conn.execute(
                "SELECT id FROM users WHERE id = ?", (target_user_id,)
            ).fetchone()
            if not target:
                raise ValueError("That account does not exist.")
            if role == "user":
                admin_count = conn.execute(
                    "SELECT COUNT(*) AS count FROM users WHERE role = 'admin'"
                ).fetchone()["count"]
                target_role = conn.execute(
                    "SELECT role FROM users WHERE id = ?", (target_user_id,)
                ).fetchone()["role"]
                if target_role == "admin" and admin_count <= 1:
                    raise ValueError("FitLog must keep at least one administrator.")
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, target_user_id))


def list_workouts(user_id, db_file=DB_FILE):
    if user_id is None:
        return []
    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        rows = conn.execute(
            """SELECT id, date, workout, duration, calories FROM workouts
               WHERE user_id = ? ORDER BY date DESC, id DESC""",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_workout(user_id, payload, db_file=DB_FILE):
    if not isinstance(payload, dict):
        raise ValueError("Workout must be a JSON object.")
    try:
        workout_date = date.fromisoformat(str(payload["date"])).isoformat()
        workout = str(payload["workout"]).strip()
        duration = int(payload["duration"])
        calories = int(payload["calories"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "Provide date (YYYY-MM-DD), workout, duration, and calories."
        ) from exc
    if not workout:
        raise ValueError("Workout name cannot be empty.")
    if duration <= 0:
        raise ValueError("Duration must be greater than zero.")
    if calories < 0:
        raise ValueError("Calories cannot be negative.")

    init_db(db_file)
    with closing(_connect(db_file)) as conn:
        with conn:
            cursor = conn.execute(
                """INSERT INTO workouts
                   (user_id, date, workout, duration, calories)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, workout_date, workout, duration, calories),
            )
            row_id = cursor.lastrowid
    return {
        "id": row_id,
        "date": workout_date,
        "workout": workout,
        "duration": duration,
        "calories": calories,
    }
