================================================================================
  CYBERNOVA ANALYTICS LTD — BI PORTAL
  System Design & Technical Documentation
  CET333 Product Development  |  BSc (Hons) Business Intelligence & Data Analytics
  Author: Seipone Talama Sebina
================================================================================

Last updated : 2026-05-03
Primary file : app_html.py
Run command  : streamlit run app_html.py --server.port 8505


--------------------------------------------------------------------------------
TABLE OF CONTENTS
--------------------------------------------------------------------------------

  1.  Project Overview
  2.  System Architecture
  3.  Methodology — CRISP-DM
  4.  File Structure
  5.  Data Generation Pipeline
  6.  ETL Pipeline
  7.  Data Schema
  8.  Behavioural Segmentation Model
  9.  Dashboard Design — Three-Tab Structure
  10. Role-Based Access Control
  11. Live Pulse — Real-Time Feed
  12. Forecasting Model
  13. Geographic Analysis
  14. Statistical Evidence Layer
  15. Reporting & Exports
  16. Design System & UI Architecture
  17. Technology Stack & Dependencies
  18. Configuration Reference (config.yaml)
  19. How to Run
  20. Demo Credentials
  21. Requirements Traceability (FR1–FR12, NFR1–NFR8)
  22. Known Limitations & Constraints
  23. Glossary


================================================================================
1. PROJECT OVERVIEW
================================================================================

CyberNova Analytics Ltd is a fictitious Gaborone-based AI cybersecurity start-up
serving SMEs, financial institutions, and government agencies across Southern
Africa. Its flagship product is an AI-powered Cyber Assistant.

This system is a Product Sales Data Analysis System developed as a CET333
Product Development submission. It evaluates the online effectiveness of
CyberNova's software solutions through IIS web server log analysis, delivering
role-specific business intelligence to three stakeholder groups:

  - Sales Team Lead    → CyberNova Pulse dashboard
  - Marketing Lead     → CyberNova Reach dashboard
  - Executive Mgmt     → CyberNova Horizon dashboard

The system covers the full BI pipeline: synthetic data generation, ETL,
exploratory data analysis, behavioural segmentation, live monitoring, geographic
hotzone mapping, 30/90-day forecasting, and PDF/CSV export.

All data is entirely synthetic. No real personal or organisational data is used.


