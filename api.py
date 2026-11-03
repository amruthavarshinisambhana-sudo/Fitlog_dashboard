"""Local JSON API for authenticated FitLog accounts.

Run with: python api.py
The API listens only on this computer at http://127.0.0.1:8000.
"""

import base64
import binascii
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from fitlog_store import authenticate_user, init_db, list_workouts, save_workout


class FitLogHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, value, extra_headers=None):
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _current_user(self):
        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Basic "):
            return None
        try:
            raw = base64.b64decode(authorization[6:], validate=True).decode("utf-8")
            username, password = raw.split(":", 1)
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None
        return authenticate_user(username, password)

    def _require_user(self):
        user = self._current_user()
        if user is None:
            self._send_json(
                401,
                {"error": "Sign up in the FitLog dashboard before using the API."},
                {"WWW-Authenticate": 'Basic realm="FitLog API"'},
            )
        return user

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, {"status": "ok"})
        elif path == "/api/workouts":
            user = self._require_user()
            if user:
                self._send_json(200, list_workouts(user["id"]))
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/workouts":
            self._send_json(404, {"error": "Not found"})
            return
        user = self._require_user()
        if not user:
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("Request body must be between 1 and 16384 bytes.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            created = save_workout(user["id"], payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._send_json(400, {"error": str(exc)})
            return
        self._send_json(201, created)

    def log_message(self, format_string, *args):
        super().log_message(format_string, *args)


if __name__ == "__main__":
    init_db()
    print("FitLog API running at http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), FitLogHandler).serve_forever()
