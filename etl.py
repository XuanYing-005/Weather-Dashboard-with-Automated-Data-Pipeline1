"""
ETL Pipeline: Taiwan CWA Weather API → Supabase PostgreSQL
Fetches 36-hour forecasts for Taipei, Taichung, and Kaohsiung every run.
"""
import os
import logging
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — set these as environment variables or GitHub Secrets
# ---------------------------------------------------------------------------
CWA_API_KEY = os.environ["CWA_API_KEY"]          # Apply at opendata.cwa.gov.tw
DATABASE_URL = os.environ["DATABASE_URL"]          # Supabase connection string

# CWA 36-hour forecast endpoint (all cities/counties)
CWA_ENDPOINT = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

TARGET_CITIES_ZH = [
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "新竹縣", "苗栗縣", "彰化縣", "南投縣",
    "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣",
]
CITY_TRANSLATION = {
    "臺北市": "Taipei",      "新北市": "NewTaipei",  "桃園市": "Taoyuan",
    "臺中市": "Taichung",    "臺南市": "Tainan",      "高雄市": "Kaohsiung",
    "基隆市": "Keelung",     "新竹市": "Hsinchu",     "新竹縣": "HsinchuCounty",
    "苗栗縣": "Miaoli",      "彰化縣": "Changhua",    "南投縣": "Nantou",
    "雲林縣": "Yunlin",      "嘉義市": "Chiayi",      "嘉義縣": "ChiayiCounty",
    "屏東縣": "Pingtung",    "宜蘭縣": "Yilan",       "花蓮縣": "Hualien",
    "臺東縣": "Taitung",     "澎湖縣": "Penghu",      "金門縣": "Kinmen",
    "連江縣": "Lienchiang",
}
RETENTION_DAYS = 7  # Keep 7 days of history, then purge older records


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------
def compute_comfort_index(temp: float) -> str:
    if temp < 18:
        return "寒冷"
    elif temp < 24:
        return "涼爽"
    elif temp < 28:
        return "舒適"
    elif temp < 32:
        return "溫熱"
    else:
        return "炎熱"


def compute_outfit_tip(temp: float, rain_prob: int) -> str:
    if rain_prob > 50:
        return "記得帶傘"
    elif temp < 18:
        return "建議穿厚外套"
    elif temp < 24:
        return "建議穿薄外套"
    else:
        return "輕薄衣物即可"


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------
def fetch_forecast() -> dict:
    params = {
        "Authorization": CWA_API_KEY,
        "format": "JSON",
        "locationName": ",".join(TARGET_CITIES_ZH),
    }
    logger.info("Fetching forecast from CWA API…")
    resp = requests.get(CWA_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("success") != "true":
        raise ValueError(f"CWA API returned unexpected response: {data}")
    return data


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------
def parse_forecast(data: dict) -> pd.DataFrame:
    fetched_at = datetime.now(timezone.utc)
    records = []

    for location in data["records"]["location"]:
        city_zh = location["locationName"]
        city_en = CITY_TRANSLATION.get(city_zh, city_zh)

        # Index weather elements by name for easy access
        elements = {
            elem["elementName"]: elem["time"]
            for elem in location["weatherElement"]
        }

        pop_periods = elements.get("PoP", [])
        min_t_periods = elements.get("MinT", [])
        max_t_periods = elements.get("MaxT", [])

        for i, period in enumerate(pop_periods):
            forecast_date = period["startTime"][:10]  # "YYYY-MM-DD"

            rain_prob = int(period["parameter"]["parameterName"])

            min_t = (
                float(min_t_periods[i]["parameter"]["parameterName"])
                if i < len(min_t_periods)
                else None
            )
            max_t = (
                float(max_t_periods[i]["parameter"]["parameterName"])
                if i < len(max_t_periods)
                else None
            )

            if min_t is not None and max_t is not None:
                avg_temp = round((min_t + max_t) / 2, 1)
            else:
                avg_temp = min_t if min_t is not None else max_t

            records.append(
                {
                    "fetched_at": fetched_at,
                    "forecast_date": forecast_date,
                    "city": city_en,
                    "temperature": avg_temp,
                    "rain_probability": rain_prob,
                    "comfort_index": compute_comfort_index(avg_temp),
                    "outfit_tip": compute_outfit_tip(avg_temp, rain_prob),
                }
            )

    df = pd.DataFrame(records)
    logger.info(f"Parsed {len(df)} forecast records for {df['city'].unique().tolist()}")
    return df


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def load_to_db(df: pd.DataFrame, engine) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    with engine.connect() as conn:
        # Purge records older than retention window
        result = conn.execute(
            text("DELETE FROM weather_forecasts WHERE fetched_at < :cutoff"),
            {"cutoff": cutoff},
        )
        conn.commit()
        logger.info(f"Purged {result.rowcount} records older than {RETENTION_DAYS} days")

    df.to_sql("weather_forecasts", engine, if_exists="append", index=False)
    logger.info(f"Inserted {len(df)} new records into weather_forecasts")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    raw = fetch_forecast()
    df = parse_forecast(raw)

    engine = create_engine(DATABASE_URL)
    load_to_db(df, engine)
    logger.info("ETL pipeline completed successfully.")


if __name__ == "__main__":
    main()
