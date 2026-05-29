Project Implementation Plan: Weather Dashboard with Automated Data Pipeline
1. Project Overview
Objective: Build and deploy a web-based weather and lifestyle index dashboard with a fully automated, cloud-based data pipeline (ETL).

Constraints:

No Business Intelligence tools (Tableau/Power BI) allowed.

No localhost demonstration allowed for the final submission; must be accessible via a public URL.

Complete development and deployment within 7 days.

Zero grid web development experience (HTML/CSS/JS to be avoided via pure-Python stack).

Tech Stack:

Frontend/Dashboard: Streamlit (deployed on Streamlit Community Cloud)

Backend & ETL: Python (requests, pandas, SQLAlchemy)

Database: Supabase (Cloud PostgreSQL)

Data Refresh Mechanism: GitHub Actions (Cron Job)

2. System Architecture & Data Flow
[ Central Weather Administration API ] (Data Source)
                │
                ▼ (Python Extraction: requests)
       [ GitHub Actions ] (Cron Job Server - Runs every 3 hours)
                │
                ▼ (Data Wrangling: pandas)
       [ Supabase (PostgreSQL) ] (Cloud Database)
                │
                ▼ (SQL Query: SQLAlchemy/psycopg2)
 [ Streamlit Community Cloud ] (Publicly Hosted Dashboard App)
3. Implementation Steps (7-Day Sprint Blueprint)
Phase 1: Database Setup & ETL Pipeline (Day 1-2)
Goal: Extract real-time weather data from open APIs, clean it, and load it into Supabase.

Tasks for Claude Code:

Define a PostgreSQL schema for a table named weather_forecasts with columns: id (serial), fetched_at (timestamp), forecast_date (date), city (varchar), temperature (float), rain_probability (int), comfort_index (varchar), and outfit_tip (text).

Create a Python script etl.py that:

Fetches current 36-hour or 7-day weather forecast JSON data from the Taiwan Central Weather Administration (CWA) Open Data API (or OpenWeatherMap API).

Parses the JSON and transforms it into a structured Pandas DataFrame.

Computes a derived feature outfit_tip based on business logic (e.g., if rain probability > 50%, suggest "Bring an umbrella"; if temp < 18°C, suggest "Wear a heavy coat").

Uploads the clean DataFrame to Supabase using SQLAlchemy, overwriting or appending data with proper timestamps.

Phase 2: Automation via GitHub Actions (Day 3)
Goal: Enable the data pipeline to run automatically in the cloud without local intervention.

Tasks for Claude Code:

Generate a GitHub Actions workflow file .github/workflows/refresh.yml.

Configure the workflow to trigger via a cron schedule (e.g., every 3 hours) and manually (workflow_dispatch).

Ensure it sets up a Python environment, installs dependencies from requirements.txt, injects Supabase credentials via GitHub Secrets, and executes python etl.py.

Phase 3: Interactive Streamlit Dashboard (Day 4-5)
Goal: Create a high-quality visual frontend that reads from the cloud database.

Tasks for Claude Code:

Create a Streamlit application app.py.

Implement interactive widgets: a dropdown selectbox (st.selectbox) for users to filter data by city (e.g., Taipei, Taichung, Kaohsiung).

Display key-value indicators using st.metric for current temperature and rain probability.

Visualize temperature trends over time using st.line_chart or plotly express charts.

Render the structured raw data table using st.dataframe to display data pipeline competency to the grader.

Add a visual notice showing the "Last Updated Timestamp" fetched from the database to prove the auto-refresh is active.

Phase 4: Deployment & Documentation (Day 6-7)
Goal: Go live and prepare the final executive summary.

Tasks for Claude Code:

Generate a clean requirements.txt listing all explicit dependencies (streamlit, pandas, supabase, sqlalchemy, psycopg2-binary, requests, plotly).

Draft a 1-page Executive Summary in Markdown layout matching the grading criteria (Pipeline, Visualization, Refresh Mechanism, Communication).

4. Prompt Instructions for Claude Code (How to activate this plan)
"Act as a Senior Data Engineer and Python Web Developer. I have provided our 7-day project plan above. Please start with Phase 1. Give me the PostgreSQL DDL script to create the table in Supabase, and write the complete, robust etl.py script to fetch, clean, and load the weather data. Use mock variables for API keys and database credentials, and explain how I should set them up as environment variables."