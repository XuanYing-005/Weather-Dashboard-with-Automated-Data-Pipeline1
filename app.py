"""
Taiwan Weather Dashboard — Streamlit frontend
Reads live data from Supabase PostgreSQL populated by etl.py.
"""
import os
import random
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

st.set_page_config(
    page_title="台灣天氣通",
    page_icon="🌤️",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');

html, body, [class*="css"], * {
    font-family: 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
}

#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; }

.hero {
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 55%, #6c5ce7 100%);
    border-radius: 24px;
    padding: 2rem 2.5rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(9,132,227,0.25);
}
.hero h1 { font-size: 2rem; font-weight: 900; margin: 0 0 0.3rem; letter-spacing: 0.04em; }
.hero p  { margin: 0; opacity: 0.88; font-size: 0.88rem; }

.weather-emoji { font-size: 4rem; line-height: 1; }

.outfit-card {
    background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
    border-radius: 18px;
    padding: 1rem 1.6rem;
    color: white;
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0.6rem 0 1rem;
    box-shadow: 0 4px 16px rgba(225,112,85,0.28);
}

.fun-card {
    background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
    border-radius: 18px;
    padding: 0.9rem 1.6rem;
    color: white;
    font-size: 0.95rem;
    margin: 0.5rem 0 1.2rem;
    box-shadow: 0 4px 16px rgba(108,92,231,0.22);
}

.section-bar {
    font-size: 1.1rem;
    font-weight: 700;
    color: #2d3436;
    margin: 1.4rem 0 0.6rem;
    padding-left: 0.75rem;
    border-left: 4px solid #0984e3;
}

[data-testid="metric-container"] {
    background: #ffffff;
    border-radius: 16px;
    padding: 1rem 1.2rem !important;
    box-shadow: 0 2px 14px rgba(0,0,0,0.07);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f0f4ff 0%, #e8eeff 100%);
}
</style>
""", unsafe_allow_html=True)

# ── DB ───────────────────────────────────────────────────────────────────────
def get_database_url() -> str:
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        url = os.environ.get("DATABASE_URL")
        if not url:
            st.error("DATABASE_URL 未設定，請新增至 .streamlit/secrets.toml 或環境變數。")
            st.stop()
        return url

@st.cache_resource
def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)

@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT id, fetched_at, forecast_date, city,
               temperature, rain_probability, comfort_index, outfit_tip
        FROM weather_forecasts
        ORDER BY fetched_at DESC, forecast_date ASC
    """
    df = pd.read_sql(query, engine)
    df["fetched_at"]    = pd.to_datetime(df["fetched_at"], utc=True)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"資料庫連線失敗：{e}")
    st.stop()

if df.empty:
    st.warning("資料庫尚無資料，請先執行 ETL。")
    st.stop()

# ── Constants ────────────────────────────────────────────────────────────────
CITY_DISPLAY = {"Taipei": "台北市", "Taichung": "台中市", "Kaohsiung": "高雄市"}
CITY_EMOJI   = {"Taipei": "🏙️",    "Taichung": "🌳",      "Kaohsiung": "🌊"}

FUN_TIPS = [
    "☀️ 出門前抬頭看天空，比看手機更準！",
    "💧 天氣熱的時候記得多喝水，每天至少 2000ml！",
    "🌿 台灣的天氣變化快，包包裡放把折疊傘最保險～",
    "🧴 紫外線強的時候，防曬乳是你最好的朋友！",
    "🍵 下雨天最適合喝一杯熱飲，讓心情變好 ☕",
    "🎒 今天的天氣資料來自中央氣象署，比鄰居阿姨的預測準多了 😄",
    "🌈 每一場雨後都可能有彩虹，抬頭找找看！",
    "❄️ 氣溫驟降記得加件外套，健康最重要！",
]

def weather_emoji(temp: float, rain: int) -> str:
    if rain > 70:  return "🌧️"
    if rain > 50:  return "☂️"
    if rain > 30:  return "🌦️"
    if temp < 10:  return "❄️"
    if temp < 18:  return "🧥"
    if temp < 26:  return "🌤️"
    if temp < 32:  return "☀️"
    return "🔥"

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌏 城市選擇")
    cities = sorted(df["city"].unique().tolist())
    selected_city = st.selectbox(
        "選擇要查看的城市",
        cities,
        format_func=lambda x: f"{CITY_EMOJI.get(x,'')} {CITY_DISPLAY.get(x, x)}",
    )
    st.markdown("---")
    st.markdown("### 📡 資料來源")
    st.caption("中央氣象署（CWA）開放資料平台")
    st.markdown("### ⏰ 更新頻率")
    st.caption("每 3 小時透過 GitHub Actions 自動抓取，儀表板快取每 5 分鐘刷新。")
    st.markdown("---")
    st.caption("Made with ❤️ & Streamlit")

# ── Filter data ──────────────────────────────────────────────────────────────
city_df         = df[df["city"] == selected_city].copy()
latest_fetch    = city_df["fetched_at"].max()
latest_batch    = city_df[city_df["fetched_at"] == latest_fetch]
nearest         = latest_batch.sort_values("forecast_date").iloc[0]
city_name       = CITY_DISPLAY.get(selected_city, selected_city)
w_emoji         = weather_emoji(nearest["temperature"], nearest["rain_probability"])
updated_str     = latest_fetch.strftime("%Y-%m-%d %H:%M UTC")

# ── Hero ─────────────────────────────────────────────────────────────────────
col_text, col_icon = st.columns([5, 1])
with col_text:
    st.markdown(f"""
    <div class="hero">
        <h1>{CITY_EMOJI.get(selected_city,'')} 台灣天氣通 · {city_name}</h1>
        <p>🔄 最後更新：{updated_str} &nbsp;｜&nbsp; ⚡ 自動更新：每 3 小時</p>
    </div>
    """, unsafe_allow_html=True)