================================================================================
2. SYSTEM ARCHITECTURE
================================================================================

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        CYBERNOVA BI PORTAL                              │
  │                       High-Level Architecture                           │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐
  │  config.yaml │────▶│ generate_    │────▶│  data/output/                │
  │  Seed, dates │     │ logs.py /    │     │    cybernova_web_logs.xlsx    │
  │  countries,  │     │ synthetic_   │     │    cybernova_enriched_        │
  │  services,   │     │ log_studio.py│     │      logs.csv                │
  │  campaigns,  │     │              │     │    cybernova_iis_raw_logs.csv │
  │  anomalies   │     │  Faker + IIS │     │    generation_summary.csv     │
  └──────────────┘     │  W3C format  │     └──────────────────────────────┘
                       └──────────────┘                   │
                                                          │ load_data()
                                                          ▼
                       ┌──────────────────────────────────────────────────┐
                       │              ETL LAYER  (app_html.py)            │
                       │  - Load Excel + join enriched CSV                │
                       │  - Parse timestamps, cast booleans               │
                       │  - Resolve IP → country (static lookup)          │
                       │  - Sort chronologically                          │
                       │  - Cache with @st.cache_data                     │
                       └──────────────────────────────────────────────────┘
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                   ┌──────────┐   ┌──────────────┐  ┌──────────────┐
                   │  FILTER  │   │ LIVE TICKER  │  │  ANALYTICS   │
                   │  LAYER   │   │ @st.fragment │  │  HELPERS     │
                   │apply_    │   │ run_every=3s │  │ calculate_   │
                   │filters() │   │ ring buffer  │  │ sales/mktg/  │
                   └──────────┘   │ 300 records  │  │ exec_metrics │
                          │       └──────────────┘  └──────────────┘
                          │                                │
                          └──────────────┬────────────────┘
                                         ▼
                    ┌────────────────────────────────────────┐
                    │          STREAMLIT DASHBOARD           │
                    │                                        │
                    │  ┌──────────┐ ┌──────────┐ ┌───────┐  │
                    │  │ CyberNova│ │ CyberNova│ │Cyber  │  │
                    │  │  PULSE   │ │  REACH   │ │HORIZON│  │
                    │  │ (Sales)  │ │(Marketing│ │(Exec) │  │
                    │  └──────────┘ └──────────┘ └───────┘  │
                    └────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌────────────────────────────────────────┐
                    │         EXPORT / REPORT LAYER          │
                    │  Weekly PDF  ·  Monthly PDF            │
                    │  Evidence CSV  ·  Filtered Data CSV    │
                    └────────────────────────────────────────┘


COMPONENT SUMMARY
-----------------
  config.yaml          Master configuration — seed, date range, country
                       weights, service URIs and weights, campaign windows,
                       anomaly injection rules, output paths.

  generate_logs.py     Synthetic IIS log generator. Uses Faker for realistic
                       IP addresses, user agents, and referrers. Applies
                       country weights, peak-hour clustering, bot injection,
                       campaign traffic boosts, and anomaly events.

  synthetic_log_studio.py  Extended generation module for session enrichment,
                       segmentation, and enriched column derivation.

  validate_dataset.py  Post-generation validation — checks record count, column
                       presence, Botswana share, bot ratio bounds, and IIS
                       format compliance.

  app_html.py          Main Streamlit application (>3,300 lines). Contains:
                       CSS injection, authentication, ETL loader, filter
                       helpers, calculation helpers, story generators, chart
                       styling helpers, all three dashboard render functions,
                       PDF report builder, sidebar renderer, main loop.

  live_feed.py         Standalone live feed simulation script for development
                       and testing outside the Streamlit fragment context.

  data/output/         All generated artefacts — raw CSV, enriched CSV,
                       Excel workbook, and generation summary.


================================================================================
3. METHODOLOGY — CRISP-DM
================================================================================

This project follows CRISP-DM (Chapman et al., 2000) as the primary framework,
with CRISP-DM 2.0 layered on top to accommodate iterative data generation.

  Phase 1 — Business Understanding
    Define CyberNova's 8 business goals, identify three stakeholder audiences
    (Sales, Marketing, Executive), map requirements to FR/NFR, scope the
    prototype.

  Phase 2 — Data Understanding
    Design the synthetic IIS W3C Extended Log Format schema. Establish
    realistic Southern African traffic patterns, service URI weights, country
    distribution (≥30% Botswana), bot ratios (8–12%), peak-hour clustering,
    and campaign event windows.

  Phase 3 — Data Preparation
    ETL pipeline: ingest Excel/CSV, join enrichment columns, parse timestamps,
    cast booleans, derive hour/week/month aggregation columns, sort
    chronologically, cache.

  Phase 4 — Modelling
    Behavioural segmentation (4 tiers), linear regression forecasting
    (numpy.polyfit), correlation heatmaps (hour × service), conversion rate
    calculation, warm-lead funnel modelling.

  Phase 5 — Evaluation
    Verify FR1–FR12 and NFR1–NFR8 against the working prototype. Evaluate
    segmentation quality (distinct traffic profiles per tier), forecast
    interpretability, and chart accuracy. Obtain client sign-off.

  Phase 6 — Deployment
    Runnable locally (streamlit run) or via Streamlit Community Cloud from
    requirements.txt. No proprietary BI platform required.


================================================================================
4. FILE STRUCTURE
================================================================================

  Cybernova_BI_Project/
  │
  ├── app_html.py                    Main Streamlit application
  ├── app_final.py                   Earlier version (840 lines, kept for ref)
  ├── generate_logs.py               Synthetic IIS log generator
  ├── synthetic_log_studio.py        Extended enrichment generator
  ├── validate_dataset.py            Post-generation dataset validator
  ├── live_feed.py                   Standalone live feed script
  ├── config.yaml                    Master configuration file
  ├── requirements.txt               Python dependencies
  ├── cybernova_logo_transparent.svg Brand logo (SVG, base64-embedded in app)
  │
  ├── data/
  │   └── output/
  │       ├── cybernova_web_logs.xlsx       Primary data source (app reads this)
  │       ├── cybernova_enriched_logs.csv   Enrichment join (session, segment,
  │       │                                 event type, anomaly flags)
  │       ├── cybernova_iis_raw_logs.csv    Raw IIS-format log output
  │       └── generation_summary.csv        Generator run statistics
  │
  └── .gitignore


IMPORTANT FILE NOTES
--------------------
  app_html.py is the definitive, submission-ready file. All UI polish,
  role-based access, live feed, forecasting, geographic maps, PDF export,
  and statistical evidence are implemented here.

  app_final.py is an earlier prototype (smaller scope). Do not use for
  submission evaluation.

  The app reads data from a OneDrive-hosted path. To bypass OneDrive's file
  locking, load_data() copies the Excel file to a temp path before reading,
  then deletes the temp file.


================================================================================
5. DATA GENERATION PIPELINE
================================================================================

PURPOSE
  Produce a reproducible synthetic IIS W3C Extended Log dataset simulating
  realistic CyberNova web traffic across Southern Africa.

CONFIGURATION (config.yaml)
  random_seed          : 333  (full reproducibility across all runs)
  date_range           : 2026-01-01 to 2026-05-15
  base_daily_requests  : 500
  daily_variation      : ±35%
  weekday_factor       : 1.00  (full traffic)
  weekend_factor       : 0.45  (reduced traffic)
  monthly_growth_rate  : 8% month-on-month
  bot_ratio            : 8–12% of all requests
  mean_pages/session   : 4.0

COUNTRY DISTRIBUTION
  Botswana       32%    (exceeds the ≥30% FR2 requirement)
  South Africa   20%
  Zambia         12%
  Namibia         9%
  Zimbabwe        8%
  Lesotho         4%
  Eswatini        4%
  Mozambique      4%
  Malawi          4%
  Tanzania        3%

SERVICE URIs AND WEIGHTS
  /ai-assistant.php              28%   (flagship product)
  /cybersecurity-monitoring.php  22%
  /risk-assessment.php           16%
  /digital-transformation.php    13%
  /predictive-maintenance.php    10%
  /prototype.php                  7%
  /events.php                     4%

  Additional URIs (non-service):
  /scheduledemo.php, /event.php, /contact.php, /index.php, /about.php

CAMPAIGN WINDOWS (traffic multipliers)
  SME Cyber Risk Week            2026-02-12 to 2026-02-16   ×1.6
  AI Cyber Assistant Launch Push 2026-03-18 to 2026-03-24   ×2.0
  Gov Digital Transformation Expo 2026-04-22 to 2026-04-26  ×1.7

ANOMALY INJECTIONS
  2026-03-29  Suspicious Prototype Bot Spike  /prototype.php        ×4.0
  2026-04-03  Broken AI Campaign Link         /ai-cyber-assistant.php 404 ×3.0
  2026-05-06  Viral AI Assistant Spike        /ai-assistant.php     ×3.5

PEAK-HOUR CLUSTERING
  Business hours (09:00–17:00) carry higher request probability, simulating
  Southern African working-day traffic patterns. Peak concentration is
  10:00–14:00.

OUTPUT FILES
  cybernova_web_logs.xlsx    : Primary Excel workbook (app loads this)
  cybernova_enriched_logs.csv: Derived columns — session_id, segment,
                               event_type, is_warm_lead, is_anomaly,
                               is_bot, is_sadc, distinct_pages_session,
                               session_number_for_ip, entry_page,
                               campaign_name, anomaly_name, etc.
  cybernova_iis_raw_logs.csv : Raw IIS W3C format (for format compliance check)
  generation_summary.csv     : Row counts, bot ratio, country breakdown


================================================================================
6. ETL PIPELINE
================================================================================

FUNCTION: load_data()   [app_html.py, line ~287]
DECORATOR: @st.cache_data(show_spinner=False)

STEP 1 — Load Raw Excel
  - Copies Excel file to a system temp path (shutil.copy2) to bypass OneDrive
    file locking
  - Reads with pd.read_excel()
  - Deletes temp file after load
  - Returns None if file is missing (triggers data-missing warning in UI)

STEP 2 — Join Enriched CSV
  - Builds a composite key: ip_address + "|" + date + "|" + time
  - Left-joins enriched CSV columns onto the Excel base
  - Only non-duplicate columns are merged
  - If enriched CSV is missing, proceeds with base Excel only (graceful fallback)

STEP 3 — Parse and Cast
  - timestamp: pd.to_datetime(date + " " + time, errors="coerce")
  - date, first_request_ts, last_request_ts: pd.to_datetime
  - Boolean columns cast: is_bot, is_warm_lead, is_anomaly, converted_to_lead,
    is_sadc, is_weekend, is_campaign_period
  - session_number_for_ip: pd.to_numeric, fillna(1), int
  - anomaly_name: fillna("None"), str

STEP 4 — Sort
  - df.sort_values("timestamp") — chronological order for live ticker

DATA LOAD QUALITY SUMMARY
  Displayed as an always-visible card above the dashboard:
  - Raw rows loaded
  - Usable rows (raw minus max(bad_ts, bad_ip))
  - Invalid timestamp count
  - Missing IP count
  - Duplicate row count (flagged in red if non-zero)
  - Status badge: "Good" (all zeros) or "Review Needed"


FILTER FUNCTION: apply_filters()   [line ~335]
  Applied after sidebar selections on every render call.
  Filters: date range, countries, services, HTTP status classes, segments,
  bot inclusion toggle.
  Returns a filtered copy of the DataFrame (fdf) — never modifies the
  original cached df.


================================================================================
7. DATA SCHEMA
================================================================================

PRIMARY COLUMNS (from cybernova_web_logs.xlsx)
  date              datetime64     Request date
  time              object         Request time (HH:MM:SS)
  ip_address        object         Client IP (synthetic)
  method            object         HTTP method (GET/POST)
  uri               object         Requested URI
  status_code       int64          HTTP status code (200, 301, 404, 500...)
  bytes_transferred int64          Response size in bytes
  response_time_ms  int64          Server response time in milliseconds
  user_agent        object         Browser/bot user agent string
  referrer          object         HTTP referrer

ENRICHED COLUMNS (joined from cybernova_enriched_logs.csv)
  timestamp              datetime64    Full datetime (date + time combined)
  session_id             object        Unique session identifier per IP/day
  session_number_for_ip  int           1st, 2nd, 3rd+ visit by same IP
  entry_page             object        First URI of the session
  distinct_pages_session int           Pages visited in session
  service_name           object        Human-readable service label
  segment                object        Behavioural tier (see Section 8)
  event_type             object        page_request / demo_request / event_signup
  is_warm_lead           bool          True if /scheduledemo.php or /event.php
  is_anomaly             bool          True if flagged by anomaly injection
  is_bot                 bool          True if user-agent pattern = crawler
  is_sadc                bool          True if country is in SADC region
  is_weekend             bool          True if Saturday or Sunday
  is_campaign_period     bool          True if within a campaign window
  campaign_name          object        Name of active campaign or NaN
  anomaly_name           object        Name of anomaly event or "None"
  converted_to_lead      bool          Session contains a demo/contact request
  status_class           object        2xx / 3xx / 4xx / 5xx
  hour                   int           Request hour (0–23)
  country                object        Resolved from IP (static lookup)
  bot_ratio              float         Session-level bot proportion
  first_request_ts       datetime64    Session start timestamp
  last_request_ts        datetime64    Session end timestamp


================================================================================
8. BEHAVIOURAL SEGMENTATION MODEL
================================================================================

Four tiers are assigned at data generation time based on URI patterns and
user-agent detection. The segment column carries one of four labels:

  High-intent
    Definition : Sessions containing /scheduledemo.php or /event.php
    Signal     : Strongest purchase intent — these are warm leads
    Action     : Immediate sales follow-up

  Product-curious
    Definition : Sessions visiting /ai-assistant.php or /prototype.php
                 without proceeding to demo
    Signal     : Evaluating the product, not yet committed
    Action     : Nurture with case studies, AI-capability messaging

  General browser
    Definition : Sessions visiting /index.php, /about.php, or other
                 informational pages without service depth
    Signal     : Awareness stage
    Action     : Top-of-funnel campaign targeting

  Bot / Crawler
    Definition : User-agent string matches known crawler patterns
                 (Googlebot, Bingbot, generic spider signatures)
    Signal     : Not a human — excluded from engagement metrics
    Action     : Monitor for bot-driven distortion; filter when analysing

SEGMENTATION QUALITY CHECK
  Each tier produces meaningfully distinct traffic profiles:
  - High-intent: lowest session volume, highest bytes/response time
    (demo forms, form submissions)
  - Product-curious: moderate volume, higher distinct_pages_session
  - General browser: highest volume, lowest engagement depth
  - Bot: highest request frequency, lowest distinct_pages_session (1)


================================================================================
9. DASHBOARD DESIGN — THREE-TAB STRUCTURE
================================================================================

All three dashboards follow the same visual storytelling flow:

  [1] Hero Banner            Role name, subtitle, access badge
  [2] Context Chips Bar      Active filters, row count, data quality badge
  [3] KPI Row                5–6 metric cards
  [4] Role Summary Banner    Today's Focus / Board Summary
  [5] Live Pulse Section     Real-time stream (auto-refreshes every 3s)
  [6] Insight Assistant      Narrative story cards with bullets + action
  [7] Strategic Analytics    2-column chart grid
  [8] Geographic Hotzones    Choropleth map + country ranking
  [9] Statistical Evidence   Heatmaps, tables, descriptive stats
  [10] Forecasting Outlook   30-day or 90-day linear projection
  [11] Evidence / Action Tables  Service-level or country-level stats
  [12] Reports & Exports     PDF and CSV download section
  [13] Methodology Note      ETL diagram, data description, disclaimers


────────────────────────────────────────────────────────
9A. CYBERNOVA PULSE — Sales Dashboard
────────────────────────────────────────────────────────

AUDIENCE   : Sales Team Lead
ACCENT     : Blue / Cyan
FOCUS      : Warm-lead pipeline, conversion funnel, service demand

KPIs (6 cards)
  New Warm Leads (24h)    Today vs yesterday delta
  Weekly Warm Leads       Last 7-day rolling total
  AI → Demo Conversion    Sessions starting on AI assistant that reached demo
  Top Warm Market         Country with most warm-lead events
  Top Service Demand      Service with highest warm-lead attachment
  Top Lead Action         Most frequent high-intent event type

Strategic Analytics Charts
  1. Warm-lead volume over time (line + area chart by minute/day/week)
  2. Demo request trend overlaid (dual trace)
  3. Funnel: Index → Service Pages → Demo Page → Demo Submitted
  4. Service demand ranking (horizontal bar)
  5. Session cohort conversion rates (bar — 1st/2nd/3–5/6+ visits)
  6. Weekly warm-lead trend (line)
  7. AI Assistant: weekly requests + conversion events (dual axis)
  8. High-intent action breakdown (bar)
  9. Geographic choropleth: warm leads by country
  10. Country warm-lead ranking (horizontal bar)
  11. Service-level sales statistics table (mean, median, std, warm lead rate)
  12. Time-of-day × service heatmap
  13. 30-day warm-lead linear forecast
  14. Sales Action Queue (warm-lead evidence table)


────────────────────────────────────────────────────────
9B. CYBERNOVA REACH — Marketing Dashboard
────────────────────────────────────────────────────────

AUDIENCE   : Marketing Lead
ACCENT     : Cyan / Green
FOCUS      : Audience quality, geographic reach, content engagement, segments

KPIs (5 cards)
  Unique Visitors         Distinct IP count in filtered range
  Engaged Session Rate    Sessions with ≥3 distinct pages
  Top Entry Path          Page with highest mean engaged depth
  Geographic Reach        Countries with ≥10 requests
  Bot Ratio               Bot requests as % of total

Strategic Analytics Charts
  1. Human vs bot traffic trend (line — dual trace)
  2. Human / bot split donut
  3. Country visitor ranking (bar)
  4. Visitor vs engagement scatter (bubble sized by warm leads)
  5. Service visit vs conversion share gap analysis (grouped bar)
  6. Weekly segment composition (stacked bar)
  7. Geographic reach: visitors by country, SADC vs Other (bar)
  8. Time-of-day × service heatmap (Marketing colour scale)
  9. Bot vs human weekly stack (bar)
  10. Entry page engagement depth (bar)
  11. Country-level engagement statistics table
  12. 30-day engaged-session forecast
  13. Visitor Segment Detail (evidence table)
  14. Campaign Opportunity Matrix (service gap table)


────────────────────────────────────────────────────────
9C. CYBERNOVA HORIZON — Executive Dashboard
────────────────────────────────────────────────────────

AUDIENCE   : Executive Management
ACCENT     : Navy / Amber
FOCUS      : Growth direction, AI traction, SADC market penetration,
             strategic risk, 90-day forecast

KPIs (4 cards)
  Month-on-Month Growth     Current vs previous month visitor delta (%)
  AI Assistant Share        AI requests as % of all service requests
  SADC Active Markets       Distinct countries with ≥1 request
  30-Day Lead Forecast      Linear projection of warm leads

Strategic Analytics Charts
  1. Weekly overview: total requests + warm leads + AI requests (multi-line)
  2. Regional market ranking (bar, SADC flagged, growth % colour scale)
  3. AI Assistant: monthly requests + share trend (dual-axis bar + line)
  4. Anomaly event log (table with date, type, impact)
  5. 90-day warm-lead forecast with anomaly day markers (line + dash)
  6. Executive Decision Brief (strategic action table)
  7. Regional Priority Table


================================================================================
10. ROLE-BASED ACCESS CONTROL
================================================================================

Implemented via st.session_state in a login-gated flow.

CREDENTIALS TABLE
  Role                  Password        Dashboard Access
  ──────────────────────────────────────────────────────────────────
  Sales Team Lead       sales123        CyberNova Pulse only
  Marketing Lead        marketing123    CyberNova Reach only
  Executive Management  exec123         CyberNova Horizon only
  Admin / Lecturer View admin123        All three dashboards

FLOW
  1. User reaches login page (no session_state["logged_in"])
  2. Selects role from selectbox, enters password
  3. On correct password: session_state["logged_in"] = True,
     session_state["role"] = selected role
  4. render_sidebar() enforces access: navigation radio only shows
     dashboards permitted for that role
  5. Dashboard render functions check role and gate content blocks
  6. Logout button clears all session_state keys and reruns

LIVE FEED ROLE FILTERING
  The live ticker fragment also applies role-based priority ordering:
  - Sales   : warm leads and demo/contact events surfaced first
  - Marketing: human traffic and campaign events surfaced first
  - Executive: anomaly events, warm leads, and AI requests first


================================================================================
11. LIVE PULSE — REAL-TIME FEED
================================================================================

IMPLEMENTATION
  The live section uses Streamlit's @st.fragment(run_every=3) decorator to
  auto-refresh every 3 seconds without rerunning the full page.

MECHANISM (ring buffer replay)
  - On first render, the full sorted DataFrame is stored in
    st.session_state["_full_df"]
  - live_cursor tracks the current position in the dataset
  - Every 3 seconds: one new row is prepended to st.session_state["live_log"]
  - live_log is capped at 300 records (ring buffer behaviour)
  - The live_log is converted to a DataFrame and used for all live metrics

LIVE COMPONENTS RENDERED
  1. NOW STREAMING banner — dark gradient panel showing the current record:
     source country, IP, user agent, HTTP method + URI, service name,
     status code, response time, and bytes. Warm lead / anomaly / bot tags.

  2. Live KPI row — 8 compact cards:
     Total seen, Unique IPs, Warm leads detected, Anomalies flagged,
     Bot requests, 2xx success rate, Average response time, Total KB

  3. Live charts (3-column):
     - Human vs bot trend line (last 300 records, per 5-min window)
     - Human / bot split donut
     - Top countries by live volume (bar)
     - High-intent signals per window (bar: warm leads, demo, AI, events)
     - Status code distribution (bar)
     - Anomaly timeline (bar, amber highlight on flagged windows)

  4. Live activity feed — last 10 events rendered as styled rows with
     colour-coded dots (green = warm, amber = anomaly, blue = normal)


================================================================================
12. FORECASTING MODEL
================================================================================

METHOD : Simple linear regression via numpy.polyfit(x, y, 1)

SALES FORECAST (30 days)
  Input  : Daily warm-lead counts grouped by date
  Fit    : Least-squares linear trend on the historical series
  Output : 30 daily projected values, clipped to ≥0 (no negative leads)
  Chart  : Historical (blue solid) + Forecast (amber dashed)
  Minimum data required: 7 days

MARKETING FORECAST (30 days)
  Input  : Daily engaged-session counts (sessions with ≥3 distinct pages)
  Same regression and charting approach as Sales forecast

EXECUTIVE FORECAST (90 days)
  Input  : Daily warm-lead counts
  Output : 90 daily projected values summed to a single 3-month total
  Chart  : Historical + forecast with red vertical lines on anomaly days
  Also used: pre-computed in calculate_executive_metrics() for the KPI card

INTERPRETATION NOTE
  All forecasts are planning-level trend estimates based on simple linear
  regression. They assume the historical trend continues without structural
  breaks. They are NOT production-grade predictive models. Labelled
  "Rule-based linear projection" in all UI notes.

MODEL SELECTION RATIONALE
  Simple linear regression was selected over ARIMA/Prophet because:
  - Dataset covers ~4.5 months (insufficient for ARIMA seasonal fitting)
  - Interpretability required for client presentation
  - numpy.polyfit requires no external ML dependencies
  - The business question (direction and scale of demand) does not require
    high forecast precision


================================================================================
13. GEOGRAPHIC ANALYSIS
================================================================================

DATA SOURCE
  country column — resolved from synthetic IP using static lookup
  is_sadc column — boolean flag for SADC member countries

CHOROPLETH MAP
  Library    : Plotly Express px.choropleth
  Scope      : Africa
  Colour     : Warm-lead density per country
  Labels     : Country name, total requests, warm leads

COUNTRY RANKING PANELS
  - Horizontal bar charts ranking countries by warm leads, visitors, or requests
  - SADC vs Other colour segmentation
  - "Top Hotzones" ranked list beneath the map

GEOGRAPHIC KPIs
  - Top market by warm-lead volume
  - Geographic reach: countries with ≥10 requests
  - SADC active markets: distinct countries in the region


================================================================================
14. STATISTICAL EVIDENCE LAYER
================================================================================

SERVICE-LEVEL STATISTICS TABLE (Sales)
  Per service: Total Requests, Warm Leads, Demo Requests, Contact Requests,
  Mean / Median / Std of response time (or bytes), Warm Lead Rate (%)

COUNTRY-LEVEL ENGAGEMENT STATISTICS TABLE (Marketing)
  Per country: Unique Visitors, Engaged Sessions, Warm Leads, Bot Ratio,
  Mean / Median / Std of distinct pages per session

TIME-OF-DAY × SERVICE HEATMAP (FR12 — correlation analysis)
  Rows    : Service names
  Columns : Hour of day (0–23)
  Values  : Request count (colour intensity)
  Purpose : Identifies which services are most requested at which hours
            — directly addresses the FR12 correlation requirement

DESCRIPTIVE STATISTICS COMPUTED
  Mean     : mean()  — average pages/session, average response time
  Median   : median() — robust central tendency
  Std Dev  : std()   — variability in session depth or response time
  Totals   : sum()   — request counts, lead counts, byte totals
  Rates    : Warm lead %, engagement rate %, bot ratio %


================================================================================
15. REPORTING & EXPORTS
================================================================================

PDF REPORT BUILDER   [build_pdf_report(), line ~1443]
  Library : ReportLab (SimpleDocTemplate, A4)
  Content :
    - Report header with CyberNova brand colours
    - Filter context table (date range, countries, services, status, bots)
    - KPI summary table (label, value, context)
    - AI-generated narrative bullets (from generate_*_story functions)
    - Recommended Action panel
    - Evidence table (top 20 rows of evidence DataFrame)
    - Footer with timestamp and role

  WEEKLY PDF  : KPI summary, live pulse snapshot, top hotzones, evidence table
  MONTHLY PDF : Trend analysis, forecast projection, regional analysis,
                narrative bullets, recommendations, evidence table

CSV EXPORTS
  Evidence Pack CSV   : The evidence DataFrame for the current role
                        (warm leads / segments / anomaly log)
  Filtered Data CSV   : Full filtered dataset (fdf) for the current
                        filter state

EXPORT BUTTONS
  Placed in a premium report card with filter context badges, row count badge,
  generated timestamp, and report contents preview (weekly and monthly).

REPORT PREVIEW PANEL
  Shows before the download buttons:
  - Weekly report contents summary
  - Monthly report contents summary
  - Active filter chips
  - Row count and generated timestamp


================================================================================
16. DESIGN SYSTEM & UI ARCHITECTURE
================================================================================

COLOUR TOKENS
  BG          #F1F3F6   Page background (light grey)
  CARD        #FFFFFF   Card surfaces
  NAVY        #0B1F3A   Primary headings, high-emphasis text
  HEADER      #1F3A5F   Secondary headings
  TEXT        #102A43   Body text
  SECONDARY   #52606D   Supporting text
  MUTED       #7B8794   Labels, captions, eyebrow text
  BORDER      #D9E2EC   Card borders, divider lines
  BLUE        #2563FF   Primary accent (Sales identity, CTAs)
  BLUE_SOFT   #DBEAFE   Blue chip backgrounds, insight banners
  CYAN        #16B8C7   Secondary accent (Marketing identity)
  CYAN_SOFT   #CFFAFE   Cyan backgrounds
  GREEN       #10B981   Positive indicators, success states
  GREEN_SOFT  #D1FAE5   Green chip backgrounds
  AMBER       #F59E0B   Warnings, forecast lines, Executive accent
  AMBER_SOFT  #FEF3C7   Amber chip backgrounds
  SLATE_SOFT  #E5EAF0   Neutral surfaces, ETL diagram background

ROLE ACCENT IDENTITY
  Sales        → Blue / Cyan     (professional, transactional)
  Marketing    → Cyan / Green    (growth, engagement)
  Executive    → Navy / Amber    (authority, strategic risk)

CARD SYSTEM
  All analytics content sits inside st.container(border=True) white cards.
  CSS overrides target [data-testid="stVerticalBlockBorderWrapper"]:
  - background:white, border-radius:20px, border:1px solid #D9E2EC
  - box-shadow: layered soft shadow
  - overflow:hidden (clips content at rounded corners)
  - margin-bottom:28px (consistent spacing between stacked cards)
  - inner padding: 26px 28px 36px (generous bottom to clear rounded corners)
  - inner gap: 1.1rem between Streamlit elements

CARD STRUCTURE (per analytics card)
  1. Eyebrow label (optional) — 10px uppercase, muted grey
  2. Business-question title — 17px bold navy
  3. Short subtitle — 12.5px muted grey
  4. Gradient rule — 1px separator
  5. Chart or table
  6. Insight note — rounded rect, colour-coded by signal type

SECTION HEADING PATTERN  [render_section_label()]
  - Small uppercase eyebrow on the left
  - Gradient divider line extending to the right
  - Large bold heading below (23px, navy, tight letter-spacing)
  - 52px top margin, 22px bottom margin

INSIGHT NOTE COLOURS
  Informational (blue)  : BLUE_SOFT background, #1E40AF text
  Positive (green)      : GREEN_SOFT background, #047857 text
  Warning (amber)       : AMBER_SOFT background, #92400E text
  Cyan (marketing)      : CYAN_SOFT background, #0E7490 text

TYPOGRAPHY
  Font stack : Inter, Segoe UI, Arial, sans-serif
  Headings   : 950–900 weight, navy, tight letter-spacing (-.04em to -.055em)
  KPI values : 31px / 17px (adaptive based on value length)
  Body       : 13–15px, #102A43
  Captions   : 11–12px, MUTED
  Eyebrows   : 10–10.5px, uppercase, letter-spacing .14em–.16em

SIDEBAR
  Background : Linear gradient (#0B1E3D → #102A43) — dark navy
  Nav items  : Styled as pill buttons with active state indicator
               (blue gradient fill + cyan left inset shadow when selected)


================================================================================
17. TECHNOLOGY STACK & DEPENDENCIES
================================================================================

RUNTIME
  Python 3.10+
  Streamlit (≥1.31 recommended for st.html() support)

CORE LIBRARIES
  pandas          Data manipulation, aggregation, merging
  numpy           Numerical operations, linear regression (polyfit)
  plotly          Interactive charts (px and go modules)
  streamlit       Web application framework, fragments, state management

DATA GENERATION
  faker           Synthetic IP, user agent, referrer generation
  pyyaml          config.yaml parsing

REPORTING
  reportlab       PDF generation (SimpleDocTemplate, A4, Table, Paragraph)
  openpyxl        Excel read/write support for pandas
  kaleido         Plotly chart image export (for potential PDF chart embedding)

CHARTING TYPES IMPLEMENTED
  px.bar          Horizontal and vertical bar charts (FR11)
  px.line         Line charts with markers (FR11)
  px.pie          Donut chart (hole=0.55) (FR11)
  px.scatter      Bubble scatter plot (FR11)
  px.choropleth   Geographic choropleth map (FR11)
  px.imshow       Heatmap via image plot (FR11, FR12)
  go.Scatter      Area chart (fill="tozeroy"), multi-trace line
  go.Bar          Multi-series bar with barmode stack/group
  go.Funnel       Conversion funnel (FR11)

requirements.txt
  pandas
  numpy
  faker
  pyyaml
  streamlit
  matplotlib
  seaborn
  openpyxl
  plotly
  reportlab
  kaleido


================================================================================
18. CONFIGURATION REFERENCE (config.yaml)
================================================================================

Key               Type      Description
───────────────────────────────────────────────────────────────────────────────
project.name      string    Project label used in reports
random_seed       int       Seed for all random operations (333)
date_range.start  date      First log date (2026-01-01)
date_range.end    date      Last log date (2026-05-15)
traffic.*         float     Traffic volume and variation parameters
countries.*       float     Country traffic weight (must sum to 1.0)
services.*        dict      URI, category, weight, demo_probability per service
campaigns[].name  string    Campaign label
campaigns[].start/end date  Campaign active window
campaigns[].boosted_services list  Services that receive the multiplier
campaigns[].traffic_multiplier float  Request volume boost factor
anomalies[].name  string    Anomaly label
anomalies[].type  string    suspicious_bot_spike / broken_campaign_link / viral
anomalies[].date  date      Anomaly injection date
anomalies[].uri   string    Affected URI
anomalies[].status_code int  HTTP status (optional override)
anomalies[].multiplier float Request volume multiplier
output.*          string    File paths for each output artefact


================================================================================
19. HOW TO RUN
================================================================================

PREREQUISITES
  Python 3.10 or higher installed
  pip install -r requirements.txt

STEP 1 — Generate the dataset (if not already present)
  python generate_logs.py
  This produces all files under data/output/.

STEP 2 — Validate the dataset (optional)
  python validate_dataset.py
  Checks record count, column presence, Botswana share, bot ratio,
  and IIS format compliance.

STEP 3 — Run the dashboard
  streamlit run app_html.py --server.port 8505
  Open browser at: http://localhost:8505

STEP 4 — Log in
  Select a role from the dropdown, enter the corresponding password.
  See Section 20 for credentials.

NOTES
  - If running from OneDrive, the app copies the Excel file to a temp path
    before reading to bypass OneDrive's file-lock mechanism.
  - The live pulse section starts auto-refreshing immediately on login.
    Each 3-second tick advances one record through the dataset.
  - All filters are in the left sidebar. Changes apply to all charts and
    tables on the active dashboard immediately.
  - PDF and CSV exports are available at the bottom of each dashboard in
    the Reports & Exports section.

STREAMLIT COMMUNITY CLOUD DEPLOYMENT
  1. Push the repository to GitHub
  2. Connect to Streamlit Community Cloud (share.streamlit.io)
  3. Set main file path to: app_html.py
  4. Ensure data/output/ files are committed to the repo
  5. Deploy — no additional configuration required


================================================================================
20. DEMO CREDENTIALS
================================================================================

  Role                  Password        Access
  ─────────────────────────────────────────────────────────────────────────
  Sales Team Lead       sales123        CyberNova Pulse
  Marketing Lead        marketing123    CyberNova Reach
  Executive Management  exec123         CyberNova Horizon
  Admin / Lecturer View admin123        All three dashboards (full access)

Use "Admin / Lecturer View" with password "admin123" to evaluate all three
dashboards in a single login session.


================================================================================
21. REQUIREMENTS TRACEABILITY
================================================================================

FUNCTIONAL REQUIREMENTS
──────────────────────────────────────────────────────────────────────────────
FR   Requirement Summary                              Status   Implementation
──────────────────────────────────────────────────────────────────────────────
FR1  ≥1,000-row synthetic IIS W3C log dataset         PASS     generate_logs.py +
     Southern African IPs, realistic patterns                  config.yaml (seed 333)

FR2  ETL: parse fields, IP→country, handle errors    PASS     load_data() — Excel
     report records processed/cleaned/dropped                  copy, join, cast,
                                                               sort. Data Quality
                                                               card always visible.

FR3  EDA: univariate, bivariate, time series,        PASS     Heatmaps, trend lines,
     anomaly detection, interpretive commentary               anomaly log, insight
                                                               notes on all charts

FR4  Four behavioural tiers: High-intent,            PASS     segment column in
     Product-curious, General browser, Bot                    enriched CSV; filter
     with volumes per country                                  sidebar; segment charts

FR5  Real-time feed — detects new entries,           PASS     @st.fragment(run_every=3)
     refreshes metrics without manual reload                   ring buffer, 300 records

FR6  Geographic demand: ranked bar + choropleth,     PASS     px.choropleth, country
     top 5 markets, underperforming regions                    bar charts, hotzones
                                                               panel, SADC flags

FR7  Service demand ranking; AI Cyber Assistant       PASS     Dedicated section:
     as standalone flagship KPI with trend                     "FLAGSHIP PRODUCT —
                                                               AI CYBER ASSISTANT"
                                                               with KPI card + chart

FR8  Three-tab dashboard — Sales, Marketing,         PASS     CyberNova Pulse,
     Management with role-appropriate content                  Reach, Horizon tabs
                                                               with distinct content

FR9  Sidebar filtering: date, country, service,      PASS     render_sidebar() with
     HTTP status — all visuals update reactively               date_input, multiselect
                                                               for country/service/
                                                               status/segment, toggle

FR10 Warm lead tracking: /scheduledemo.php +         PASS     is_warm_lead bool,
     /event.php — count, country split, trend,                 dedicated KPI cards,
     rate as % of total                                        country charts, weekly
                                                               trend line, rate %

FR11 Minimum five chart types with titles,           PASS     7 distinct types: bar,
     labels, legends, annotations                             line/area, donut, scatter,
                                                               choropleth, heatmap,
                                                               funnel

FR12 Descriptive stats per country/service/time:     PASS     mean/median/std in
     mean, median, std, totals. Correlation of                 service-level and
     time-of-day vs service type                               country-level tables;
                                                               hour × service heatmap
                                                               (visual correlation)

NON-FUNCTIONAL REQUIREMENTS
──────────────────────────────────────────────────────────────────────────────
NFR  Requirement Summary                              Status   Implementation
──────────────────────────────────────────────────────────────────────────────
NFR1 Dashboard loads ≤3s; filter ≤1s                 LIKELY   @st.cache_data,
                                                     PASS     @st.cache_resource,
                                                               temp-file copy pattern

NFR2 IIS W3C format compliance; ≥30% Botswana;       PASS     Botswana weight = 32%
     realistic SADC proportions                               in config.yaml;
                                                               validate_dataset.py

NFR3 Fixed random seed; full reproducibility         PASS     random_seed: 333 in
                                                               config.yaml

NFR4 Consistent UI ≥11pt; role-appropriate           PASS     Design token system;
     information density                                       Management: KPI-focused;
                                                               Sales/Marketing: detailed

NFR5 Modular codebase; separate modules;             PASS     5 separate modules;
     inline documentation; monthly re-execution               render/calculate/
                                                               story functions

NFR6 Handles ≤50,000 log entries without             LIKELY   @st.cache_data +
     restructuring                                   PASS     standard pandas ops

NFR7 Deployable locally or via Streamlit Cloud;      PASS     requirements.txt,
     no proprietary BI platforms                              open-source only

NFR8 All data synthetic; no real personal data;      PASS     Methodology note +
     documented to professional standards                      disclaimer on all pages


================================================================================
22. KNOWN LIMITATIONS & CONSTRAINTS
================================================================================

1. SYNTHETIC DATA ONLY
   No real CyberNova server logs were available. All data is generated by
   generate_logs.py using Faker. Patterns are realistic but not empirical.

2. STATIC IP-TO-COUNTRY RESOLUTION
   IP-to-country resolution uses a static lookup built into the generator,
   not a live geolocation API. This is intentional — no external API
   budget or access was allocated (Constraint 2 in SRS).

3. SOLE ANALYST
   All phases (generation, analysis, development, testing, documentation)
   were carried out by a single analyst with no team support (Constraint 4).

4. FORECAST MODEL IS PLANNING-LEVEL ONLY
   numpy.polyfit linear regression is interpretable and appropriate for the
   dataset size (~4.5 months). It is not a production forecast model.
   ARIMA and Prophet were evaluated and excluded due to insufficient history
   for seasonal fitting and the interpretability requirement.

5. LIVE FEED IS REPLAY, NOT REAL-TIME INGESTION
   The live section replays stored records at 3-second intervals. It
   simulates real-time monitoring but does not connect to a live data source.

6. ONEDRIVE FILE LOCKING
   Running from a OneDrive-synced directory can cause Excel read errors due
   to OneDrive's file locking. The temp-file copy workaround in load_data()
   handles this but adds a small latency.

7. KALEIDO REQUIREMENT
   kaleido is listed in requirements.txt for potential Plotly chart image
   export. If PDF chart embedding is not needed, this dependency can be
   removed.

8. BROWSER COMPATIBILITY
   The dashboard uses modern CSS (gap, flex, :has() selector for sidebar).
   Best viewed in Chrome or Edge. Firefox has partial :has() support.

9. STREAMLIT VERSION
   The ETL diagram uses st.html() which requires Streamlit ≥1.31. A
   fallback to st.markdown(unsafe_allow_html=True) is included for older
   installs.


================================================================================
23. GLOSSARY
================================================================================

AI Cyber Assistant   CyberNova's flagship product — an AI-powered cybersecurity
                     advisory tool. Tracked as a standalone KPI across all
                     three dashboards.

Anomaly              A synthetic data event representing abnormal traffic
                     (bot spike, 404 campaign link, viral traffic burst).
                     Flagged by is_anomaly = True.

CRISP-DM             Cross-Industry Standard Process for Data Mining. The
                     6-phase methodology (Business Understanding → Data
                     Understanding → Data Preparation → Modelling → Evaluation
                     → Deployment) governing this project's lifecycle.

fdf                  Filtered DataFrame — the result of apply_filters() on
                     the cached full DataFrame. Used by all render functions.

Fragment             Streamlit's @st.fragment(run_every=N) decorator that
                     re-renders a section of the page independently of the
                     main script, enabling the live feed without full reruns.

High-intent          Behavioural segment: sessions containing demo or event
                     signup requests. The strongest purchase-intent signal.

IIS W3C Extended     Microsoft Internet Information Services web server log
                     format: date, time, ip, method, uri, status, bytes,
                     user_agent, referrer fields.

KPI                  Key Performance Indicator — a single summarised business
                     metric shown in a compact card at the top of each dashboard.

SADC                 Southern African Development Community — the 10-country
                     regional bloc targeted by CyberNova's commercial strategy.

Ring Buffer          A fixed-size list (300 records) where new items are
                     prepended and items beyond the limit are discarded.
                     Used by the live ticker to maintain a rolling window.

Warm Lead            A website visitor who performed a high-intent action
                     (schedule demo: /scheduledemo.php or event signup:
                     /event.php). Tracked by is_warm_lead = True.

W3C                  World Wide Web Consortium — the standards body that
                     defined the Extended Log Format used as the IIS log schema.


================================================================================
END OF DOCUMENTATION
CyberNova Analytics Ltd — BI Portal  |  CET333 Product Development
Author: Seipone Talama Sebina  |  BSc (Hons) Business Intelligence & Data Analytics
================================================================================
