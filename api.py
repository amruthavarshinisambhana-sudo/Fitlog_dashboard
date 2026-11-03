"""Small JSON API for reading and adding FitLog workouts.

Run with: python api.py
The API listens at http://127.0.0.1:8000.
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
DB_FILE = Path(os.environ.get("FITLOG_DB", BASE_DIR / "fitlog.db"))


def init_db(db_file=DB_FILE):
    with closing(sqlite3.connect(db_file)) as conn:
        with conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    workout TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    calories INTEGER NOT NULL
                )"""
            )


def list_workouts(db_file=DB_FILE):
    init_db(db_file)
    with closing(sqlite3.connect(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, date, workout, duration, calories "
            "FROM workouts ORDER BY date DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def add_workout(payload, db_file=DB_FILE):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    try:
        workout_date = date.fromisoformat(str(payload["date"])).isoformat()
        workout = str(payload["workout"]).strip()
        duration = int(payload["duration"])
        calories = int(payload["calories"])
    except (KeyError, TypeError, ValueError) as exc:
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
    with closing(sqlite3.connect(db_file)) as conn:
        with conn:
            cursor = conn.execute(
                "INSERT INTO workouts (date, workout, duration, calories) "
                "VALUES (?, ?, ?, ?)",
                (workout_date, workout, duration, calories),
            )
            workout_id = cursor.lastrowid
    return {
        "id": workout_id,
        "date": workout_date,
        "workout": workout,
        "duration": duration,
        "calories": calories,
    }


class FitLogHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, value):
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/api/workouts":
            self._send_json(200, list_workouts())
        elif urlparse(self.path).path == "/api/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/workouts":
            self._send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            created = add_workout(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._send_json(400, {"error": str(exc)})
            return
        self._send_json(201, created)

    def log_message(self, format_string, *args):
        # Keep the default server output concise and avoid logging request data.
        super().log_message(format_string, *args)


if __name__ == "__main__":
    init_db()
    print("FitLog API running at http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), FitLogHandler).serve_forever()
