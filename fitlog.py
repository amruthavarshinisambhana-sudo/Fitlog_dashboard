
import argparse
import csv
import sqlite3
import difflib
from pathlib import Path
from datetime import date, timedelta
from dataclasses import dataclass


# -----------------------------------------
# FILES AND DATABASE
# -----------------------------------------

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "workouts.csv"
DB_FILE = BASE_DIR / "fitlog.db"


# -----------------------------------------
# ALLOWED WORKOUT CATEGORIES
# -----------------------------------------

WORKOUT_CATEGORIES = [
    "Running",
    "Walking",
    "Push-ups",
    "Weightlifting",
    "Boxing",
    "Cycling",
    "Cardio",
    "Yoga",
    "Swimming",
    "Squats",
]


# -----------------------------------------
# WORKOUT DATA MODEL
# -----------------------------------------

@dataclass
class Workout:
    date: str
    workout: str
    duration: int
    calories: int


# -----------------------------------------
# NORMALIZE WORKOUT NAMES
# -----------------------------------------

def normalize_name(name):
    """Ignore spaces, hyphens and letter case."""
    return "".join(
        character.lower()
        for character in name
        if character.isalnum()
    )


def validate_workout(name):
    """Return the official category name or report an error."""

    if not name or not name.strip():
        print("Error: Workout name cannot be empty.")
        return None

    category_map = {
        normalize_name(category): category
        for category in WORKOUT_CATEGORIES
    }

    normalized = normalize_name(name)

    # Accept capitalization and simple formatting variations.
    if normalized in category_map:
        return category_map[normalized]

    # Suggest a spelling correction.
    matches = difflib.get_close_matches(
        normalized,
        list(category_map.keys()),
        n=1,
        cutoff=0.65,
    )

    print(f"Unknown workout category: {name}")

    if matches:
        suggestion = category_map[matches[0]]
        print(f"Did you mean '{suggestion}'?")

    print("Available categories:")
    for category in WORKOUT_CATEGORIES:
        print(f"- {category}")

    return None


# -----------------------------------------
# INITIALIZE CSV STORAGE
# -----------------------------------------

def initialize_csv():
    if not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["date", "workout", "duration", "calories"]
            )


# -----------------------------------------
# INITIALIZE SQLITE DATABASE
# -----------------------------------------

