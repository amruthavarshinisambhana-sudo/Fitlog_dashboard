# FitLog Dashboard

FitLog is a Streamlit workout tracker with local accounts, private workout history, personal CSV reports, an authenticated local API, and an optional Gemini AI coach.

## Start the dashboard

Open PowerShell in this folder and run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run "dashboard (1).py"
```

Create an account from the **Sign up** tab the first time you open it. Sign in afterward to see that account's workouts. Passwords are stored as salted PBKDF2 hashes. Existing single-user workouts are assigned to the first account that signs up.

## Log workouts and download reports

Use **Log a Workout** to enter an activity. The dashboard stores it in SQLite under the signed-in account. The sidebar's **My Data Report** downloads only that account's workouts as CSV. The Workout History section also has filters and a CSV download.

## Back up and restore data

Open **Backup & SQLite** in the sidebar. **Export full JSON snapshot** creates a backup of the signed-in account's workouts. **Export SQLite SQL dump** downloads SQL statements that can be opened with SQLite tools. To restore, upload a FitLog JSON snapshot and select **Restore JSON backup to my account**. Existing matching workouts are skipped to avoid duplicates. CSV download is available under **My Data Report**.

## Enable the Gemini AI Coach

The optional coach uses Google's Gemini Interactions API. Create an authorization key in [Google AI Studio](https://aistudio.google.com/api-keys), open **Ask AI Gemini** in the sidebar, and paste the key into the masked **Gemini API key** field. The key stays in the active Streamlit session and is not saved to the project files. Do not share the key. When you ask Gemini a question, the app sends that question and a summary of your signed-in account's workouts to Google.

For repeat local use, you can instead save the key in `.streamlit/secrets.toml` as `GEMINI_API_KEY = "your-key"`. That file is ignored by Git; never commit it.

## Local API

Start it in a second PowerShell window:

```powershell
python api.py
```

The API listens on `http://127.0.0.1:8000` and requires HTTP Basic authentication using a FitLog username and password.

- `GET /api/health` checks whether the API is running.
- `GET /api/workouts` returns the authenticated account's workouts.
- `POST /api/workouts` adds a workout to the authenticated account. Example JSON:

  ```json
  {"date":"2026-11-03","workout":"Running","duration":30,"calories":200}
  ```

## Run the tests

```powershell
python -m unittest discover -s tests -v
```

The tests cover password authentication, separate workout histories for different accounts, and invalid workout values. GitHub Actions runs them automatically when changes are pushed.
