
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

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
DB_FILE = BASE_DIR / "fitlog.db"

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


def load_workouts():
    """Read workout history from CSV and SQLite, if available."""
    frames = []

    if CSV_FILE.exists():
        try:
            frames.append(clean_dataframe(pd.read_csv(CSV_FILE)))
        except Exception as exc:
            st.warning(f"Could not read workouts.csv: {exc}")

    if DB_FILE.exists():
        try:
            with sqlite3.connect(DB_FILE) as conn:
                tables = pd.read_sql_query(
                    "SELECT name FROM sqlite_master WHERE type='table'",
                    conn,
                )["name"].tolist()

                if "workouts" in tables:
                    db_df = pd.read_sql_query(
                        "SELECT * FROM workouts", conn
                    )
                    frames.append(clean_dataframe(db_df))
        except Exception as exc:
            st.warning(f"Could not read fitlog.db: {exc}")

    if not frames:
        return pd.DataFrame(
            columns=["date", "workout", "duration", "calories"]
        )

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["date", "workout", "duration", "calories"]
    )
    return combined.sort_values("date", ascending=False).reset_index(drop=True)


def save_workout(workout_date, workout_name, duration, calories):
    """Save one workout to CSV and SQLite."""
    record = {
        "date": workout_date.isoformat(),
        "workout": workout_name,
        "duration": int(duration),
        "calories": int(calories),
    }

    # Save to CSV.
    if CSV_FILE.exists():
        try:
            old_csv = pd.read_csv(CSV_FILE)
            old_csv = old_csv.rename(
                columns={
                    "workout_type": "workout",
                    "activity": "workout",
                    "duration_minutes": "duration",
                    "calories_burned": "calories",
                    "workout_date": "date",
                }
            )
            for col in ["date", "workout", "duration", "calories"]:
                if col not in old_csv.columns:
                    old_csv[col] = None
            old_csv = old_csv[["date", "workout", "duration", "calories"]]
        except Exception:
            old_csv = pd.DataFrame(
                columns=["date", "workout", "duration", "calories"]
            )
    else:
        old_csv = pd.DataFrame(
            columns=["date", "workout", "duration", "calories"]
        )

    new_csv = pd.concat([old_csv, pd.DataFrame([record])], ignore_index=True)
    new_csv.to_csv(CSV_FILE, index=False)

    # Save to SQLite. Preserve any existing workouts table.
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                workout TEXT NOT NULL,
                duration INTEGER NOT NULL,
                calories INTEGER NOT NULL
            )
            """
        )

        columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(workouts)").fetchall()
        ]

        if all(col in columns for col in ["date", "workout", "duration", "calories"]):
            conn.execute(
                """
                INSERT INTO workouts (date, workout, duration, calories)
                VALUES (?, ?, ?, ?)
                """,
                (
                    record["date"],
                    record["workout"],
                    record["duration"],
                    record["calories"],
                ),
            )
        else:
            raise ValueError(
                "Your existing workouts table has a different structure. "
                "The CSV was saved, but the SQLite record could not be added."
            )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🌿 FitLog")
    st.caption("Your personal fitness companion")
    st.divider()

    st.markdown("### 🎯 Daily Goals")
    daily_minutes_goal = st.number_input(
        "Workout minutes",
        min_value=1,
        max_value=600,
        value=30,
        step=5,
        key="daily_minutes_goal",
    )
    daily_calories_goal = st.number_input(
        "Calories to burn",
        min_value=1,
        max_value=10000,
        value=300,
        step=50,
        key="daily_calories_goal",
    )
    daily_sessions_goal = st.number_input(
        "Workout sessions",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
        key="daily_sessions_goal",
    )

    st.divider()
    st.markdown("### 💡 Quick Tips")
    st.info(
        "Consistency matters more than perfection. "
        "Start small, track progress, and keep moving."
    )

    st.caption("Data files")
    st.code("workouts.csv\nfitlog.db", language="text")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = load_workouts()
today = date.today()

if not df.empty:
    df["date"] = pd.to_datetime(df["date"]).dt.date

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
