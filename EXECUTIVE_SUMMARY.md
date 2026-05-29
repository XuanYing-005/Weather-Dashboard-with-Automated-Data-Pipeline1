# Executive Summary
## Taiwan Weather Dashboard with Automated Data Pipeline

**Live URL:** https://weather-dashboard-with-automated-data-pipeline1-iufvb7uqvnujqx.streamlit.app

---

## 1. Data Pipeline / ETL / Data Wrangling

**Data Source:** Taiwan Central Weather Administration (CWA) Open Data API — 36-hour forecast endpoint (`F-C0032-001`), covering **all 22 administrative districts** of Taiwan.

| Stage | Tool | Description |
|---|---|---|
| Extract | `requests` | Fetches real-time JSON forecast for all 22 cities per run |
| Transform | `pandas` | Parses nested JSON; computes average temperature from min/max; derives two business-logic features |
| Load | `SQLAlchemy` + `psycopg2` | Appends structured records to Supabase (PostgreSQL); auto-purges data older than 7 days |

**Derived Features (Business Logic):**
- `comfort_index` — classifies average temperature into 5 levels: 寒冷 / 涼爽 / 舒適 / 溫熱 / 炎熱
- `outfit_tip` — rule-based daily recommendation: umbrella (PoP > 50%), heavy coat (< 18°C), light jacket (< 24°C), light clothing otherwise

**Schema:** `weather_forecasts(id, fetched_at, forecast_date, city, temperature, rain_probability, comfort_index, outfit_tip)`

---

## 2. Data Refresh Mechanism

| Component | Implementation |
|---|---|
| Scheduler | GitHub Actions cron — `0 */3 * * *` (every 3 hours, 24/7, zero infrastructure cost) |
| Manual trigger | `workflow_dispatch` — one-click re-run from GitHub UI |
| Credential management | `CWA_API_KEY` and `DATABASE_URL` injected via GitHub Secrets (never hardcoded) |
| Dashboard cache | `st.cache_data(ttl=300)` — re-queries database every 5 minutes |
| Proof of liveness | Dashboard prominently shows **Last Pipeline Run** timestamp pulled directly from `fetched_at` in the database |

---

## 3. Visualization

Hosted on **Streamlit Community Cloud** (public URL, no server management).

| Element | Purpose |
|---|---|
| City selector (`st.selectbox`) | Filter all visuals by any of the 22 districts, sorted by geographic region |
| 4× `st.metric` cards | At-a-glance: Temperature, Rain Probability, Comfort Index, Forecast Date |
| Dynamic weather emoji | Auto-selects from ❄️🧥🌤️☀️🔥🌧️ based on live temperature & rain data |
| Plotly line chart | Temperature trend with area fill across forecast dates |
| Plotly bar chart | Rain probability with gradient color scale (light → deep blue) |
| 3-city comparison charts | Side-by-side bar charts comparing all major cities simultaneously |
| `st.dataframe` | Full raw pipeline output — demonstrates end-to-end ETL transparency |
| Daily tip card | Randomly selected weather tips on each load — enhances user engagement |

**UI Design:** Custom Neumorphism (Soft UI) style — unified Noto Sans TC font, extruded card shadows, consistent `#e0e5ec` color palette throughout.

---

## 4. Architecture

```
[ CWA Open Data API ]
        │  Python requests
        ▼
[ GitHub Actions ]  ──  cron every 3 hrs  ──►  etl.py  (pandas wrangling)
        │  SQLAlchemy / psycopg2
        ▼
[ Supabase PostgreSQL ]  ──  7-day rolling window
        │  SQLAlchemy read  (cache TTL 5 min)
        ▼
[ Streamlit Community Cloud ]  ──►  Public Dashboard URL
```

**Constraints satisfied:** No BI tools · No localhost · Pure Python · Fully cloud-hosted · Automated pipeline · Zero manual data refresh
