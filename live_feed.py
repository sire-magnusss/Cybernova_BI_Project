#!/usr/bin/env python3
"""
CyberNova Live Feed Generator
Simulates real-time web traffic by continuously generating synthetic log rows
and appending them to data/output/cybernova_live_feed.csv.

Run alongside the Streamlit dashboard:
    python live_feed.py

Then open the "Live Feed" tab in the BI portal to see live metrics.
Press Ctrl+C to stop.
"""
from __future__ import annotations

import hashlib
import json
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

# ── Output paths ──────────────────────────────────────────────────────────────
LIVE_CSV   = Path("data/output/cybernova_live_feed.csv")
STATS_JSON = Path("data/output/live_stats.json")

# ── Tuning knobs ──────────────────────────────────────────────────────────────
ROLLING_ROWS = 5_000   # max rows kept in the CSV (trim older entries)
TICK_SECONDS = 0.5     # seconds between each batch write
ROWS_MIN     = 2       # min rows per tick
ROWS_MAX     = 10      # max rows per tick (creates realistic traffic bursts)

# ── Realistic data pools (mirrors the enriched dataset schema) ─────────────────
_SADC = {
    "Botswana": True, "South Africa": True, "Zimbabwe": True,
    "Namibia": True,  "Zambia": True,       "Mozambique": True,
    "Malawi": True,   "Lesotho": True,      "Tanzania": True, "Eswatini": True,
}
_OTHER = {
    "Kenya": False, "Nigeria": False, "Ghana": False,
    "United Kingdom": False, "United States": False,
    "Germany": False, "France": False, "India": False, "UAE": False,
}
ALL_COUNTRIES  = {**_SADC, **_OTHER}
COUNTRY_NAMES  = list(ALL_COUNTRIES.keys())
COUNTRY_WEIGHTS = [0.11] * len(_SADC) + [0.03] * len(_OTHER)

SERVICES = [
    {"name": "General Website",          "uri": "/index.html",                    "cat": "General",               "event": "general_browse",                  "warm": False, "w": 0.25},
    {"name": "AI Cyber Assistant",        "uri": "/ai-assistant.php",              "cat": "AI Advisory",           "event": "ai_cyber_assistant_interest",     "warm": True,  "w": 0.14},
    {"name": "Cybersecurity Monitoring",  "uri": "/cybersecurity-monitoring.php",  "cat": "Security",              "event": "security_interest",               "warm": False, "w": 0.09},
    {"name": "Digital Transformation",    "uri": "/digital-transformation.php",    "cat": "Digital Transformation","event": "digital_transformation_interest", "warm": False, "w": 0.10},
    {"name": "Rapid Prototyping",         "uri": "/rapid-prototyping.php",         "cat": "Innovation",            "event": "prototype_interest",              "warm": False, "w": 0.07},
    {"name": "Automated Risk Assessment", "uri": "/automated-risk-assessment.php", "cat": "Security",              "event": "risk_assessment_interest",        "warm": False, "w": 0.07},
    {"name": "Predictive Maintenance",    "uri": "/predictive-maintenance.php",    "cat": "AI Advisory",           "event": "predictive_interest",             "warm": False, "w": 0.06},
    {"name": "Schedule Demo",             "uri": "/scheduledemo.php",              "cat": "Sales",                 "event": "demo_request",                    "warm": True,  "w": 0.09},
    {"name": "Contact",                   "uri": "/contact.php",                   "cat": "General",               "event": "contact_inquiry",                 "warm": False, "w": 0.05},
    {"name": "Static Asset",              "uri": "/assets/logo.png",               "cat": "General",               "event": "static_asset",                    "warm": False, "w": 0.04},
    {"name": "Events and Promotions",     "uri": "/events.php",                    "cat": "Marketing",             "event": "event_interest",                  "warm": False, "w": 0.04},
]
SVC_NAMES   = [s["name"] for s in SERVICES]
SVC_WEIGHTS = [s["w"]    for s in SERVICES]
SVC_MAP     = {s["name"]: s for s in SERVICES}

DEVICES = [
    ("Desktop", "Chrome"),        ("Desktop", "Edge"),         ("Desktop", "Firefox"),
    ("Desktop", "Safari"),        ("Mobile",  "Chrome Mobile"),("Mobile",  "Mobile Safari"),
    ("Bot",     "Search Bot"),    ("Bot",     "SEO Bot"),      ("Bot",     "Suspicious Scanner"),
]
DEV_WEIGHTS = [0.18, 0.14, 0.09, 0.06, 0.16, 0.12, 0.09, 0.08, 0.08]

