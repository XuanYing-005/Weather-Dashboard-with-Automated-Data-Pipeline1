"""
Taiwan Weather Dashboard — Streamlit frontend
Reads live data from Supabase PostgreSQL populated by etl.py.
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Taiwan Weather Dashboard",
    page_icon="⛅",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Database connection
# Uses st.secrets on Streamlit Cloud; falls back to env var for local dev.
# ---------------------------------------------------------------------------
def get_database_url() -> str:
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        url = os.environ.get("DATABASE_URL")
        if not url:
            st.error(
                "DATABASE_URL not configured. "
                "Add it to .streamlit/secrets.toml or set the environment variable."
            )
            st.stop()
        return url


@st.cache_resource
def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)


@st.cache_data(ttl=300)  # Re-query every 5 minutes
def load_data() -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT id, fetched_at, forecast_date, city,
               temperature, rain_probability, comfort_index, outfit_tip
        FROM weather_forecasts
        ORDER BY fetched_at DESC, forecast_date ASC
    """
    df = pd.read_sql(query, engine)
    df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data from database: {e}")
    st.stop()

if df.empty:
    st.warning("No data in the database yet. Run `python etl.py` first.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar — filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⛅ Filters")
    cities = sorted(df["city"].unique().tolist())
    selected_city = st.selectbox("Select City", cities)

    st.markdown("---")
    st.caption(
        "Data refreshes automatically every 3 hours via GitHub Actions. "
        "The dashboard cache updates every 5 minutes."
    )

# ---------------------------------------------------------------------------
# Filter to selected city; latest fetch batch only for current conditions
# ---------------------------------------------------------------------------
city_df = df[df["city"] == selected_city].copy()
latest_fetched_at = city_df["fetched_at"].max()
latest_batch = city_df[city_df["fetched_at"] == latest_fetched_at]
nearest_forecast = latest_batch.sort_values("forecast_date").iloc[0]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title(f"⛅ Taiwan Weather Dashboard — {selected_city}")

last_updated_local = latest_fetched_at.strftime("%Y-%m-%d %H:%M UTC")
st.info(f"🔄 **Last pipeline run:** {last_updated_local}  |  Auto-refresh: every 3 hours via GitHub Actions")

st.markdown("---")

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="🌡️ Temperature",
    value=f"{nearest_forecast['temperature']:.1f} °C",
)
col2.metric(
    label="☔ Rain Probability",
    value=f"{nearest_forecast['rain_probability']} %",
)
col3.metric(
    label="😊 Comfort Index",
    value=nearest_forecast["comfort_index"],
)
col4.metric(
    label="📅 Forecast Date",
    value=nearest_forecast["forecast_date"].strftime("%Y-%m-%d"),
)

st.markdown(f"### 👕 Outfit Tip: *{nearest_forecast['outfit_tip']}*")
st.markdown("---")

# ---------------------------------------------------------------------------
# Temperature trend chart (latest fetch per forecast_date)
# ---------------------------------------------------------------------------
st.subheader("🌡️ Temperature Forecast Trend")

# For each unique forecast_date, take the row from the most recent fetch
trend_df = (
    city_df.sort_values("fetched_at", ascending=False)
    .drop_duplicates(subset=["forecast_date"])
    .sort_values("forecast_date")
    .reset_index(drop=True)
)

fig_temp = px.line(
    trend_df,
    x="forecast_date",
    y="temperature",
    markers=True,
    labels={"forecast_date": "Date", "temperature": "Temperature (°C)"},
    title=f"Temperature Trend — {selected_city}",
    color_discrete_sequence=["#FF6B35"],
)
fig_temp.update_traces(marker_size=8, line_width=2)
fig_temp.update_layout(hovermode="x unified", height=380)
st.plotly_chart(fig_temp, use_container_width=True)

# ---------------------------------------------------------------------------
# Rain probability bar chart
# ---------------------------------------------------------------------------
st.subheader("☔ Rain Probability Forecast")

fig_rain = px.bar(
    trend_df,
    x="forecast_date",
    y="rain_probability",
    labels={"forecast_date": "Date", "rain_probability": "Rain Probability (%)"},
    title=f"Rain Probability — {selected_city}",
    color="rain_probability",
    color_continuous_scale=["#90CAF9", "#1565C0"],
    range_y=[0, 100],
)
fig_rain.update_layout(height=320, coloraxis_showscale=False)
st.plotly_chart(fig_rain, use_container_width=True)

# ---------------------------------------------------------------------------
# Raw data table
# ---------------------------------------------------------------------------
st.subheader("📊 Raw Data (Latest Pipeline Batch)")

display_df = latest_batch[
    ["forecast_date", "city", "temperature", "rain_probability", "comfort_index", "outfit_tip", "fetched_at"]
].rename(
    columns={
        "forecast_date": "Forecast Date",
        "city": "City",
        "temperature": "Temp (°C)",
        "rain_probability": "Rain Prob (%)",
        "comfort_index": "Comfort Index",
        "outfit_tip": "Outfit Tip",
        "fetched_at": "Fetched At (UTC)",
    }
).sort_values("Forecast Date")

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.caption(
    "This table shows the most recently fetched batch from the automated pipeline. "
    "Data is sourced from the Taiwan Central Weather Administration (CWA) Open Data API."
)
