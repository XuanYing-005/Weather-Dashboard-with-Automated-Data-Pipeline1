-- PostgreSQL DDL for Supabase
-- Run this once in the Supabase SQL Editor to create the table

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id          SERIAL PRIMARY KEY,
    fetched_at  TIMESTAMPTZ NOT NULL,
    forecast_date DATE NOT NULL,
    city        VARCHAR(50) NOT NULL,
    temperature FLOAT,
    rain_probability INT,
    comfort_index VARCHAR(20),
    outfit_tip  TEXT
);

CREATE INDEX IF NOT EXISTS idx_wf_city ON weather_forecasts (city);
CREATE INDEX IF NOT EXISTS idx_wf_fetched_at ON weather_forecasts (fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_wf_forecast_date ON weather_forecasts (forecast_date);