STATUS_POOL = [
    ("2xx", 200), ("2xx", 200), ("2xx", 200), ("2xx", 200), ("2xx", 204),
    ("3xx", 304), ("3xx", 301),
    ("4xx", 404), ("4xx", 403), ("4xx", 400),
    ("5xx", 500), ("5xx", 503),
]
STATUS_WEIGHTS = [0.12, 0.12, 0.12, 0.11, 0.05, 0.07, 0.04, 0.09, 0.06, 0.04, 0.09, 0.05]

CAMPAIGNS = [
    "Government Digital Transformation Expo",
    "AI Cyber Assistant Launch Push",
    "SME Cyber Risk Week",
    "SADC Digital Summit 2026",
    None,
]
CAMPAIGN_WEIGHTS = [0.20, 0.15, 0.10, 0.10, 0.45]

# Fixed pool of IPs so sessions stay realistic
random.seed(42)
IP_POOL = [
    f"{random.choice([41, 102, 154, 197])}.{random.randint(100,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
    for _ in range(2000)
]
random.seed()


# ── Row generation ─────────────────────────────────────────────────────────────
def _make_rows(n: int, base_id: int) -> list[dict]:
    now  = datetime.now().replace(microsecond=0)
    rows = []

    for i in range(n):
        country  = random.choices(COUNTRY_NAMES, weights=COUNTRY_WEIGHTS, k=1)[0]
        is_sadc  = ALL_COUNTRIES[country]
        svc      = random.choices(SVC_NAMES, weights=SVC_WEIGHTS, k=1)[0]
        svc_info = SVC_MAP[svc]
        dev, browser = random.choices(DEVICES, weights=DEV_WEIGHTS, k=1)[0]
        is_bot   = dev == "Bot"
        sc_class, sc_code = random.choices(STATUS_POOL, weights=STATUS_WEIGHTS, k=1)[0]
        campaign = random.choices(CAMPAIGNS, weights=CAMPAIGN_WEIGHTS, k=1)[0]
        is_anom  = (not is_bot) and (random.random() < 0.04)

        segment  = (
            "Bot" if is_bot
            else "High-intent"     if svc_info["warm"]
            else "Product-curious" if random.random() < 0.35
            else "General browser"
        )
        is_warm = svc_info["warm"] and not is_bot and sc_class == "2xx"
        conv    = is_warm and random.random() < 0.30

        ip         = random.choice(IP_POOL)
        session_id = hashlib.md5(f"{ip}{now.date()}".encode()).hexdigest()

        rows.append({
            "request_id":          base_id + i,
            "timestamp":           now.strftime("%Y-%m-%d %H:%M:%S"),
            "date":                now.strftime("%Y-%m-%d"),
            "time":                now.strftime("%H:%M:%S"),
            "hour":                now.hour,
            "day_of_week":         now.strftime("%A"),
            "month_name":          now.strftime("%B"),
            "week_of_year":        now.isocalendar()[1],
            "is_weekend":          now.weekday() >= 5,
            "ip_address":          ip,
            "country":             country,
            "is_sadc":             is_sadc,
            "method":              "GET",
            "uri":                 svc_info["uri"],
            "service_name":        svc,
            "service_category":    svc_info["cat"],
            "request_type":        svc_info["event"],
            "status_code":         sc_code,
            "status_class":        sc_class,
            "user_agent":          f"Mozilla/5.0 {browser}",
            "device_type":         dev,
            "browser":             browser,
            "is_bot":              is_bot,
            "session_id":          session_id,
            "session_number_for_ip": random.randint(1, 5),
            "first_request_ts":    now.strftime("%Y-%m-%d %H:%M:%S"),
            "last_request_ts":     now.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds":    random.randint(30, 900),
            "request_count_session": random.randint(1, 12),
            "distinct_pages_session": random.randint(1, 8),
            "entry_page":          svc_info["uri"],
            "exit_page":           random.choice(["/index.html", "/contact.php", svc_info["uri"]]),
            "segment":             segment,
            "is_warm_lead":        is_warm,
            "event_type":          svc_info["event"],
            "converted_to_lead":   conv,
            "campaign_name":       campaign,
            "is_campaign_period":  campaign is not None,
            "is_anomaly":          is_anom,
            "anomaly_name":        "Traffic Spike" if is_anom else "None",
            "response_time_ms":    random.randint(2000, 8000) if is_anom else random.randint(50, 1800),
            "bytes_transferred":   random.randint(0, 50_000),
        })

    return rows


