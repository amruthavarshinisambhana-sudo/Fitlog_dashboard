import tempfile
import unittest
from pathlib import Path

from api import add_workout, list_workouts


class FitLogApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test_fitlog.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_list_workout(self):
        created = add_workout(
            {
                "date": "2026-11-03",
                "workout": "  Running  ",
                "duration": 30,
                "calories": 200,
            },
            self.db_file,
        )

        self.assertEqual(created["workout"], "Running")
        self.assertEqual(created["duration"], 30)
        self.assertEqual(list_workouts(self.db_file), [created])

    def test_rejects_non_positive_duration(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            add_workout(
                {
                    "date": "2026-11-03",
                    "workout": "Running",
                    "duration": 0,
                    "calories": 200,
                },
                self.db_file,
            )

    def test_rejects_invalid_date(self):
        with self.assertRaisesRegex(ValueError, "Provide date"):
            add_workout(
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
