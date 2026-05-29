# Executive Summary — Taiwan Weather Dashboard

## Project Overview

A publicly accessible weather dashboard for Taipei, Taichung, and Kaohsiung, built on a fully automated cloud-based ETL pipeline. No BI tools or localhost demo required.

---

## 1. Data Pipeline (ETL)

| Component | Technology | Detail |
|-----------|-----------|--------|
| Data Source | Taiwan CWA Open Data API (`F-C0032-001`) | 36-hour forecast (temp, rain %) |
| Extraction | Python `requests` | Fetches JSON for 3 cities per run |
| Transformation | `pandas` | Parses JSON → DataFrame; derives `comfort_index` & `outfit_tip` |
| Load | `SQLAlchemy` + `psycopg2` | Appends to Supabase (PostgreSQL); auto-purges records > 7 days old |

**Derived features (business logic):**
- `comfort_index`: categorizes average temperature into Cold / Cool / Comfortable / Warm / Hot
- `outfit_tip`: rule-based recommendation (umbrella if PoP > 50 %, coat if < 18 °C, etc.)

---

## 2. Refresh Mechanism (Automation)

| Component | Technology | Detail |
|-----------|-----------|--------|
| Scheduler | GitHub Actions | Cron `0 */3 * * *` — runs every 3 hours, 24/7 |
| Manual trigger | `workflow_dispatch` | One-click re-run from GitHub UI |
| Secrets management | GitHub Secrets | `CWA_API_KEY` and `DATABASE_URL` injected at runtime |
| Dashboard cache | `st.cache_data(ttl=300)` | Dashboard refreshes from DB every 5 minutes |

**Evidence of auto-refresh:** The dashboard prominently displays the "Last Pipeline Run" timestamp sourced directly from `fetched_at` in the database, proving live data flow.

---

## 3. Visualization (Dashboard)

Hosted on **Streamlit Community Cloud** (public URL, zero-infrastructure).

| Widget | Purpose |
|--------|---------|
| `st.selectbox` | Filter all visuals by city (Taipei / Taichung / Kaohsiung) |
| `st.metric` (×4) | At-a-glance: Temperature, Rain Probability, Comfort Index, Forecast Date |
| Plotly line chart | Temperature trend across forecast dates |
| Plotly bar chart | Rain probability per forecast date |
| `st.dataframe` | Full raw pipeline output — demonstrates ETL competency |
| `st.info` banner | Displays last pipeline run timestamp + refresh cadence |

---

## 4. Deployment Instructions

### Step 1 — Database (Supabase)
1. Create a free project at [supabase.com](https://supabase.com).
2. Open the SQL Editor and run `schema.sql` to create the `weather_forecasts` table.
3. Copy the **Connection String** from Settings → Database.

### Step 2 — CWA API Key
1. Register at [opendata.cwa.gov.tw](https://opendata.cwa.gov.tw).
2. Generate an API key from your account dashboard.

### Step 3 — GitHub Repository
1. Push this project to a public GitHub repository.
2. Go to **Settings → Secrets and variables → Actions** and add:
   - `CWA_API_KEY` — your CWA API key
   - `DATABASE_URL` — your Supabase connection string
3. The GitHub Actions workflow (`.github/workflows/refresh.yml`) will run automatically every 3 hours.

### Step 4 — Streamlit Cloud
1. Log in at [share.streamlit.io](https://share.streamlit.io).
2. Connect your GitHub repository and set `app.py` as the entry point.
3. In **Advanced settings → Secrets**, paste:
   ```toml
   DATABASE_URL = "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
   ```
4. Deploy — your dashboard is now live at a public URL.

---

## Technology Stack Summary

```
[ CWA Open Data API ]
        │  requests (Python)
        ▼
[ GitHub Actions Cron ] ──── every 3 hours ────►  etl.py (pandas transform)
        │  SQLAlchemy / psycopg2
        ▼
[ Supabase (PostgreSQL) ]
        │  SQLAlchemy read
        ▼
[ Streamlit Community Cloud ]  ──►  Public Dashboard URL
```

**All constraints satisfied:** no BI tools, no localhost, pure-Python stack, publicly hosted, automated pipeline.
