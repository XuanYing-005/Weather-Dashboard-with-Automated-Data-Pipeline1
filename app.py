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
    page_title="台灣天氣儀表板",
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
    st.warning("資料庫尚無資料，請先執行 `python etl.py`。")
    st.stop()

CITY_DISPLAY = {"Taipei": "台北市", "Taichung": "台中市", "Kaohsiung": "高雄市"}

# ---------------------------------------------------------------------------
# Sidebar — filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⛅ 篩選條件")
    cities = sorted(df["city"].unique().tolist())
    selected_city = st.selectbox(
        "選擇城市",
        cities,
        format_func=lambda x: CITY_DISPLAY.get(x, x),
    )

    st.markdown("---")
    st.caption(
        "資料每 3 小時透過 GitHub Actions 自動更新，"
        "儀表板快取每 5 分鐘刷新一次。"
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
st.title(f"⛅ 台灣天氣儀表板 — {CITY_DISPLAY.get(selected_city, selected_city)}")

last_updated_local = latest_fetched_at.strftime("%Y-%m-%d %H:%M UTC")
st.info(f"🔄 **最後更新時間：** {last_updated_local}  |  自動更新：每 3 小時透過 GitHub Actions 執行")

st.markdown("---")

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="🌡️ 氣溫",
    value=f"{nearest_forecast['temperature']:.1f} °C",
)
col2.metric(
    label="☔ 降雨機率",
    value=f"{nearest_forecast['rain_probability']} %",
)
col3.metric(
    label="😊 舒適度",
    value=nearest_forecast["comfort_index"],
)
col4.metric(
    label="📅 預報日期",
    value=nearest_forecast["forecast_date"].strftime("%Y-%m-%d"),
)

st.markdown(f"### 👕 穿搭建議：*{nearest_forecast['outfit_tip']}*")
st.markdown("---")

# ---------------------------------------------------------------------------
# Temperature trend chart (latest fetch per forecast_date)
# ---------------------------------------------------------------------------
st.subheader("🌡️ 氣溫預報趨勢")

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
    labels={"forecast_date": "日期", "temperature": "氣溫 (°C)"},
    title=f"氣溫趨勢 — {CITY_DISPLAY.get(selected_city, selected_city)}",
    color_discrete_sequence=["#FF6B35"],
)
fig_temp.update_traces(marker_size=8, line_width=2)
fig_temp.update_layout(hovermode="x unified", height=380)
st.plotly_chart(fig_temp, use_container_width=True)

# ---------------------------------------------------------------------------
# Rain probability bar chart
# ---------------------------------------------------------------------------
st.subheader("☔ 降雨機率預報")

fig_rain = px.bar(
    trend_df,
    x="forecast_date",
    y="rain_probability",
    labels={"forecast_date": "日期", "rain_probability": "降雨機率 (%)"},
    title=f"降雨機率 — {CITY_DISPLAY.get(selected_city, selected_city)}",
    color="rain_probability",
    color_continuous_scale=["#90CAF9", "#1565C0"],
    range_y=[0, 100],
)
fig_rain.update_layout(height=320, coloraxis_showscale=False)
st.plotly_chart(fig_rain, use_container_width=True)

# ---------------------------------------------------------------------------
# Raw data table
# ---------------------------------------------------------------------------
st.subheader("📊 原始資料（最新一批次）")

display_df = latest_batch[
    ["forecast_date", "city", "temperature", "rain_probability", "comfort_index", "outfit_tip", "fetched_at"]
].rename(
    columns={
        "forecast_date": "預報日期",
        "city": "城市",
        "temperature": "氣溫 (°C)",
        "rain_probability": "降雨機率 (%)",
        "comfort_index": "舒適度",
        "outfit_tip": "穿搭建議",
        "fetched_at": "擷取時間 (UTC)",
    }
).sort_values("預報日期")

display_df["城市"] = display_df["城市"].map(lambda x: CITY_DISPLAY.get(x, x))

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.caption(
    "此表格顯示自動化 pipeline 最新一批次的擷取資料，"
    "資料來源為中央氣象署（CWA）開放資料平台。"
)
