
import streamlit as st
import pandas as pd
import json
import os
import random
import time
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from urllib import error, request
import plotly.express as px
import plotly.graph_objects as go

from fitlog_store import (
    authenticate_user,
    create_user,
    get_user_role,
    init_db,
    list_users_for_admin,
    list_workouts as list_user_workouts,
    reset_first_admin_password,
    save_workout as save_user_workout,
    set_user_role,
)

# --------------------------------------------------
# FITLOG - SMART WORKOUT TRACKER
# --------------------------------------------------

st.set_page_config(
    page_title="FitLog | Smart Fitness Dashboard",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "workouts.csv"

MINT = "#A9E8C0"
LAVENDER = "#D8C4FF"
BLUE = "#B8D2FF"
PEACH = "#FFD7C2"
TEXT = "#F2F7F3"
MUTED = "#B8C8BD"
PANEL = "#1B2821"

WORKOUT_ICONS = {
    "Running": "🏃",
    "Walking": "🚶",
    "Push-ups": "💪",
    "Weightlifting": "🏋️",
    "Boxing": "🥊",
    "Cycling": "🚴",
    "Cardio": "❤️",
    "Yoga": "🧘",
    "Swimming": "🏊",
    "Squats": "🦵",
    "Other": "✨",
}

WORKOUT_TYPES = list(WORKOUT_ICONS.keys())

# --------------------------------------------------
# DESIGN / CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        background: linear-gradient(135deg, #101713 0%, #17231C 55%, #111A15 100%);
        color: #F2F7F3;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(16, 23, 19, 0.92);
    }

    [data-testid="stSidebar"] {
        background: #19241D;
        border-right: 1px solid #34483A;
    }

    [data-testid="stSidebar"] * {
        color: #F2F7F3;
    }

    h1, h2, h3, h4, p, label {
        color: #F2F7F3;
    }

    .stApp label,
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stWidgetLabel"] label {
        color: #E6F1E8 !important;
        font-weight: 600 !important;
    }

    .stMarkdown, .stCaption, [data-testid="stCaptionContainer"] {
        color: #B8C8BD;
    }

    .stApp input,
    .stApp textarea {
        color: #F4FFF6 !important;
        background-color: #19251F !important;
        border: 1px solid #668573 !important;
        border-radius: 10px !important;
    }

    .stApp input::placeholder,
    .stApp textarea::placeholder {
        color: #AABCB0 !important;
        opacity: 1 !important;
    }

    .stApp [data-baseweb="select"] > div {
        background-color: #19251F !important;
        color: #F4FFF6 !important;
        border: 1px solid #668573 !important;
        border-radius: 10px !important;
    }

    .stApp [data-baseweb="select"] span,
    .stApp [data-baseweb="select"] input {
        color: #F4FFF6 !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background-color: #24352A !important;
    }

    [role="option"] {
        color: #F4FFF6 !important;
    }

    .stApp input:focus,
    .stApp textarea:focus {
        border-color: #A9E8C0 !important;
        box-shadow: 0 0 0 2px #A9E8C044 !important;
    }

    [data-testid="stDateInput"] button,
    [data-testid="stNumberInput"] button {
        color: #A9E8C0 !important;
        background: #24362A !important;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #223128, #19241D);
        border: 1px solid #3B5243;
        border-radius: 16px;
        padding: 17px 18px;
        box-shadow: 0 5px 18px #00000018;
    }

    [data-testid="stMetricLabel"] {
        color: #B8C8BD !important;
    }

    [data-testid="stMetricValue"] {
        color: #A9E8C0 !important;
        font-weight: 800;
    }

    [data-testid="stMetricDelta"] {
        color: #D8C4FF !important;
    }

    div.stButton > button,
    div.stFormSubmitButton > button,
    div.stDownloadButton > button {
        background: linear-gradient(90deg, #A9E8C0, #B8D2FF);
        color: #152219 !important;
        border: none;
        border-radius: 11px;
        font-weight: 800;
        padding: 0.55rem 1rem;
        transition: 0.2s ease;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover,
    div.stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 16px #A9E8C033;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #34483A;
        border-radius: 12px;
        overflow: hidden;
    }

    [data-testid="stTabs"] button {
        color: #D9E7DC !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #A9E8C0 !important;
        border-bottom-color: #A9E8C0 !important;
    }

    .hero {
        background: linear-gradient(120deg, #20352A, #283044);
        border: 1px solid #506B59;
        border-radius: 22px;
        padding: 25px 28px;
        margin: 8px 0 24px 0;
    }

    .hero-title {
        font-size: 34px;
        font-weight: 800;
        color: #F2F7F3;
        margin: 0;
    }

    .hero-subtitle {
        color: #C3D4C8;
        font-size: 15px;
        margin-top: 7px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 800;
        color: #E6F1E8;
        margin: 10px 0 5px 0;
    }

    .soft-card {
        background: #1B2821;
        border: 1px solid #3B5243;
        border-radius: 16px;
        padding: 17px;
        margin-bottom: 12px;
    }

    .small-muted {
        color: #B8C8BD;
        font-size: 13px;
    }

    .pastel-pill {
        display: inline-block;
        color: #17231C;
        background: #A9E8C0;
        padding: 5px 11px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 800;
    }

    @keyframes fitlog-run {
        0%   { transform: translateX(0) rotate(-5deg); }
        50%  { transform: translateX(10px) rotate(5deg); }
        100% { transform: translateX(0) rotate(-5deg); }
    }

    .fitlog-mascot {
        display: inline-block;
        font-size: 36px;
        animation: fitlog-run 1.5s ease-in-out infinite;
    }

    .fitlog-heading {
        display: flex;
        align-items: center;
        gap: 12px;
        color: #E6F1E8;
        font-size: 27px;
        font-weight: 800;
    }

    .fitlog-subtitle {
        color: #B8C8BD;
        margin: 4px 0 15px 0;
    }

    @media (prefers-reduced-motion: reduce) {
        .fitlog-mascot { animation: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# DATA MANAGEMENT
# --------------------------------------------------

def clean_dataframe(df):
    """Standardize workout data columns and values."""
    if df is None or df.empty:
        return pd.DataFrame(
            columns=["date", "workout", "duration", "calories"]
        )

    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    aliases = {
        "workout_type": "workout",
        "activity": "workout",
        "exercise": "workout",
        "duration_minutes": "duration",
        "minutes": "duration",
        "calories_burned": "calories",
        "calorie": "calories",
        "burned_calories": "calories",
        "workout_date": "date",
    }
    df = df.rename(columns=aliases)

    required = ["date", "workout", "duration", "calories"]
    for col in required:
        if col not in df.columns:
            df[col] = None

    df = df[required]
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["workout"] = df["workout"].fillna("Other").astype(str).str.strip()
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
    df["calories"] = pd.to_numeric(df["calories"], errors="coerce")

    df = df.dropna(subset=["date", "duration", "calories"])
    df = df[df["workout"] != ""]
    df = df[(df["duration"] > 0) & (df["calories"] >= 0)]

    return df.reset_index(drop=True)


def load_workouts(user_id):
    """Load only the signed-in user's records from SQLite."""
    rows = list_user_workouts(user_id)
    return clean_dataframe(pd.DataFrame(rows))


def save_workout(user_id, workout_date, workout_name, duration, calories):
    """Save a workout under the current account."""
    save_user_workout(
        user_id,
        {
            "date": workout_date.isoformat(),
            "workout": workout_name,
            "duration": duration,
            "calories": calories,
        },
    )


def normalize_backup_records(records):
    if not isinstance(records, list):
        raise ValueError("Backup must contain a workouts list.")
    normalized = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each workout in the backup must be an object.")
        try:
            workout_date = date.fromisoformat(str(record["date"])).isoformat()
            workout_name = str(record["workout"]).strip()
            duration = int(record["duration"])
            calories = int(record["calories"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("A workout in the backup has invalid fields.") from exc
        if not workout_name or duration <= 0 or calories < 0:
            raise ValueError("A workout in the backup has invalid values.")
        normalized.append(
            {
                "date": workout_date,
                "workout": workout_name,
                "duration": duration,
                "calories": calories,
            }
        )
    return normalized


def get_anthropic_api_key():
    placeholder = "PASTE_NEW_KEY_HERE"
    try:
        secret_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        secret_key = str(secret_key).strip()
        if secret_key and secret_key != placeholder:
            return secret_key
    except Exception:
        pass

    environment_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    return "" if environment_key == placeholder else environment_key


def ask_anthropic(api_key, question, user_df):
    """Answer general questions and questions about this user's workout report."""
    activities = []
    recent_workouts = []
    if not user_df.empty:
        grouped = user_df.groupby("workout").agg(
            sessions=("workout", "size"),
            minutes=("duration", "sum"),
            calories=("calories", "sum"),
        )
        activities = [
            f"{name}: {int(row.sessions)} sessions, {int(row.minutes)} minutes, "
            f"{int(row.calories)} calories"
            for name, row in grouped.iterrows()
        ]
        recent = user_df.sort_values("date").tail(10)
        recent_workouts = [
            f"{row.date}: {row.workout}, {int(row.duration)} minutes, "
            f"{int(row.calories)} calories"
            for row in recent.itertuples(index=False)
        ]
        date_range = (
            f"{user_df['date'].min()} to {user_df['date'].max()}"
        )
    else:
        date_range = "no workouts recorded"

    summary = "\n".join(
        [
            f"Workout records: {len(user_df)}",
            f"Date range: {date_range}",
            f"Total workout minutes: {int(user_df['duration'].sum()) if not user_df.empty else 0}",
            f"Total recorded calories: {int(user_df['calories'].sum()) if not user_df.empty else 0}",
            "Breakdown by activity: " + ("; ".join(activities) if activities else "none yet"),
            "Most recent workout records: " + ("; ".join(recent_workouts) if recent_workouts else "none yet"),
        ]
    )
    prompt = (
        "The following is a summary of the signed-in user's FitLog report. "
        "Use it when relevant, and answer other general questions too.\n\n"
        f"FITLOG REPORT:\n{summary}\n\nQUESTION:\n{question}"
    )
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "system": (
            "You are a helpful general-purpose assistant in the FitLog app. "
            "Answer questions about the user's FitLog report using the supplied "
            "report summary, and answer questions on other topics with general "
            "knowledge. Do not claim to know personal report details that were not "
            "provided; say when the report does not contain enough information. "
            "Keep answers clear and practical. For health questions, provide "
            "general information only, do not diagnose or prescribe treatment, "
            "and advise contacting a qualified clinician when appropriate."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    endpoint = "https://api.anthropic.com/v1/messages"
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    retryable_statuses = {408, 429, 500, 502, 503, 504, 529}
    result = None
    for attempt in range(3):
        try:
            with request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
            break
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            if exc.code not in retryable_statuses or attempt == 2:
                raise RuntimeError(
                    f"Anthropic API returned HTTP {exc.code}: {details[:400]}"
                ) from exc
            exc.close()
        except (error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError(f"Could not reach Anthropic: {exc}") from exc
        time.sleep((2 ** attempt) + random.uniform(0, 0.5))

    try:
        answer_parts = [
            block["text"]
            for block in result.get("content", [])
            if block.get("type") == "text" and block.get("text")
        ]
        if answer_parts:
            return "\n".join(answer_parts)
    except (AttributeError, TypeError) as exc:
        raise RuntimeError("Anthropic returned an empty or unexpected response.") from exc
    raise RuntimeError("Anthropic returned no text response.")


# --------------------------------------------------
# ACCOUNT SIGN-IN / SIGN-UP
# --------------------------------------------------

init_db()

if "fitlog_user_id" not in st.session_state:
    st.markdown("## 🌿 Welcome to FitLog")
    st.caption("Sign in to see your private workout history, or create an account.")
    login_tab, signup_tab, recovery_tab = st.tabs(
        ["Log in", "Sign up", "Admin recovery"]
    )

    with login_tab:
        with st.form("fitlog_login_form"):
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input(
                "Password", type="password", key="login_password"
            )
            login_submitted = st.form_submit_button("Log in", use_container_width=True)
        if login_submitted:
            user = authenticate_user(login_username, login_password)
            if user:
                st.session_state["fitlog_user_id"] = user["id"]
                st.session_state["fitlog_username"] = user["username"]
                st.session_state["fitlog_user_role"] = user["role"]
                st.rerun()
            st.error("Username or password is incorrect.")

    with signup_tab:
        st.info(
            "Your password is stored as a secure hash. The first account becomes "
            "the administrator; later accounts are regular users. Existing workout "
            "records will belong to the first account created."
        )
        with st.form("fitlog_signup_form"):
            signup_username = st.text_input("Choose a username", key="signup_username")
            signup_password = st.text_input(
                "Choose a password (8+ characters)",
                type="password",
                key="signup_password",
            )
            confirm_password = st.text_input(
                "Confirm password", type="password", key="confirm_password"
            )
            signup_submitted = st.form_submit_button(
                "Create account", use_container_width=True
            )
        if signup_submitted:
            if signup_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                try:
                    user = create_user(
                        signup_username,
                        signup_password,
                        legacy_csv_file=CSV_FILE,
                    )
                    st.session_state["fitlog_user_id"] = user["id"]
                    st.session_state["fitlog_username"] = user["username"]
                    st.session_state["fitlog_user_role"] = user["role"]
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with recovery_tab:
        st.caption(
            "Reset the first administrator account with the recovery code configured "
            "in the app's private Secrets settings."
        )
        recovery_secret = ""
        try:
            recovery_secret = str(
                st.secrets.get("FITLOG_ADMIN_RECOVERY_CODE", "")
            ).strip()
        except Exception:
            # Secrets are optional for local runs; recovery stays unavailable without one.
            pass
        if len(recovery_secret) < 32:
            st.info(
                "Admin recovery is not configured. The app owner must add a strong "
                "FITLOG_ADMIN_RECOVERY_CODE in Streamlit Secrets."
            )
        else:
            with st.form("fitlog_admin_recovery_form"):
                recovery_code = st.text_input(
                    "Admin recovery code", type="password", key="admin_recovery_code"
                )
                recovery_password = st.text_input(
                    "New admin password (8+ characters)",
                    type="password",
                    key="admin_recovery_password",
                )
                recovery_password_confirm = st.text_input(
                    "Confirm new password",
                    type="password",
                    key="admin_recovery_password_confirm",
                )
                recovery_submitted = st.form_submit_button(
                    "Reset admin password", use_container_width=True
                )
            if recovery_submitted:
                if recovery_password != recovery_password_confirm:
                    st.error("The passwords do not match.")
                else:
                    try:
                        recovered_admin = reset_first_admin_password(
                            recovery_code,
                            recovery_password,
                            recovery_secret,
                        )
                        if recovered_admin:
                            st.success(
                                "Admin password reset. Sign in with the displayed "
                                "admin username and your new password."
                            )
                            st.info(
                                f"Admin username: {recovered_admin['username']}. "
                                "Rotate the recovery code in Streamlit Secrets now; "
                                "the current code remains usable until changed."
                            )
                        else:
                            st.error(
                                "Recovery failed. Check the recovery code and try again."
                            )
                    except ValueError as exc:
                        st.error(str(exc))
    st.stop()

current_user_id = st.session_state["fitlog_user_id"]
current_username = st.session_state["fitlog_username"]
current_user_role = get_user_role(current_user_id)
if current_user_role is None:
    st.session_state.clear()
    st.rerun()
df = load_workouts(current_user_id)
today = date.today()
if not df.empty:
    df["date"] = pd.to_datetime(df["date"]).dt.date

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🌿 FitLog")
    st.caption("Your personal fitness companion")
    st.caption(f"Signed in as **{current_username}** · {current_user_role.title()}")
    if st.button("Log out", use_container_width=True):
        st.session_state.pop("fitlog_user_id", None)
        st.session_state.pop("fitlog_username", None)
        st.session_state.pop("fitlog_user_role", None)
        st.rerun()
    st.divider()

    if current_user_role == "admin":
        with st.expander("🛡️ Admin Panel", expanded=False):
            try:
                admin_users = list_users_for_admin(current_user_id)
                st.caption(
                    "Manage account roles. This panel shows account details and "
                    "workout counts, not personal workout entries."
                )
                st.dataframe(
                    [
                        {
                            "Username": user["username"],
                            "Role": user["role"].title(),
                            "Joined": user["created_at"][:10],
                            "Workout count": user["workout_count"],
                        }
                        for user in admin_users
                    ],
                    hide_index=True,
                    use_container_width=True,
                )
                manageable_users = [
                    user for user in admin_users if user["id"] != current_user_id
                ]
                if manageable_users:
                    users_by_id = {user["id"]: user for user in manageable_users}
                    selected_user = st.selectbox(
                        "Choose an account",
                        list(users_by_id),
                        format_func=lambda user_id: (
                            f"{users_by_id[user_id]['username']} "
                            f"({users_by_id[user_id]['role']})"
                        ),
                        key=f"admin_target_{current_user_id}",
                    )
                    selected_user = users_by_id[selected_user]
                    new_role = st.selectbox(
                        "Set role",
                        ["user", "admin"],
                        index=0 if selected_user["role"] == "admin" else 1,
                        key=f"admin_new_role_{current_user_id}_{selected_user['id']}",
                    )
                    if st.button(
                        "Update account role",
                        key=f"admin_update_role_{current_user_id}",
                        use_container_width=True,
                    ):
                        try:
                            set_user_role(
                                current_user_id, selected_user["id"], new_role
                            )
                            st.success(
                                f"{selected_user['username']}'s role is now {new_role}."
                            )
                            st.rerun()
                        except (PermissionError, ValueError) as exc:
                            st.error(str(exc))
                else:
                    st.caption("There are no other accounts to manage yet.")
            except PermissionError:
                st.error("Administrator access is required.")

    st.markdown("### 🎯 Daily Goals")
    daily_minutes_goal = st.number_input(
        "Workout minutes",
        min_value=1,
        max_value=600,
        value=30,
        step=5,
        key=f"daily_minutes_goal_{current_user_id}",
    )
    daily_calories_goal = st.number_input(
        "Calories to burn",
        min_value=1,
        max_value=10000,
        value=300,
        step=50,
        key=f"daily_calories_goal_{current_user_id}",
    )
    daily_sessions_goal = st.number_input(
        "Workout sessions",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
        key=f"daily_sessions_goal_{current_user_id}",
    )

    st.divider()
    with st.expander("📄 My Data Report", expanded=False):
        if df.empty:
            st.caption("Log a workout to create your personal report.")
        else:
            personal_csv = df.sort_values("date", ascending=False).copy()
            personal_csv["date"] = personal_csv["date"].astype(str)
            safe_username = "".join(
                character
                for character in current_username
                if character.isalnum() or character in "-_"
            ) or "user"
            st.download_button(
                "Download my report (CSV)",
                data=personal_csv.to_csv(index=False).encode("utf-8"),
                file_name=f"fitlog_{safe_username}_report_{today.isoformat()}.csv",
                mime="text/csv",
                key=f"sidebar_report_{current_user_id}",
                use_container_width=True,
            )

    with st.expander("💾 Backup & SQLite", expanded=False):
        st.caption("Backups contain only the signed-in account's workouts.")
        backup_records = [
            {
                "date": str(row.date),
                "workout": str(row.workout),
                "duration": int(row.duration),
                "calories": int(row.calories),
            }
            for row in df.itertuples(index=False)
        ]
        safe_username = "".join(
            character
            for character in current_username
            if character.isalnum() or character in "-_"
        ) or "user"
        backup_snapshot = {
            "format": "fitlog-backup-v1",
            "username": current_username,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "workouts": backup_records,
        }
        st.download_button(
            "Export full JSON snapshot",
            data=json.dumps(backup_snapshot, indent=2).encode("utf-8"),
            file_name=f"fitlog_{safe_username}_backup_{today.isoformat()}.json",
            mime="application/json",
            key=f"json_backup_{current_user_id}",
            use_container_width=True,
        )

        sql_lines = [
            "-- FitLog workout backup; only this account's workout records.",
            "CREATE TABLE IF NOT EXISTS fitlog_backup (",
            "    date TEXT NOT NULL,",
            "    workout TEXT NOT NULL,",
            "    duration INTEGER NOT NULL,",
            "    calories INTEGER NOT NULL",
            ");",
        ]
        for record in backup_records:
            quoted_workout = record["workout"].replace("'", "''")
            sql_lines.append(
                "INSERT INTO fitlog_backup (date, workout, duration, calories) "
                f"VALUES ('{record['date']}', '{quoted_workout}', "
                f"{record['duration']}, {record['calories']});"
            )
        st.download_button(
            "Export SQLite SQL dump",
            data="\n".join(sql_lines).encode("utf-8"),
            file_name=f"fitlog_{safe_username}_backup_{today.isoformat()}.sql",
            mime="application/sql",
            key=f"sql_backup_{current_user_id}",
            use_container_width=True,
        )

        uploaded_backup = st.file_uploader(
            "Restore workouts from a FitLog JSON snapshot",
            type=["json"],
            key=f"restore_backup_{current_user_id}",
        )
        if st.button(
            "Restore JSON backup to my account",
            disabled=uploaded_backup is None,
            key=f"restore_backup_button_{current_user_id}",
            use_container_width=True,
        ):
            try:
                snapshot = json.loads(uploaded_backup.getvalue().decode("utf-8"))
                if not isinstance(snapshot, dict) or snapshot.get("format") != "fitlog-backup-v1":
                    raise ValueError("Choose a FitLog JSON snapshot.")
                restore_records = normalize_backup_records(snapshot.get("workouts"))
                existing_rows = list_user_workouts(current_user_id)
                existing_keys = {
                    (
                        str(row["date"]),
                        str(row["workout"]),
                        int(row["duration"]),
                        int(row["calories"]),
                    )
                    for row in existing_rows
                }
                restored = 0
                for record in restore_records:
                    record_key = (
                        record["date"],
                        record["workout"],
                        record["duration"],
                        record["calories"],
                    )
                    if record_key not in existing_keys:
                        save_user_workout(current_user_id, record)
                        existing_keys.add(record_key)
                        restored += 1
                st.success(
                    f"Restored {restored} workout(s). Existing matching records were skipped."
                )
                st.rerun()
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                st.error(f"Could not restore that backup: {exc}")

    with st.expander("✨ Claude AI Coach", expanded=False):
        anthropic_key = get_anthropic_api_key()
        if not anthropic_key:
            st.caption(
                "Create an Anthropic API key in the Anthropic Console. It stays in this "
                "browser session and is not saved to your project files."
            )
            anthropic_key = st.text_input(
                "Anthropic API key",
                type="password",
                key=f"anthropic_session_key_{current_user_id}",
                help="Paste your key here. It is kept only for this active app session.",
            )
        if anthropic_key:
            st.caption(
                "Your question and a summary of your workouts are sent to Anthropic Claude. "
                "You can ask about your report or other general topics."
            )
            question = st.text_area(
                "Ask about your report or any other question",
                key=f"anthropic_question_{current_user_id}",
                placeholder="Example: Summarize my report, or ask a general question...",
            )
            if st.button(
                "Ask Claude",
                key=f"ask_anthropic_{current_user_id}",
                use_container_width=True,
            ):
                if not question.strip():
                    st.warning("Enter a question first.")
                else:
                    with st.spinner("Claude is preparing a suggestion..."):
                        try:
                            st.session_state[
                                f"anthropic_answer_{current_user_id}"
                            ] = ask_anthropic(anthropic_key, question.strip(), df)
                        except RuntimeError as exc:
                            st.error(str(exc))
            answer = st.session_state.get(f"anthropic_answer_{current_user_id}")
            if answer:
                st.markdown(answer)

    with st.expander("❓ FitLog FAQ", expanded=False):
        st.markdown("**How do I record a workout?**")
        st.caption("Use Log a Workout on the dashboard, fill in the details, then select Save Workout.")

        st.markdown("**How do I download my own report?**")
        st.caption("Open My Data Report in the sidebar and select Download my report (CSV).")

        st.markdown("**How do I back up or restore my workouts?**")
        st.caption(
            "Open Backup & SQLite. Download a JSON snapshot or SQL dump, or choose "
            "a FitLog JSON snapshot and restore it to your signed-in account."
        )

        st.markdown("**Where do I change my daily goals?**")
        st.caption("Use the Daily Goals controls in the sidebar. The dashboard updates your progress from your workouts.")

        st.markdown("**Why can’t I see another account’s workouts?**")
        st.caption("FitLog keeps each account’s workout history separate. Sign in with the account that recorded those workouts.")

        st.markdown("**What if Claude shows a 429 or 529 error?**")
        st.caption("Wait briefly and try again. These errors can mean a rate limit or temporary service load. The FAQ works without an Anthropic key.")

        st.markdown("**How do I view the project tests?**")
        st.caption(
            "The tests are in the tests folder. GitHub Actions runs them after "
            "you push a commit; open the repository's Actions tab to see the result."
        )

    st.divider()
    st.markdown("### 💡 Quick Tips")
    st.info(
        "Consistency matters more than perfection. "
        "Start small, track progress, and keep moving."
    )

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

today_df = df[df["date"] == today] if not df.empty else df.copy()

today_minutes = int(today_df["duration"].sum()) if not today_df.empty else 0
today_calories = int(today_df["calories"].sum()) if not today_df.empty else 0
today_sessions = len(today_df)

total_workouts = len(df)
total_minutes = int(df["duration"].sum()) if not df.empty else 0
total_calories = int(df["calories"].sum()) if not df.empty else 0

# --------------------------------------------------
# HERO HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🌿 FitLog Smart Fitness Dashboard</div>
        <div class="hero-subtitle">
            Track workouts. Build consistency. Celebrate every improvement.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# TOP METRICS
# --------------------------------------------------

st.markdown("### ✨ Your Fitness at a Glance")

m1, m2, m3, m4 = st.columns(4)

m1.metric("🏋️ Total Workouts", f"{total_workouts:,}")
m2.metric("⏱️ Total Minutes", f"{total_minutes:,}")
m3.metric("🔥 Total Calories", f"{total_calories:,}")
m4.metric("📅 Today's Sessions", f"{today_sessions:,}")

st.write("")

# --------------------------------------------------
# DAILY GOAL PROGRESS
# --------------------------------------------------

st.markdown("### 🎯 Today's Goal Progress")

g1, g2, g3 = st.columns(3)

with g1:
    st.markdown("**⏱️ Workout Minutes**")
    minutes_progress = min(today_minutes / daily_minutes_goal, 1.0)
    st.progress(minutes_progress)
    st.caption(
        f"{today_minutes} / {daily_minutes_goal} minutes"
        + (" · Goal reached! 🎉" if today_minutes >= daily_minutes_goal else "")
    )

with g2:
    st.markdown("**🔥 Calories Burned**")
    calories_progress = min(today_calories / daily_calories_goal, 1.0)
    st.progress(calories_progress)
    st.caption(
        f"{today_calories} / {daily_calories_goal} calories"
        + (" · Goal reached! 🎉" if today_calories >= daily_calories_goal else "")
    )

with g3:
    st.markdown("**🏆 Workout Sessions**")
    sessions_progress = min(today_sessions / daily_sessions_goal, 1.0)
    st.progress(sessions_progress)
    st.caption(
        f"{today_sessions} / {daily_sessions_goal} sessions"
        + (" · Goal reached! 🎉" if today_sessions >= daily_sessions_goal else "")
    )

if (
    today_minutes >= daily_minutes_goal
    and today_calories >= daily_calories_goal
    and today_sessions >= daily_sessions_goal
):
    st.success("Amazing! You have achieved all your daily goals. Keep it up! 🌟")

st.divider()

# --------------------------------------------------
# WORKOUT ENTRY FORM
# --------------------------------------------------

st.markdown(
    """
    <div class="fitlog-heading">
        <span class="fitlog-mascot">🏃</span>
        <span>Log a Workout</span>
        <span>🌿</span>
    </div>
    <div class="fitlog-subtitle">
        Every workout counts. Record your activity and keep moving towards your goals!
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("workout_entry_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        workout_date = st.date_input(
            "📅 Workout date",
            value=today,
            max_value=today,
        )

        workout = st.selectbox(
            "🏃 Workout type",
            WORKOUT_TYPES,
            format_func=lambda x: f"{WORKOUT_ICONS[x]}  {x}",
        )

        custom = st.text_input(
            "✨ Custom workout (optional)",
            placeholder="Example: Badminton, dancing, hiking",
        )

    with col2:
        duration = st.number_input(
            "⏱️ Duration (minutes)",
            min_value=1,
            max_value=1440,
            value=30,
            step=5,
        )

        calories = st.number_input(
            "🔥 Calories burned",
            min_value=0,
            max_value=20000,
            value=200,
            step=10,
        )

        st.markdown(
            "<div class='small-muted'>"
            "Tip: Enter a realistic duration and calorie estimate."
            "</div>",
            unsafe_allow_html=True,
        )

    selected_name = custom.strip() if custom.strip() else workout
    st.caption(
        f"{WORKOUT_ICONS.get(workout, '⚡')} Selected activity: {selected_name}"
    )

    submitted = st.form_submit_button(
        "➕ Save Workout",
        use_container_width=True,
    )

    if submitted:
        if workout_date > today:
            st.error("Please select today or a past date.")
        elif not selected_name:
            st.error("Please select or enter a workout type.")
        elif duration <= 0:
            st.error("Duration must be greater than zero.")
        else:
            try:
                save_workout(
                    current_user_id,
                    workout_date,
                    selected_name,
                    duration,
                    calories,
                )
                st.success(
                    f"Workout saved! {WORKOUT_ICONS.get(workout, '✨')} "
                    f"{selected_name} · {duration} minutes · {calories} calories"
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save the workout: {exc}")

st.divider()

# --------------------------------------------------
# INSIGHTS
# --------------------------------------------------

st.markdown("### 🧠 Your Fitness Insights")

i1, i2, i3 = st.columns(3)

with i1:
    if not df.empty:
        average_duration = df["duration"].mean()
        st.markdown(
            f"""
            <div class="soft-card">
                <div style="font-size:25px;">⏳</div>
                <div style="color:{MUTED};font-size:13px;">Average workout</div>
                <div style="font-size:27px;font-weight:800;color:{MINT};">
                    {average_duration:.1f} min
                </div>
                <div class="small-muted">Average duration per recorded session</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Log a workout to see your average duration.")

with i2:
    if not df.empty:
        best_workout = (
            df.groupby("workout")["duration"].sum().sort_values(ascending=False)
        )
        best_name = best_workout.index[0]
        st.markdown(
            f"""
            <div class="soft-card">
                <div style="font-size:25px;">🏅</div>
                <div style="color:{MUTED};font-size:13px;">Most practiced activity</div>
                <div style="font-size:23px;font-weight:800;color:{LAVENDER};">
                    {best_name}
                </div>
                <div class="small-muted">
                    {int(best_workout.iloc[0])} total minutes
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Your most practiced activity will appear here.")

with i3:
    if not df.empty:
        active_days = df["date"].nunique()
        st.markdown(
            f"""
            <div class="soft-card">
                <div style="font-size:25px;">🌱</div>
                <div style="color:{MUTED};font-size:13px;">Active days</div>
                <div style="font-size:27px;font-weight:800;color:{BLUE};">
                    {active_days}
                </div>
                <div class="small-muted">Different days with recorded workouts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Your active-day count will appear here.")

# --------------------------------------------------
# CHARTS
# --------------------------------------------------

st.divider()
st.markdown("### 📊 Workout Analytics")

if df.empty:
    st.info("No workout data yet. Add your first workout above to unlock analytics.")
else:
    chart1, chart2 = st.columns(2)

    with chart1:
        daily = (
            df.groupby("date", as_index=False)
            .agg(duration=("duration", "sum"))
            .sort_values("date")
        )
        daily["date_label"] = daily["date"].astype(str)

        fig_duration = px.bar(
            daily,
            x="date_label",
            y="duration",
            title="⏱️ Workout Minutes by Day",
            labels={"date_label": "Date", "duration": "Minutes"},
            color="duration",
            color_continuous_scale=["#26352D", MINT, BLUE, LAVENDER],
        )
        fig_duration.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=TEXT,
            title_font_color=MINT,
            coloraxis_showscale=False,
            margin=dict(l=15, r=15, t=55, b=15),
        )
        fig_duration.update_xaxes(showgrid=False)
        fig_duration.update_yaxes(gridcolor="#34483A")
        st.plotly_chart(fig_duration, use_container_width=True)

    with chart2:
        activity = (
            df.groupby("workout", as_index=False)
            .agg(calories=("calories", "sum"))
            .sort_values("calories", ascending=True)
        )

        fig_activity = px.bar(
            activity,
            x="calories",
            y="workout",
            orientation="h",
            title="🔥 Calories by Activity",
            labels={"workout": "Activity", "calories": "Calories"},
            color="workout",
            color_discrete_sequence=[
                MINT, LAVENDER, BLUE, PEACH, "#E8B9CF", "#D8E8A9"
            ],
        )
        fig_activity.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=TEXT,
            title_font_color=LAVENDER,
            showlegend=False,
            margin=dict(l=15, r=15, t=55, b=15),
        )
        fig_activity.update_xaxes(gridcolor="#34483A")
        fig_activity.update_yaxes(showgrid=False)
        st.plotly_chart(fig_activity, use_container_width=True)

    # Weekly trend
    st.markdown("#### 🌤️ Last 7 Days")

    end_day = today
    start_day = today - timedelta(days=6)
    days = pd.date_range(start=start_day, end=end_day, freq="D")

    last_week = df[
        (df["date"] >= start_day) & (df["date"] <= end_day)
    ].copy()

    weekly = (
        last_week.groupby("date")["duration"].sum()
        if not last_week.empty
        else pd.Series(dtype=float)
    )

    week_values = [
        int(weekly.get(day.date(), 0))
        for day in days
    ]

    fig_week = go.Figure()
    fig_week.add_trace(
        go.Bar(
            x=[day.strftime("%a\n%d %b") for day in days],
            y=week_values,
            marker=dict(
                color=week_values,
                colorscale=[
                    [0, "#26352D"],
                    [0.35, MINT],
                    [0.7, BLUE],
                    [1, LAVENDER],
                ],
                line=dict(color="#34483A", width=1),
            ),
            text=week_values,
            textposition="outside",
            texttemplate="%{text} min",
            hovertemplate="%{x}<br>%{y} minutes<extra></extra>",
        )
    )
    fig_week.update_layout(
        title="Your Daily Workout Minutes",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT,
        title_font_color=MINT,
        yaxis_title="Minutes",
        xaxis_title="Day",
        showlegend=False,
        margin=dict(l=15, r=15, t=55, b=15),
    )
    fig_week.update_yaxes(gridcolor="#34483A", rangemode="tozero")
    fig_week.update_xaxes(showgrid=False)
    st.plotly_chart(fig_week, use_container_width=True)

    # Activity calendar-style view
    st.markdown("#### 🗓️ Activity Calendar")

    calendar_days = pd.date_range(
        end=today,
        periods=35,
        freq="D",
    )

    calendar_data = pd.DataFrame({"date": calendar_days.date})
    calendar_totals = (
        df.groupby("date", as_index=False)
        .agg(minutes=("duration", "sum"))
    )
    calendar_data = calendar_data.merge(
        calendar_totals,
        on="date",
        how="left",
    )
    calendar_data["minutes"] = calendar_data["minutes"].fillna(0)
    calendar_data["day_name"] = pd.to_datetime(
        calendar_data["date"]
    ).dt.strftime("%a")
    calendar_data["week"] = list(range(35))
    calendar_data["day_label"] = pd.to_datetime(
        calendar_data["date"]
    ).dt.strftime("%d %b")

    calendar_data["week_col"] = [
        i // 7 for i in range(len(calendar_data))
    ]
    calendar_data["weekday"] = pd.to_datetime(
        calendar_data["date"]
    ).dt.dayofweek

    # Create a readable calendar grid with weekday labels.
    calendar_matrix = calendar_data.pivot(
        index="weekday",
        columns="week_col",
        values="minutes",
    ).reindex(index=range(7), columns=range(5))

    fig_calendar = go.Figure(
        data=go.Heatmap(
            z=calendar_matrix.values,
            x=["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
            y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            colorscale=[
                [0.0, "#26352D"],
                [0.25, "#C7E9D5"],
                [0.50, "#9EDBC0"],
                [0.75, "#B8D2FF"],
                [1.0, "#D8C4FF"],
            ],
            xgap=5,
            ygap=5,
            colorbar=dict(title="Minutes"),
            hovertemplate="%{y}, %{x}<br>Workout: %{z} minutes<extra></extra>",
        )
    )
    fig_calendar.update_layout(
        title="Recent Activity · Brighter colors mean more workout minutes",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT,
        title_font_color=BLUE,
        margin=dict(l=15, r=15, t=55, b=15),
        height=320,
    )
    fig_calendar.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_calendar, use_container_width=True)

# --------------------------------------------------
# WORKOUT HISTORY AND EXPORT
# --------------------------------------------------

st.divider()
st.markdown("### 📚 Workout History")

if df.empty:
    st.info("Your workout history will appear here after you save a workout.")
else:
    filter1, filter2 = st.columns(2)

    with filter1:
        activity_options = ["All activities"] + sorted(
            df["workout"].dropna().unique().tolist()
        )
        selected_activity = st.selectbox(
            "Filter by activity",
            activity_options,
        )

    with filter2:
        date_filter = st.selectbox(
            "Date range",
            ["All time", "Last 7 days", "Last 30 days"],
        )

    history = df.copy()

    if selected_activity != "All activities":
        history = history[history["workout"] == selected_activity]

    if date_filter == "Last 7 days":
        history = history[
            history["date"] >= today - timedelta(days=6)
        ]
    elif date_filter == "Last 30 days":
        history = history[
            history["date"] >= today - timedelta(days=29)
        ]

    history = history.sort_values("date", ascending=False).copy()

    history["date"] = history["date"].astype(str)
    history["activity"] = history["workout"].apply(
        lambda x: f"{WORKOUT_ICONS.get(x, '✨')} {x}"
    )
    history = history.rename(
        columns={
            "date": "Date",
            "activity": "Workout",
            "duration": "Duration (min)",
            "calories": "Calories",
        }
    )
    history = history[["Date", "Workout", "Duration (min)", "Calories"]]

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True,
    )

    export_df = history.copy()
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Workout History (CSV)",
        data=csv_bytes,
        file_name=f"fitlog_history_{today.isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    """
    <div style="
        text-align:center;
        padding:24px 10px 10px 10px;
        color:#B8C8BD;
        font-size:13px;
    ">
        🌿 <b style="color:#A9E8C0;">FitLog</b> · Small steps, stronger habits.
        <br>Keep showing up for yourself. 💚
    </div>
    """,
    unsafe_allow_html=True,
)
