
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# Save the CSV beside this script.
CSV_FILE = Path(__file__).resolve().parent / "workouts.csv"

# 30 sample workouts using your existing 10 categories.
workouts = [
    ("Running", 30, 250),
    ("Walking", 25, 110),
    ("Cycling", 40, 320),
    ("Swimming", 30, 250),
    ("Boxing", 35, 320),
    ("Push-ups", 15, 50),
    ("Weightlifting", 45, 250),
    ("Yoga", 25, 80),
    ("Squats", 15, 70),
    ("Cardio", 30, 220),
    ("Running", 35, 290),
    ("Walking", 20, 90),
    ("Cycling", 45, 350),
    ("Swimming", 40, 330),
    ("Boxing", 30, 280),
    ("Push-ups", 20, 65),
    ("Weightlifting", 50, 300),
    ("Yoga", 30, 100),
    ("Squats", 20, 90),
    ("Cardio", 25, 180),
    ("Running", 25, 210),
    ("Walking", 30, 130),
    ("Cycling", 35, 280),
    ("Swimming", 25, 200),
    ("Boxing", 40, 360),
    ("Push-ups", 10, 35),
    ("Weightlifting", 35, 200),
    ("Yoga", 20, 65),
    ("Squats", 25, 110),
    ("Cardio", 35, 260),
]

# Spread sample dates across the last 30 days.
today = date.today()
random.seed(42)
dates = [
    today - timedelta(days=random.randint(0, 29))
    for _ in workouts
]

# Create the file with a header if it doesn't exist.
file_exists = CSV_FILE.exists() and CSV_FILE.stat().st_size > 0

with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    if not file_exists:
        writer.writerow(["date", "workout", "duration", "calories"])

    for workout_date, (name, duration, calories) in zip(dates, workouts):
        writer.writerow([
            workout_date.isoformat(),
            name,
            duration,
            calories,
        ])

print("Successfully added 30 sample workouts!")
print(f"CSV file: {CSV_FILE}")
print("Your existing records have been preserved.")