with col_icon:
    st.markdown(f"<div style='text-align:center; font-size:5rem; padding-top:0.3rem'>{w_emoji}</div>",
                unsafe_allow_html=True)

# ── Metrics ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡️ 氣溫",    f"{nearest['temperature']:.1f} °C")
c2.metric("☔ 降雨機率", f"{nearest['rain_probability']} %")
c3.metric("😊 舒適度",  nearest["comfort_index"])
c4.metric("📅 預報日期", nearest["forecast_date"].strftime("%m/%d"))

# Outfit tip
st.markdown(f'<div class="outfit-card">👕 穿搭建議：{nearest["outfit_tip"]}</div>',
            unsafe_allow_html=True)

# Fun tip (random each load)
tip = random.choice(FUN_TIPS)
st.markdown(f'<div class="fun-card">💡 今日小提醒：{tip}</div>', unsafe_allow_html=True)

# ── Trend charts ─────────────────────────────────────────────────────────────
trend_df = (
    city_df.sort_values("fetched_at", ascending=False)
    .drop_duplicates(subset=["forecast_date"])
    .sort_values("forecast_date")
    .reset_index(drop=True)
)

st.markdown('<div class="section-bar">🌡️ 氣溫預報趨勢</div>', unsafe_allow_html=True)

fig_temp = px.line(
    trend_df, x="forecast_date", y="temperature",
    markers=True,
    labels={"forecast_date": "日期", "temperature": "氣溫 (°C)"},
    color_discrete_sequence=["#0984e3"],
)
fig_temp.update_traces(
    marker=dict(size=10, color="#ffffff", line=dict(width=2, color="#0984e3")),
    line=dict(width=3),
)
fig_temp.update_layout(
    height=320, hovermode="x unified",
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(showgrid=False, tickformat="%m/%d"),
    yaxis=dict(gridcolor="#f0f0f0", ticksuffix=" °C"),
    font=dict(family="Noto Sans TC, sans-serif"),
)
st.plotly_chart(fig_temp, use_container_width=True)

st.markdown('<div class="section-bar">☔ 降雨機率預報</div>', unsafe_allow_html=True)

fig_rain = px.bar(
    trend_df, x="forecast_date", y="rain_probability",
    labels={"forecast_date": "日期", "rain_probability": "降雨機率 (%)"},
    color="rain_probability",
    color_continuous_scale=["#b2d8f7", "#0984e3", "#2d3436"],
    range_y=[0, 100],
)
fig_rain.update_layout(
    height=280, coloraxis_showscale=False,
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(showgrid=False, tickformat="%m/%d"),
    yaxis=dict(gridcolor="#f0f0f0", ticksuffix=" %"),
    font=dict(family="Noto Sans TC, sans-serif"),
    bargap=0.35,
)
st.plotly_chart(fig_rain, use_container_width=True)

# ── Three-city comparison ────────────────────────────────────────────────────
st.markdown('<div class="section-bar">🏙️ 三城市即時比較</div>', unsafe_allow_html=True)

all_latest = (
    df.groupby("city", group_keys=False)
    .apply(lambda g: g[g["fetched_at"] == g["fetched_at"].max()])
    .sort_values("forecast_date")
    .drop_duplicates(subset=["city", "forecast_date"])
)
all_latest = all_latest.copy()
all_latest["城市"] = all_latest["city"].map(lambda x: CITY_DISPLAY.get(x, x))

col_l, col_r = st.columns(2)

with col_l:
    fig_cmp_t = px.bar(
        all_latest.drop_duplicates("city"),
        x="城市", y="temperature",
        color="城市",
        color_discrete_map={"台北市": "#0984e3", "台中市": "#00b894", "高雄市": "#e17055"},
        labels={"temperature": "氣溫 (°C)"},
        title="各城市氣溫",
        text_auto=".1f",
    )
    fig_cmp_t.update_layout(
        height=280, showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=36, b=0),
        font=dict(family="Noto Sans TC, sans-serif"),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    fig_cmp_t.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_cmp_t, use_container_width=True)

with col_r:
    fig_cmp_r = px.bar(
        all_latest.drop_duplicates("city"),
        x="城市", y="rain_probability",
        color="城市",
        color_discrete_map={"台北市": "#74b9ff", "台中市": "#55efc4", "高雄市": "#fab1a0"},
        labels={"rain_probability": "降雨機率 (%)"},
        title="各城市降雨機率",
        range_y=[0, 100],
        text_auto=True,
    )
    fig_cmp_r.update_layout(
        height=280, showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=36, b=0),
        font=dict(family="Noto Sans TC, sans-serif"),
        yaxis=dict(gridcolor="#f0f0f0", ticksuffix=" %"),
    )
    fig_cmp_r.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_cmp_r, use_container_width=True)

# ── Raw data ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-bar">📊 原始資料（最新批次）</div>', unsafe_allow_html=True)

display_df = latest_batch[[
    "forecast_date", "city", "temperature", "rain_probability",
    "comfort_index", "outfit_tip", "fetched_at"
]].rename(columns={
    "forecast_date":    "預報日期",
    "city":             "城市",
    "temperature":      "氣溫 (°C)",
    "rain_probability": "降雨機率 (%)",
    "comfort_index":    "舒適度",
    "outfit_tip":       "穿搭建議",
    "fetched_at":       "擷取時間 (UTC)",
}).sort_values("預報日期")
display_df["城市"] = display_df["城市"].map(lambda x: CITY_DISPLAY.get(x, x))

st.dataframe(display_df, use_container_width=True, hide_index=True)
st.caption("資料來源：中央氣象署（CWA）開放資料平台 ｜ 自動化 ETL Pipeline")