def initialize_database():
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                workout TEXT NOT NULL,
                duration INTEGER NOT NULL CHECK(duration > 0),
                calories INTEGER NOT NULL CHECK(calories >= 0)
            )
        """)


# -----------------------------------------
# VALIDATE NUMERIC INPUTS
# -----------------------------------------

def validate_numbers(duration, calories):
    if duration is None or calories is None:
        print("Error: Duration and calories are required.")
        return False

    if duration <= 0:
        print("Error: Duration must be greater than zero.")
        return False

    if calories < 0:
        print("Error: Calories cannot be negative.")
        return False

    return True


# -----------------------------------------
# ADD A WORKOUT
# -----------------------------------------

def add_workout(name, duration, calories):
    category = validate_workout(name)

    if category is None:
        return

    if not validate_numbers(duration, calories):
        return

    today = date.today().isoformat()

    workout = Workout(
        date=today,
        workout=category,
        duration=duration,
        calories=calories,
    )

    # Save to CSV.
    initialize_csv()

    with open(
        CSV_FILE, "a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            workout.date,
            workout.workout,
            workout.duration,
            workout.calories,
        ])

    # Save to SQLite.
    initialize_database()

    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("""
            INSERT INTO workouts
                (date, workout, duration, calories)
            VALUES (?, ?, ?, ?)
        """, (
            workout.date,
            workout.workout,
            workout.duration,
            workout.calories,
        ))

    print("Workout added successfully!")
    print(f"Date: {workout.date}")
    print(f"Category: {workout.workout}")
    print(f"Duration: {workout.duration} minutes")
    print(f"Calories: {workout.calories}")


# -----------------------------------------
# READ CSV WORKOUTS
# -----------------------------------------

def read_csv_workouts():
    initialize_csv()
    records = []

    with open(
        CSV_FILE, "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                workout_date = row["date"].strip()
                category = row["workout"].strip()
                duration = int(row["duration"])
                calories = int(row["calories"])

                # Ignore malformed records in reports.
                date.fromisoformat(workout_date)

                records.append({
                    "date": workout_date,
                    "workout": category,
                    "duration": duration,
                    "calories": calories,
                })

            except (ValueError, KeyError, TypeError):
                continue

    return records


# -----------------------------------------
# LIST WORKOUT JOURNAL
# -----------------------------------------

def list_workouts():
    records = read_csv_workouts()

    print("\nWorkout Journal")
    print("-" * 42)

    if not records:
        print("No workout records found.")
        return

    for record in records:
        print(
            f"Date: {record['date']} | "
            f"Category: {record['workout']} | "
            f"Duration: {record['duration']} minutes | "
            f"Calories: {record['calories']}"
        )


# -----------------------------------------
# LIST SQLITE RECORDS
# -----------------------------------------

def sql_list_workouts():
    initialize_database()

    with sqlite3.connect(DB_FILE) as connection:
        rows = connection.execute("""
            SELECT id, date, workout, duration, calories
            FROM workouts
            ORDER BY id
        """).fetchall()

    print("\nSQLite Workout Records")
    print("-" * 42)

    if not rows:
        print("No workout records found in SQLite.")
        return

    for row in rows:
        workout_id, workout_date, category, duration, calories = row

        print(
            f"ID: {workout_id} | Date: {workout_date} | "
            f"Category: {category} | Duration: {duration} minutes | "
            f"Calories: {calories}"
        )


# -----------------------------------------
# FILTER RECORDS BY DATE
# -----------------------------------------

def filter_records(records, week=False, month=False):
    today = date.today()

    if week:
        # Monday to Sunday of the current week.
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

        return [
            record for record in records
            if start_date <= date.fromisoformat(record["date"]) <= end_date
        ]

    if month:
        # Current calendar month.
        return [
            record for record in records
            if date.fromisoformat(record["date"]).year == today.year
            and date.fromisoformat(record["date"]).month == today.month
        ]

    return records


# -----------------------------------------
# SUMMARY REPORT
# -----------------------------------------

def summary_report(week=False, month=False):
    records = read_csv_workouts()
    records = filter_records(records, week=week, month=month)

    if week:
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)

        print("\nWeekly Summary Report")
        print(f"Period: {start} to {end}")

    elif month:
        today = date.today()
        print("\nMonthly Summary Report")
        print(f"Month: {today.strftime('%B %Y')}")

    else:
        print("\nFitLog Summary Report")
        print("Period: All recorded workouts")

    print("-" * 42)

    total_workouts = len(records)
    total_duration = sum(
        record["duration"] for record in records
    )
    total_calories = sum(
        record["calories"] for record in records
    )

    average_duration = (
        total_duration / total_workouts
        if total_workouts else 0
    )

    print(f"Total Workouts: {total_workouts}")
    print(f"Total Duration: {total_duration} minutes")
    print(f"Total Calories: {total_calories}")
    print(f"Average Duration: {average_duration:.2f} minutes")

    print("\nCategory-wise Summary")
    print("-" * 42)

    categories = {}

    for record in records:
        name = record["workout"]

        if name not in categories:
            categories[name] = {
                "count": 0,
                "duration": 0,
                "calories": 0,
            }

        categories[name]["count"] += 1
        categories[name]["duration"] += record["duration"]
        categories[name]["calories"] += record["calories"]

    if not categories:
        print("No workouts found for this period.")
        return

    for name, data in categories.items():
        print(f"\nCategory: {name}")
        print(f"Workout Count: {data['count']}")
        print(f"Total Duration: {data['duration']} minutes")
        print(f"Total Calories: {data['calories']}")


# -----------------------------------------
# COMMAND-LINE INTERFACE
# -----------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FitLog - Workout Journal and Tracker"
    )

    parser.add_argument(
        "action",
        choices=["add", "list", "sql-list", "summary"],
        help="Action to perform",
    )

    # Positional arguments.
    parser.add_argument("workout", nargs="?")
    parser.add_argument("duration", nargs="?", type=int)
    parser.add_argument("calories", nargs="?", type=int)

    # Optional arguments.
    parser.add_argument("--workout", dest="opt_workout")
    parser.add_argument("--duration", dest="opt_duration", type=int)
    parser.add_argument("--calories", dest="opt_calories", type=int)

    # Summary period options.
    period = parser.add_mutually_exclusive_group()
    period.add_argument(
        "--week",
        action="store_true",
        help="Show the current week's summary",
    )
    period.add_argument(
        "--month",
        action="store_true",
        help="Show the current month's summary",
    )

    args = parser.parse_args()

    initialize_csv()
    initialize_database()

    if args.action == "add":
        # Optional values take priority over positional values.
        workout = (
            args.opt_workout
            if args.opt_workout is not None
            else args.workout
        )

        duration = (
            args.opt_duration
            if args.opt_duration is not None
            else args.duration
        )

        calories = (
            args.opt_calories
            if args.opt_calories is not None
            else args.calories
        )

        if workout is None or duration is None or calories is None:
            parser.error(
                "add requires a workout, duration and calories. "
                "Use positional or optional arguments."
            )

        add_workout(workout, duration, calories)

    elif args.action == "list":
        list_workouts()

    elif args.action == "sql-list":
        sql_list_workouts()

    elif args.action == "summary":
        summary_report(week=args.week, month=args.month)


if __name__ == "__main__":
    main()
