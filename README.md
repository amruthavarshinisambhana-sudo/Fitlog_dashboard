# FitLog Dashboard

A Streamlit workout tracker that saves workout history to `workouts.csv` and `fitlog.db`.

## Start the dashboard

Open PowerShell in this folder, then run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run "dashboard (1).py"
```

## Data entry and report download

The dashboard already includes a workout entry form and a CSV download button in Workout History. These features are in `dashboard (1).py`.

## Start the JSON API

In a second PowerShell window in this folder, run:

```powershell
python api.py
```

The API listens only on your computer at `http://127.0.0.1:8000`.

- `GET /api/health` checks that the API is running.
- `GET /api/workouts` returns saved workouts as JSON.
- `POST /api/workouts` adds a workout. Send JSON such as:

```json
{"date":"2026-11-03","workout":"Running","duration":30,"calories":200}
```

The POST endpoint validates the values and stores the workout in `fitlog.db`.

## Run the test cases

```powershell
python -m unittest discover -s tests -v
```

## GitHub automatic checks

The workflow in `.github/workflows/ci.yml` runs the tests when code is pushed to GitHub or a pull request is opened. To use it, create a GitHub repository, then initialize and connect this folder with Git:

```powershell
git init
git add .
git commit -m "Add FitLog project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the sample GitHub address with your repository address. GitHub will show the automatic test result in the **Actions** tab.
