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

## Enable the Gemini AI Coach

The optional coach uses Google's Gemini `generateContent` API. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey), then:

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Replace the placeholder with your key, keeping the quotes:

   ```toml
   GEMINI_API_KEY = "your-key-goes-here"
   ```

3. Restart Streamlit and open **Gemini AI Coach** in the sidebar.

The secrets file is ignored by Git. Do not commit or share the real key. When you ask Gemini a question, the app sends that question and a summary of your signed-in account's workouts to Google.

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
