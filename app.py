"""
Taiwan Weather Dashboard — Neumorphism UI
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

BG = "#e0e5ec"
SHADOW_DARK  = "#a3b1c6"
SHADOW_LIGHT = "#ffffff"
TEXT_PRIMARY  = "#31344b"
TEXT_SECONDARY = "#6b7280"

NEU_CARD = f"""
    background: {BG};
    border-radius: 20px;
    box-shadow: 8px 8px 18px {SHADOW_DARK}, -8px -8px 18px {SHADOW_LIGHT};
"""
NEU_INSET = f"""
    background: {BG};
    border-radius: 16px;
    box-shadow: inset 5px 5px 10px {SHADOW_DARK}, inset -5px -5px 10px {SHADOW_LIGHT};
"""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

* {{ font-family: 'Noto Sans TC', 'PingFang TC', sans-serif !important; }}

/* ── Global background ── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {{
    background: {BG} !important;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 2rem !important; max-width: 1100px; }}

/* ── Selectbox ── */
[data-testid="stSelectbox"] {{
    border-radius: 14px !important;
}}
[data-testid="stSelectbox"] > div {{
    background: {BG} !important;
    border-radius: 14px !important;
    box-shadow: 5px 5px 12px {SHADOW_DARK}, -5px -5px 12px {SHADOW_LIGHT} !important;
    border: none !important;
}}
/* ── Metric containers ── */
[data-testid="metric-container"] {{
    background: {BG} !important;
    border-radius: 20px !important;
    padding: 1.4rem 1.2rem !important;
    box-shadow: 8px 8px 18px {SHADOW_DARK}, -8px -8px 18px {SHADOW_LIGHT} !important;
    border: none !important;
}}
[data-testid="metric-container"] label {{
    font-size: 0.78rem !important;
    color: {TEXT_SECONDARY} !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    color: {TEXT_PRIMARY} !important;
}}

/* ── Selectbox ── */
[data-testid="stSelectbox"] {{
    background: {BG} !important;
    border-radius: 14px !important;
    box-shadow: 5px 5px 12px {SHADOW_DARK}, -5px -5px 12px {SHADOW_LIGHT} !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border-radius: 20px !important;
    overflow: hidden;
    box-shadow: 8px 8px 18px {SHADOW_DARK}, -8px -8px 18px {SHADOW_LIGHT} !important;
}}

/* ── Plotly chart container ── */
[data-testid="stPlotlyChart"] {{
    border-radius: 20px !important;
    padding: 0.5rem !important;
    box-shadow: 8px 8px 18px {SHADOW_DARK}, -8px -8px 18px {SHADOW_LIGHT} !important;
    background: {BG} !important;
}}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {{ color: {TEXT_SECONDARY} !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {SHADOW_DARK}; border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

# ── DB ───────────────────────────────────────────────────────────────────────
def get_database_url() -> str:
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        url = os.environ.get("DATABASE_URL")
        if not url:
            st.error("DATABASE_URL 未設定。")
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
CITY_DISPLAY = {
    "Taipei": "台北市",       "NewTaipei": "新北市",    "Taoyuan": "桃園市",
    "Taichung": "台中市",     "Tainan": "台南市",       "Kaohsiung": "高雄市",
    "Keelung": "基隆市",      "Hsinchu": "新竹市",      "HsinchuCounty": "新竹縣",
    "Miaoli": "苗栗縣",       "Changhua": "彰化縣",     "Nantou": "南投縣",
    "Yunlin": "雲林縣",       "Chiayi": "嘉義市",       "ChiayiCounty": "嘉義縣",
    "Pingtung": "屏東縣",     "Yilan": "宜蘭縣",        "Hualien": "花蓮縣",
    "Taitung": "台東縣",      "Penghu": "澎湖縣",       "Kinmen": "金門縣",
    "Lienchiang": "連江縣",
}
CITY_EMOJI = {
    "Taipei": "🏙️",   "NewTaipei": "🌆",  "Taoyuan": "✈️",
    "Taichung": "🌳",  "Tainan": "🏯",     "Kaohsiung": "🌊",
    "Keelung": "⚓",   "Hsinchu": "💨",    "HsinchuCounty": "🌾",
    "Miaoli": "🏔️",   "Changhua": "🐂",   "Nantou": "🏞️",
    "Yunlin": "🌽",    "Chiayi": "🌲",     "ChiayiCounty": "🌿",
    "Pingtung": "🌴",  "Yilan": "🦆",      "Hualien": "🦅",
    "Taitung": "🌺",   "Penghu": "🪸",     "Kinmen": "🦀",
    "Lienchiang": "🏝️",
}

FUN_TIPS = [
    "☀️ 出門前抬頭看天空，比看手機更準！",
    "💧 天氣熱的時候記得多喝水，每天至少 2000ml！",
    "🌿 台灣的天氣變化快，包包裡放把折疊傘最保險～",
    "🧴 紫外線強的時候，防曬乳是你最好的朋友！",
    "🍵 下雨天最適合喝一杯熱飲，讓心情變好 ☕",
    "🌈 每一場雨後都可能有彩虹，抬頭找找看！",
    "❄️ 氣溫驟降記得加件外套，健康最重要！",
    "🎒 今天的天氣資料來自中央氣象署，比鄰居阿姨的預測準多了 😄",
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

def chart_layout(title="", height=300):
    return dict(
        title=dict(text=title, font=dict(size=13, color=TEXT_SECONDARY, family="Noto Sans TC")),
        height=height,
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        margin=dict(l=10, r=10, t=36, b=10),
        font=dict(family="Noto Sans TC, sans-serif", color=TEXT_PRIMARY),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SECONDARY), tickformat="%m/%d"),
        yaxis=dict(gridcolor="#cdd3df", gridwidth=1, tickfont=dict(color=TEXT_SECONDARY)),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=BG, bordercolor=SHADOW_DARK, font_color=TEXT_PRIMARY),
    )

# ── Top bar ──────────────────────────────────────────────────────────────────
top_left, top_right = st.columns([3, 1])
with top_left:
    st.markdown(f"""
    <div style='padding:0.4rem 0 1rem;'>
        <span style='font-size:1.5rem; font-weight:900; color:{TEXT_PRIMARY};'>🌤️ 台灣天氣通</span>
        <span style='font-size:0.8rem; color:{TEXT_SECONDARY}; margin-left:0.8rem;'>Taiwan Weather Dashboard</span>
    </div>
    """, unsafe_allow_html=True)
with top_right:
    st.markdown(f"""
    <div style='font-size:0.72rem; color:{TEXT_SECONDARY}; text-align:right; padding-top:0.6rem;'>
        📡 中央氣象署 ｜ ⏰ 每 3 小時更新
    </div>
    """, unsafe_allow_html=True)

cities = sorted(df["city"].unique().tolist())
sel_col, _ = st.columns([2, 3])
with sel_col:
    selected_city = st.selectbox(
        "選擇縣市",
        cities,
        format_func=lambda x: f"{CITY_EMOJI.get(x,'')} {CITY_DISPLAY.get(x, x)}",
    )

# ── Filter data ──────────────────────────────────────────────────────────────
city_df      = df[df["city"] == selected_city].copy()
latest_fetch = city_df["fetched_at"].max()
latest_batch = city_df[city_df["fetched_at"] == latest_fetch]
nearest      = latest_batch.sort_values("forecast_date").iloc[0]
city_name    = CITY_DISPLAY.get(selected_city, selected_city)
w_emoji      = weather_emoji(nearest["temperature"], nearest["rain_probability"])
updated_str  = latest_fetch.strftime("%Y-%m-%d %H:%M UTC")

# ── Hero header ──────────────────────────────────────────────────────────────
col_h, col_e = st.columns([5, 1])
with col_h:
    st.markdown(f"""
    <div style='{NEU_CARD} padding:2rem 2.5rem; margin-bottom:1.8rem;'>
        <div style='font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase; color:{TEXT_SECONDARY}; margin-bottom:0.5rem;'>
            {CITY_EMOJI.get(selected_city,'')} TAIWAN WEATHER DASHBOARD
        </div>
        <div style='font-size:2rem; font-weight:900; color:{TEXT_PRIMARY}; letter-spacing:0.03em;'>
            {city_name} 天氣預報
        </div>
        <div style='margin-top:0.8rem;'>
            <span style='{NEU_INSET} display:inline-block; padding:0.3rem 0.9rem; font-size:0.78rem; color:{TEXT_SECONDARY}; border-radius:99px;'>
                🔄 最後更新：{updated_str}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_e:
    st.markdown(f"""
    <div style='{NEU_CARD} padding:1.8rem 1rem; text-align:center; margin-bottom:1.8rem;'>
        <div style='font-size:3.5rem; line-height:1;'>{w_emoji}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Metrics ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡️ 氣溫",    f"{nearest['temperature']:.1f} °C")
c2.metric("☔ 降雨機率", f"{nearest['rain_probability']} %")
c3.metric("😊 舒適度",  nearest["comfort_index"])
c4.metric("📅 預報日期", nearest["forecast_date"].strftime("%m / %d"))

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

# ── Outfit + fun tip ─────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"""
    <div style='{NEU_CARD} padding:1.2rem 1.6rem;'>
        <div style='font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase; color:{TEXT_SECONDARY}; margin-bottom:0.4rem;'>👕 穿搭建議</div>
        <div style='font-size:1.05rem; font-weight:600; color:{TEXT_PRIMARY};'>{nearest["outfit_tip"]}</div>
    </div>
    """, unsafe_allow_html=True)
with col_b:
    tip = random.choice(FUN_TIPS)
    st.markdown(f"""
    <div style='{NEU_CARD} padding:1.2rem 1.6rem;'>
        <div style='font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase; color:{TEXT_SECONDARY}; margin-bottom:0.4rem;'>💡 今日小提醒</div>
        <div style='font-size:0.95rem; color:{TEXT_PRIMARY};'>{tip}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Section label helper ─────────────────────────────────────────────────────
def section(icon, label):
    st.markdown(f"""
    <div style='font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase;
                color:{TEXT_SECONDARY}; margin:1.8rem 0 0.6rem; padding-left:0.2rem;'>
        {icon} {label}
    </div>""", unsafe_allow_html=True)

# ── Trend charts ─────────────────────────────────────────────────────────────
trend_df = (
    city_df.sort_values("fetched_at", ascending=False)
    .drop_duplicates(subset=["forecast_date"])
    .sort_values("forecast_date")
    .reset_index(drop=True)
)

section("🌡️", "氣溫預報趨勢")
fig_temp = go.Figure()
fig_temp.add_trace(go.Scatter(
    x=trend_df["forecast_date"], y=trend_df["temperature"],
    mode="lines+markers",
    line=dict(color="#89a4c7", width=3),
    marker=dict(size=10, color=BG, line=dict(width=2.5, color="#89a4c7")),
    fill="tozeroy",
    fillcolor="rgba(137,164,199,0.1)",
    hovertemplate="%{x|%m/%d}<br>氣溫：%{y:.1f} °C<extra></extra>",
))
fig_temp.update_layout(**chart_layout(height=300))
fig_temp.update_yaxes(ticksuffix=" °C")
st.plotly_chart(fig_temp, use_container_width=True)

section("☔", "降雨機率預報")
fig_rain = go.Figure()
fig_rain.add_trace(go.Bar(
    x=trend_df["forecast_date"], y=trend_df["rain_probability"],
    marker=dict(
        color=trend_df["rain_probability"],
        colorscale=[[0, "#d4e4f7"], [0.5, "#89a4c7"], [1, "#4a6fa5"]],
        line=dict(width=0),
    ),
    hovertemplate="%{x|%m/%d}<br>降雨機率：%{y} %<extra></extra>",
))
fig_rain.update_layout(**chart_layout(height=260))
fig_rain.update_yaxes(ticksuffix=" %", range=[0, 100])
fig_rain.update_xaxes(tickformat="%m/%d")
st.plotly_chart(fig_rain, use_container_width=True)

# ── Three-city comparison ────────────────────────────────────────────────────
section("🏙️", "三城市即時比較")

latest_per_city = df.groupby("city")["fetched_at"].max().reset_index()
latest_per_city.columns = ["city", "latest_fetched_at"]
all_latest = (
    df.merge(latest_per_city, on="city")
    .query("fetched_at == latest_fetched_at")
    .drop(columns=["latest_fetched_at"])
    .drop_duplicates(subset=["city", "forecast_date"])
    .sort_values("forecast_date")
    .copy()
)
all_latest["城市"] = all_latest["city"].map(lambda x: CITY_DISPLAY.get(x, x))
first_day = all_latest.drop_duplicates("city")

CITY_COLORS = {
    "台北市": "#89a4c7",
    "台中市": "#a8d5b5",
    "高雄市": "#e8a0b4",
}

col_l, col_r = st.columns(2)
with col_l:
    fig_ct = go.Figure()
    for _, row in first_day.iterrows():
        c = row["城市"]
        fig_ct.add_trace(go.Bar(
            x=[c], y=[row["temperature"]],
            name=c,
            marker_color=CITY_COLORS.get(c, "#aaa"),
            marker_line_width=0,
            text=[f"{row['temperature']:.1f}°C"],
            textposition="outside",
            hovertemplate=f"{c}<br>氣溫：%{{y:.1f}} °C<extra></extra>",
        ))
    fig_ct.update_layout(**chart_layout("氣溫比較", height=280))
    fig_ct.update_layout(showlegend=False, bargap=0.45)
    fig_ct.update_yaxes(ticksuffix=" °C")
    st.plotly_chart(fig_ct, use_container_width=True)

with col_r:
    fig_cr = go.Figure()
    for _, row in first_day.iterrows():
        c = row["城市"]
        fig_cr.add_trace(go.Bar(
            x=[c], y=[row["rain_probability"]],
            name=c,
            marker_color=CITY_COLORS.get(c, "#aaa"),
            marker_line_width=0,
            text=[f"{int(row['rain_probability'])}%"],
            textposition="outside",
            hovertemplate=f"{c}<br>降雨機率：%{{y}} %<extra></extra>",
        ))
    fig_cr.update_layout(**chart_layout("降雨機率比較", height=280))
    fig_cr.update_layout(showlegend=False, bargap=0.45)
    fig_cr.update_yaxes(ticksuffix=" %", range=[0, 110])
    st.plotly_chart(fig_cr, use_container_width=True)

# ── Raw data ─────────────────────────────────────────────────────────────────
section("📊", "原始資料（最新批次）")

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