# ── Stats JSON (for optional fast reads) ──────────────────────────────────────
def _write_stats(df: pd.DataFrame) -> None:
    try:
        now     = pd.Timestamp.now()
        df_5min = df[pd.to_datetime(df["timestamp"], errors="coerce") >= now - pd.Timedelta(minutes=5)]
        stats   = {
            "as_of":           now.strftime("%Y-%m-%d %H:%M:%S"),
            "total_rows":      len(df),
            "requests_5min":   len(df_5min),
            "warm_leads_5min": int(df_5min["is_warm_lead"].sum()) if not df_5min.empty else 0,
            "top_country":     str(df["country"].value_counts().index[0]) if not df.empty else "—",
            "top_service":     str(df["service_name"].value_counts().index[0]) if not df.empty else "—",
            "bot_ratio":       float(df["is_bot"].mean()),
            "avg_response_ms": float(df["response_time_ms"].mean()),
            "anomalies":       int(df["is_anomaly"].sum()),
            "countries_active": int(df["country"].nunique()),
        }
        with open(STATS_JSON, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass


# ── CSV initialiser ───────────────────────────────────────────────────────────
_CSV_HEADER = [
    "request_id","timestamp","date","time","hour","day_of_week","month_name",
    "week_of_year","is_weekend","ip_address","country","is_sadc","method","uri",
    "service_name","service_category","request_type","status_code","status_class",
    "user_agent","device_type","browser","is_bot","session_id","session_number_for_ip",
    "first_request_ts","last_request_ts","duration_seconds","request_count_session",
    "distinct_pages_session","entry_page","exit_page","segment","is_warm_lead",
    "event_type","converted_to_lead","campaign_name","is_campaign_period",
    "is_anomaly","anomaly_name","response_time_ms","bytes_transferred",
]


def _init_csv() -> None:
    LIVE_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not LIVE_CSV.exists():
        pd.DataFrame(columns=_CSV_HEADER).to_csv(LIVE_CSV, index=False)
        print(f"  Created: {LIVE_CSV}")


# ── Main loop ─────────────────────────────────────────────────────────────────
def main() -> None:
    print("\n" + "═" * 60)
    print("  CyberNova Live Feed Generator")
    print(f"  Output : {LIVE_CSV}")
    print(f"  Tick   : every {TICK_SECONDS}s  |  {ROWS_MIN}–{ROWS_MAX} rows/tick")
    print(f"  Buffer : rolling {ROLLING_ROWS:,} rows")
    print("  Press Ctrl+C to stop.")
    print("═" * 60 + "\n")

    _init_csv()

    total_rows = 0
    row_id     = int(time.time()) % 100_000
    tick       = 0
    spinner    = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def _stop(sig, frame):
        print(f"\n\n  Stopped.  Session total: {total_rows:,} rows written.\n")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _stop)
    signal.signal(signal.SIGTERM, _stop)

    while True:
        n    = random.randint(ROWS_MIN, ROWS_MAX)
        rows = _make_rows(n, row_id)
        row_id    += n
        total_rows += n

        # Append new rows
        pd.DataFrame(rows).to_csv(LIVE_CSV, mode="a", header=False, index=False)

        # Every 20 ticks (~10 s) trim rolling window and refresh stats JSON
        if tick % 20 == 0:
            try:
                existing = pd.read_csv(LIVE_CSV)
                buf_len  = len(existing)
                if buf_len > ROLLING_ROWS:
                    existing.tail(ROLLING_ROWS).to_csv(LIVE_CSV, index=False)
                    buf_len = ROLLING_ROWS
                _write_stats(existing)
            except Exception:
                buf_len = "?"
        else:
            buf_len = "…"

        # Console ticker
        sample = rows[0]
        print(
            f"\r{spinner[tick % 10]}  tick {tick:>5}  |  +{n} rows  |"
            f"  session total: {total_rows:>6,}  |  buffer: {str(buf_len):>5}"
            f"  |  {sample['country'][:12]:<12} → {sample['service_name'][:22]:<22}"
            f"  {'[WARM]' if sample['is_warm_lead'] else '      '}"
            f"  {sample['status_class']}  {sample['response_time_ms']}ms",
            end="", flush=True,
        )

        tick += 1
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()
