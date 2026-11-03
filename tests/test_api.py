import tempfile
import unittest
from pathlib import Path

from fitlog_store import (
    authenticate_user,
    create_user,
    list_workouts,
    save_workout,
)


class FitLogAccountTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test_fitlog.db"
        self.legacy_csv = Path(self.temp_dir.name) / "missing_workouts.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_account(self, username):
        return create_user(
            username,
            "secure-pass-123",
            self.db_file,
            self.legacy_csv,
        )

    def test_account_password_authentication(self):
        user = self.create_account("amrutha")

        self.assertEqual(
            authenticate_user("amrutha", "secure-pass-123", self.db_file),
            user,
        )
        self.assertIsNone(
            authenticate_user("amrutha", "wrong-password", self.db_file)
        )

    def test_workouts_are_private_to_each_account(self):
        first_user = self.create_account("runner_one")
        second_user = self.create_account("runner_two")
        workout = {
            "date": "2026-11-03",
            "workout": "  Running  ",
            "duration": 30,
            "calories": 200,
        }

        created = save_workout(first_user["id"], workout, self.db_file)

        self.assertEqual(created["workout"], "Running")
        self.assertEqual(list_workouts(first_user["id"], self.db_file), [created])
        self.assertEqual(list_workouts(second_user["id"], self.db_file), [])

    def test_rejects_invalid_records(self):
        user = self.create_account("valid_user")
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            save_workout(
                user["id"],
                {
                    "date": "2026-11-03",
                    "workout": "Running",
                    "duration": 0,
                    "calories": 200,
                },
                self.db_file,
            )
        with self.assertRaisesRegex(ValueError, "Provide date"):
            save_workout(
                user["id"],
                {
                    "date": "not-a-date",
                    "workout": "Running",
                    "duration": 30,
                    "calories": 200,
                },
                self.db_file,
            )


if __name__ == "__main__":
    unittest.main()
