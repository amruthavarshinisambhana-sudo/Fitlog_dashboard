# FitLog Dashboard

FitLog is a Streamlit workout tracker with local accounts, private workout history, personal CSV reports, an authenticated local API, and an optional Anthropic Claude coach.

## Start the dashboard

Open PowerShell in this folder and run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run "dashboard (1).py"
```

Create an account from the **Sign up** tab the first time you open it. The first account becomes the administrator; accounts created afterward are regular users. Administrators can view account names, roles, and workout counts in **Admin Panel**, and change another account's role. The panel does not expose workout entries. Sign in to see your account's workouts. Passwords are stored as salted PBKDF2 hashes. Existing single-user workouts are assigned to the first account that signs up.

## Recover the administrator password

The login page has an **Admin recovery** tab. To enable it, generate a strong recovery code locally:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add the result to the deployed app's private Streamlit **Settings → Secrets** as TOML:

```toml
FITLOG_ADMIN_RECOVERY_CODE = "paste-the-generated-value-here"
```

Never commit or share this code. In the app, use **Admin recovery**, enter the code, and choose a new password. Recovery resets the first administrator account; after success, replace the code in Streamlit Secrets with a newly generated value so the old code cannot be reused. The app never stores or displays the recovery code.

## Log workouts and download reports

Use **Log a Workout** to enter an activity. The dashboard stores it in SQLite under the signed-in account. The sidebar's **My Data Report** downloads only that account's workouts as CSV. The Workout History section also has filters and a CSV download.

## Back up and restore data

Open **Backup & SQLite** in the sidebar. **Export full JSON snapshot** creates a backup of the signed-in account's workouts. **Export SQLite SQL dump** downloads SQL statements that can be opened with SQLite tools. To restore, upload a FitLog JSON snapshot and select **Restore JSON backup to my account**. Existing matching workouts are skipped to avoid duplicates. CSV download is available under **My Data Report**.

## Enable the Claude AI Coach

The optional coach uses Anthropic's Messages API. Create an API key in the [Anthropic Console](https://console.anthropic.com/), open **Claude AI Coach** in the sidebar, and paste the key into the masked **Anthropic API key** field. The key stays in the active Streamlit session and is not saved to the project files. Do not share it. You can ask questions about your signed-in account's report or ask general questions. The app sends your question and a report summary to Anthropic with each request.

For repeat local use, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `ANTHROPIC_API_KEY = "your-key"`. That file is ignored by Git; never commit it.

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
