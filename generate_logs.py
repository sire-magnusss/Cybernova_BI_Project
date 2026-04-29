"""
CyberNova Analytics Ltd
Synthetic IIS Web Server Log Generator

This script generates:
1. Raw IIS-style web server logs
2. Enriched BI-ready web logs
3. Excel workbook with all generated sheets
4. Daily generation summary

Run:
    python generate_logs.py
"""

from __future__ import annotations

import hashlib
import os
import random
from datetime import datetime, date, time, timedelta
from typing import Any

import numpy as np
import pandas as pd
import yaml


# ============================================================
# BASIC UTILITIES
# ============================================================

def load_config(path: str = "config.yaml") -> dict[str, Any]:
    """Load YAML configuration file."""
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def ensure_output_folder(filepath: str) -> None:
    """Create output folder if it does not exist."""
    folder = os.path.dirname(filepath)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)


def weighted_choice(options: dict[str, float]) -> str:
    """Pick one item from a dictionary of weighted options."""
    names = list(options.keys())
    weights = np.array(list(options.values()), dtype=float)
    weights = weights / weights.sum()
    return str(np.random.choice(names, p=weights))


def status_class(status_code: int) -> str:
    """Convert HTTP status code to class."""
    if 200 <= status_code < 300:
        return "2xx"
    if 300 <= status_code < 400:
        return "3xx"
    if 400 <= status_code < 500:
        return "4xx"
    if 500 <= status_code < 600:
        return "5xx"
    return "other"


def stable_session_id(ip: str, user_agent: str, start_ts: datetime) -> str:
    """Create stable session ID from IP, user agent, and timestamp."""
    raw = f"{ip}|{user_agent}|{start_ts.isoformat()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ============================================================
# TIME GENERATION
# ============================================================

def random_time_for_human_session(day: date) -> datetime:
    """
    Generate realistic human browsing time.

    CyberNova is a B2B technology company, so most traffic happens during:
    - Morning business hours
    - Afternoon business hours
    """
    peak = np.random.choice(
        ["morning", "afternoon", "off_peak"],
        p=[0.42, 0.38, 0.20],
    )

    if peak == "morning":
        hour = int(np.clip(np.random.normal(10, 1), 7, 12))
    elif peak == "afternoon":
        hour = int(np.clip(np.random.normal(15, 1), 12, 18))
    else:
        off_peak_hours = [6, 7, 8, 18, 19, 20, 21]
        off_peak_probs = np.array([0.08, 0.12, 0.18, 0.22, 0.18, 0.14, 0.08], dtype=float)
        off_peak_probs = off_peak_probs / off_peak_probs.sum()
        hour = int(np.random.choice(off_peak_hours, p=off_peak_probs))

    minute = int(np.random.randint(0, 60))
    second = int(np.random.randint(0, 60))

    return datetime.combine(day, time(hour, minute, second))


def random_time_for_bot_session(day: date) -> datetime:
    """
    Generate bot browsing time.

    Bots are more common outside business hours.
    The probability list is normalised to avoid NumPy probability errors.
    """
    hours = list(range(24))

    probabilities = np.array([
        0.07, 0.07, 0.07, 0.06, 0.05, 0.04,
        0.03, 0.03, 0.03, 0.03, 0.03, 0.03,
        0.03, 0.03, 0.03, 0.03, 0.03, 0.04,
        0.05, 0.06, 0.07, 0.07, 0.06, 0.06,
    ], dtype=float)

    probabilities = probabilities / probabilities.sum()

    hour = int(np.random.choice(hours, p=probabilities))
    minute = int(np.random.randint(0, 60))
    second = int(np.random.randint(0, 60))

    return datetime.combine(day, time(hour, minute, second))


# ============================================================
# CYBERNOVA DOMAIN MODEL
# ============================================================

HUMAN_USER_AGENTS = [
    ("Mozilla/5.0 Chrome Windows", "Desktop", "Chrome"),
    ("Mozilla/5.0 Safari MacOS", "Desktop", "Safari"),
    ("Mozilla/5.0 Firefox Windows", "Desktop", "Firefox"),
    ("Mozilla/5.0 Chrome Android", "Mobile", "Chrome Mobile"),
    ("Mozilla/5.0 Safari iPhone", "Mobile", "Mobile Safari"),
    ("Mozilla/5.0 Edge Windows", "Desktop", "Edge"),
]

BOT_USER_AGENTS = [
    ("Googlebot/2.1", "Bot", "Search Bot"),
    ("Bingbot/2.0", "Bot", "Search Bot"),
    ("curl/8.1.0", "Bot", "Script"),
    ("python-requests/2.31", "Bot", "Script"),
    ("CyberProbeScanner/1.0", "Bot", "Suspicious Scanner"),
    ("AhrefsBot/7.0", "Bot", "SEO Bot"),
]

STATIC_ASSETS = [
    "/images/logo.png",
    "/images/events.jpg",
    "/images/cyber-assistant-banner.png",
    "/css/site.css",
    "/js/main.js",
    "/favicon.ico",
]

GENERAL_PAGES = [
    "/index.html",
    "/pricing.php",
    "/case-studies.php",
    "/resources.php",
    "/contact.php",
]

SADC_COUNTRIES = {
    "Botswana",
    "South Africa",
    "Zambia",
    "Namibia",
    "Zimbabwe",
    "Lesotho",
    "Eswatini",
    "Mozambique",
    "Malawi",
    "Tanzania",
}


def classify_sadc(country: str) -> bool:
    """Return whether country is part of the SADC target group."""
    return country in SADC_COUNTRIES


def generate_ip_for_country(country: str) -> str:
    """
    Generate synthetic country-specific IP addresses.

    These are not real geolocation mappings.
    They are designed to make the synthetic dataset analyzable by country.
    """
    country_prefixes = {
        "Botswana": "102.128",
        "South Africa": "105.245",
        "Zambia": "154.120",
        "Namibia": "196.44",
        "Zimbabwe": "197.211",
        "Lesotho": "41.203",
        "Eswatini": "102.212",
        "Mozambique": "197.249",
        "Malawi": "41.70",
        "Tanzania": "154.72",
    }

    prefix = country_prefixes.get(country, "198.51")
    third = int(np.random.randint(0, 255))
    fourth = int(np.random.randint(1, 255))

    return f"{prefix}.{third}.{fourth}"


# ============================================================
# CAMPAIGNS AND ANOMALIES
# ============================================================

def get_campaign_for_day(config: dict[str, Any], current_day: date) -> dict[str, Any] | None:
    """Return the active campaign for a given day."""
    for campaign in config.get("campaigns", []):
        start = datetime.strptime(campaign["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(campaign["end_date"], "%Y-%m-%d").date()

        if start <= current_day <= end:
            return campaign

    return None


def get_anomalies_for_day(config: dict[str, Any], current_day: date) -> list[dict[str, Any]]:
    """Return all anomalies active on a given day."""
    active_anomalies = []

    for anomaly in config.get("anomalies", []):
        anomaly_date = datetime.strptime(anomaly["date"], "%Y-%m-%d").date()

        if anomaly_date == current_day:
            active_anomalies.append(anomaly)

    return active_anomalies


# ============================================================
# TRAFFIC PLANNING
# ============================================================

def estimate_daily_request_count(config: dict[str, Any], current_day: date, day_index: int) -> int:
    """
    Estimate number of requests for a day.

    Uses:
    - Base traffic
    - Weekday/weekend effect
    - Month-on-month growth
    - Campaign boost
    - Random fluctuation
    - Anomaly boost
    """
    traffic = config["traffic"]

    base = float(traffic["base_daily_requests"])

    weekday_factor = (
        float(traffic["weekday_factor"])
        if current_day.weekday() < 5
        else float(traffic["weekend_factor"])
    )

    monthly_growth = float(traffic["monthly_growth_rate"])
    growth_factor = (1 + monthly_growth) ** (day_index / 30.0)

    variation = float(traffic["daily_random_variation"])
    random_noise = float(np.random.normal(loc=1.0, scale=variation))
    random_noise = float(np.clip(random_noise, 0.45, 1.85))

    campaign = get_campaign_for_day(config, current_day)
    campaign_multiplier = float(campaign["traffic_multiplier"]) if campaign else 1.0

    anomaly_multiplier = 1.0
    anomalies = get_anomalies_for_day(config, current_day)

    for anomaly in anomalies:
        anomaly_multiplier *= float(anomaly.get("multiplier", 1.0))

    # Cap anomaly effect so the whole dataset does not explode.
    anomaly_multiplier = min(anomaly_multiplier, 2.2)

    estimate = base * weekday_factor * growth_factor * random_noise * campaign_multiplier * anomaly_multiplier

    return max(50, int(round(estimate)))


def estimate_session_count(config: dict[str, Any], daily_requests: int) -> int:
    """Estimate number of sessions based on mean requests per session."""
    mean_requests = float(config["traffic"]["mean_requests_per_session"])
    return max(10, int(round(daily_requests / mean_requests)))


# ============================================================
# PAGE AND SESSION BEHAVIOUR
# ============================================================

def choose_service(config: dict[str, Any], campaign: dict[str, Any] | None) -> str:
    """Choose CyberNova service, boosting campaign services if a campaign is active."""
    services = config["services"]

    weights = {
        service_name: float(service_cfg["weight"])
        for service_name, service_cfg in services.items()
    }

    if campaign:
        boosted_services = set(campaign.get("boosted_services", []))

        for service_name in boosted_services:
            if service_name in weights:
                weights[service_name] *= 2.2

    return weighted_choice(weights)


def build_human_journey(config: dict[str, Any], campaign: dict[str, Any] | None) -> list[str]:
    """
    Build a realistic human visitor journey.

    Examples:
    /index.html -> /ai-assistant.php -> /scheduledemo.php
    /index.html -> /events.php -> /event.php
    /index.html -> /resources.php -> /case-studies.php
    """
    journey = ["/index.html"]

    service_name = choose_service(config, campaign)
    service_cfg = config["services"][service_name]
    service_uri = service_cfg["uri"]

    # Most B2B visitors move from homepage to a product/service page.
    if np.random.random() < 0.70:
        journey.append(service_uri)
    else:
        # Some users browse general pages only.
        if np.random.random() < 0.45:
            journey.append(str(np.random.choice(GENERAL_PAGES)))
        return journey

    # Some page loads include static assets.
    if np.random.random() < 0.22:
        journey.append(str(np.random.choice(STATIC_ASSETS)))

    # Some users compare services.
    if np.random.random() < 0.25:
        second_service_name = choose_service(config, campaign)
        second_uri = config["services"][second_service_name]["uri"]

        if second_uri != service_uri:
            journey.append(second_uri)

    # Product-specific conversion logic.
    if service_name == "Events and Promotions":
        event_probability = float(service_cfg.get("event_probability", 0.15))

        if np.random.random() < event_probability:
            journey.append("/event.php")
    else:
        demo_probability = float(service_cfg.get("demo_probability", 0.05))

        if np.random.random() < demo_probability:
            if np.random.random() < 0.30:
                journey.append("/pricing.php")

            journey.append("/scheduledemo.php")

    # Some visitors contact the company.
    if np.random.random() < 0.08:
        journey.append("/contact.php")

    return journey


def build_bot_journey(anomalies: list[dict[str, Any]]) -> list[str]:
    """
    Build bot journey.

    Bots behave differently from humans:
    - robots.txt hits
    - repeated paths
    - invalid admin paths
    - suspicious scans
    """
    if anomalies:
        anomaly = anomalies[0]
        target_uri = anomaly.get("uri", "/prototype.php")

        if anomaly["type"] in {"suspicious_bot_spike", "broken_campaign_link"}:
            repeats = int(np.random.randint(2, 8))
            return ["/robots.txt"] + [target_uri] * repeats

    bot_patterns = [
        ["/robots.txt", "/index.html"],
        ["/index.html"],
        ["/index.html", "/images/logo.png", "/css/site.css"],
        ["/pricing.php", "/contact.php"],
        ["/prototype.php"] * int(np.random.randint(1, 5)),
        ["/wp-admin.php", "/admin.php", "/login.php"],
    ]

    return list(random.choice(bot_patterns))


def service_metadata_from_uri(config: dict[str, Any], uri: str) -> tuple[str, str, str]:
    """Map URI to service name, category, and request type."""
    for service_name, service_cfg in config["services"].items():
        if service_cfg["uri"] == uri:
            request_type = service_name.lower().replace(" ", "_") + "_interest"
            return service_name, service_cfg["category"], request_type

    if uri == "/scheduledemo.php":
        return "Schedule Demo", "Lead Conversion", "demo_request"

    if uri == "/event.php":
        return "Event Signup", "Lead Conversion", "event_signup"

    if uri == "/contact.php":
        return "Contact", "Lead Conversion", "contact_request"

    if uri in STATIC_ASSETS:
        return "Static Asset", "Static Asset", "static_asset"

    if uri in ["/robots.txt", "/wp-admin.php", "/admin.php", "/login.php"]:
        return "Bot or Invalid Request", "Bot/Security", "bot_request"

    if uri in GENERAL_PAGES:
        return "General Website", "General", "general_browse"

    return "Unknown", "Unknown", "unknown_request"


def choose_status_code(is_bot: bool, uri: str, anomalies: list[dict[str, Any]]) -> int:
    """Generate realistic HTTP status code."""
    for anomaly in anomalies:
        if anomaly["type"] == "broken_campaign_link" and uri == anomaly.get("uri"):
            return int(anomaly.get("status_code", 404))

    if uri in ["/wp-admin.php", "/admin.php", "/login.php"]:
        return 404

    if uri in STATIC_ASSETS and np.random.random() < 0.35:
        return 304

    if is_bot:
        status_options = [200, 304, 404, 500]
        status_probs = np.array([0.70, 0.14, 0.15, 0.01], dtype=float)
    else:
        status_options = [200, 304, 404, 500]
        status_probs = np.array([0.83, 0.13, 0.038, 0.002], dtype=float)

    status_probs = status_probs / status_probs.sum()

    return int(np.random.choice(status_options, p=status_probs))


def generate_response_time_ms(status_code: int, is_bot: bool) -> int:
    """Generate synthetic response time."""
    if status_code >= 500:
        value = np.random.normal(1500, 350)
    elif status_code == 404:
        value = np.random.normal(280, 80)
    elif is_bot:
        value = np.random.normal(120, 35)
    else:
        value = np.random.normal(240, 90)

    return max(1, int(value))


def generate_bytes_transferred(uri: str, status_code: int) -> int:
    """Generate synthetic bytes transferred."""
    if status_code == 304:
        return 0

    if uri.endswith((".png", ".jpg", ".ico")):
        value = np.random.normal(180_000, 55_000)
    elif uri.endswith((".css", ".js")):
        value = np.random.normal(45_000, 12_000)
    else:
        value = np.random.normal(18_000, 7_000)

    return max(0, int(value))


# ============================================================
# SESSION GENERATION
# ============================================================

def generate_session(config: dict[str, Any], current_day: date, is_bot: bool) -> list[dict[str, Any]]:
    """Generate one complete visitor session as multiple request rows."""
    country = weighted_choice(config["countries"])
    ip_address = generate_ip_for_country(country)

    if is_bot:
        user_agent, device_type, browser = random.choice(BOT_USER_AGENTS)
        start_ts = random_time_for_bot_session(current_day)
    else:
        user_agent, device_type, browser = random.choice(HUMAN_USER_AGENTS)
        start_ts = random_time_for_human_session(current_day)

    session_id = stable_session_id(ip_address, user_agent, start_ts)

    campaign = get_campaign_for_day(config, current_day)
    anomalies = get_anomalies_for_day(config, current_day)

    if is_bot:
        journey = build_bot_journey(anomalies)
    else:
        journey = build_human_journey(config, campaign)

    requests = []
    timestamp = start_ts

    for step_index, uri in enumerate(journey):
        if step_index > 0:
            timestamp = timestamp + timedelta(seconds=int(np.random.randint(20, 420)))

        status_code = choose_status_code(is_bot, uri, anomalies)
        service_name, service_category, request_type = service_metadata_from_uri(config, uri)

        request = {
            "timestamp": timestamp,
            "ip_address": ip_address,
            "country": country,
            "is_sadc": classify_sadc(country),
            "method": "GET",
            "uri": uri,
            "status_code": status_code,
            "status_class": status_class(status_code),
            "user_agent": user_agent,
            "device_type": device_type,
            "browser": browser,
            "is_bot": is_bot,
            "session_id": session_id,
            "service_name": service_name,
            "service_category": service_category,
            "request_type": request_type,
            "campaign_name": campaign["name"] if campaign else "None",
            "is_campaign_period": campaign is not None,
            "is_anomaly": len(anomalies) > 0,
            "anomaly_name": anomalies[0]["name"] if anomalies else "None",
            "response_time_ms": generate_response_time_ms(status_code, is_bot),
            "bytes_transferred": generate_bytes_transferred(uri, status_code),
        }

        requests.append(request)

    return requests


# ============================================================
# ENRICHMENT
# ============================================================

def add_date_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add date/time fields for dashboard analysis."""
    df = df.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date.astype(str)
    df["time"] = df["timestamp"].dt.strftime("%H:%M:%S")
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["month"] = df["timestamp"].dt.month
    df["month_name"] = df["timestamp"].dt.month_name()
    df["week_of_year"] = df["timestamp"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["timestamp"].dt.weekday >= 5

    return df


def assign_session_level_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add session-level metrics and behavioural segmentation."""
    df = df.sort_values(["session_id", "timestamp"]).copy()

    session_summary = (
        df.groupby("session_id")
        .agg(
            first_request_ts=("timestamp", "min"),
            last_request_ts=("timestamp", "max"),
            request_count_session=("uri", "count"),
            distinct_pages_session=("uri", "nunique"),
            entry_page=("uri", "first"),
            exit_page=("uri", "last"),
            converted_to_lead=(
                "uri",
                lambda x: any(v in {"/scheduledemo.php", "/event.php", "/contact.php"} for v in x),
            ),
            has_demo=("uri", lambda x: "/scheduledemo.php" in set(x)),
            has_event=("uri", lambda x: "/event.php" in set(x)),
            has_ai_assistant=("uri", lambda x: "/ai-assistant.php" in set(x)),
            has_prototype=("uri", lambda x: "/prototype.php" in set(x)),
            session_is_bot=("is_bot", "max"),
        )
        .reset_index()
    )

    session_summary["duration_seconds"] = (
        session_summary["last_request_ts"] - session_summary["first_request_ts"]
    ).dt.total_seconds().astype(int)

    session_summary["segment"] = np.select(
        [
            session_summary["session_is_bot"].astype(bool),
            session_summary["has_demo"].astype(bool) | session_summary["has_event"].astype(bool),
            session_summary["has_ai_assistant"].astype(bool) | session_summary["has_prototype"].astype(bool),
        ],
        ["Bot", "High-intent", "Product-curious"],
        default="General browser",
    )

    session_order = (
        df.groupby(["ip_address", "session_id"])["timestamp"]
        .min()
        .reset_index()
        .sort_values(["ip_address", "timestamp"])
    )

    session_order["session_number_for_ip"] = session_order.groupby("ip_address").cumcount() + 1

    session_summary = session_summary.merge(
        session_order[["session_id", "session_number_for_ip"]],
        on="session_id",
        how="left",
    )

    df = df.merge(
        session_summary[
            [
                "session_id",
                "first_request_ts",
                "last_request_ts",
                "duration_seconds",
                "request_count_session",
                "distinct_pages_session",
                "entry_page",
                "exit_page",
                "converted_to_lead",
                "segment",
                "session_number_for_ip",
            ]
        ],
        on="session_id",
        how="left",
    )

    df["is_warm_lead"] = df["uri"].isin(["/scheduledemo.php", "/event.php", "/contact.php"])

    df["event_type"] = np.select(
        [
            df["uri"].eq("/scheduledemo.php"),
            df["uri"].eq("/event.php"),
            df["uri"].eq("/contact.php"),
            df["uri"].eq("/ai-assistant.php"),
        ],
        [
            "demo_request",
            "event_signup",
            "contact_request",
            "ai_assistant_inquiry",
        ],
        default="page_request",
    )

    return df


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_dataset(config_path: str = "config.yaml") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate raw IIS-style logs, enriched logs, and summary table."""
    config = load_config(config_path)

    seed = int(config["project"]["random_seed"])
    random.seed(seed)
    np.random.seed(seed)

    start_date = datetime.strptime(config["date_range"]["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(config["date_range"]["end_date"], "%Y-%m-%d").date()

    all_requests = []
    summary_rows = []

    current_day = start_date
    day_index = 0

    while current_day <= end_date:
        daily_request_target = estimate_daily_request_count(config, current_day, day_index)
        session_count = estimate_session_count(config, daily_request_target)

        bot_ratio = float(
            np.random.uniform(
                float(config["traffic"]["bot_ratio_min"]),
                float(config["traffic"]["bot_ratio_max"]),
            )
        )

        bot_sessions = int(round(session_count * bot_ratio))
        human_sessions = max(1, session_count - bot_sessions)

        before_count = len(all_requests)

        for _ in range(human_sessions):
            all_requests.extend(generate_session(config, current_day, is_bot=False))

        for _ in range(bot_sessions):
            all_requests.extend(generate_session(config, current_day, is_bot=True))

        after_count = len(all_requests)
        actual_requests = after_count - before_count

        campaign = get_campaign_for_day(config, current_day)
        anomalies = get_anomalies_for_day(config, current_day)

        summary_rows.append(
            {
                "date": current_day.isoformat(),
                "target_requests": daily_request_target,
                "actual_requests": actual_requests,
                "estimated_sessions": session_count,
                "human_sessions": human_sessions,
                "bot_sessions": bot_sessions,
                "bot_ratio": round(bot_sessions / max(session_count, 1), 4),
                "campaign_name": campaign["name"] if campaign else "None",
                "anomaly_count": len(anomalies),
                "anomaly_names": ", ".join(a["name"] for a in anomalies) if anomalies else "None",
            }
        )

        current_day += timedelta(days=1)
        day_index += 1

    enriched = pd.DataFrame(all_requests)

    if enriched.empty:
        raise ValueError("No data was generated. Please check config.yaml settings.")

    enriched = enriched.sort_values("timestamp").reset_index(drop=True)
    enriched.insert(0, "request_id", range(1, len(enriched) + 1))

    enriched = add_date_time_fields(enriched)
    enriched = assign_session_level_fields(enriched)

    enriched_columns = [
        "request_id",
        "timestamp",
        "date",
        "time",
        "hour",
        "day_of_week",
        "month_name",
        "week_of_year",
        "is_weekend",
        "ip_address",
        "country",
        "is_sadc",
        "method",
        "uri",
        "service_name",
        "service_category",
        "request_type",
        "status_code",
        "status_class",
        "user_agent",
        "device_type",
        "browser",
        "is_bot",
        "session_id",
        "session_number_for_ip",
        "first_request_ts",
        "last_request_ts",
        "duration_seconds",
        "request_count_session",
        "distinct_pages_session",
        "entry_page",
        "exit_page",
        "segment",
        "is_warm_lead",
        "event_type",
        "converted_to_lead",
        "campaign_name",
        "is_campaign_period",
        "is_anomaly",
        "anomaly_name",
        "response_time_ms",
        "bytes_transferred",
    ]

    enriched = enriched[enriched_columns]

    raw_iis = enriched[
        [
            "date",
            "time",
            "ip_address",
            "method",
            "uri",
            "status_code",
            "user_agent",
            "bytes_transferred",
            "response_time_ms",
        ]
    ].copy()

    summary = pd.DataFrame(summary_rows)

    return raw_iis, enriched, summary


def save_outputs(config_path: str = "config.yaml") -> None:
    """Generate and save output files."""
    config = load_config(config_path)
    output = config["output"]

    raw_iis, enriched, summary = generate_dataset(config_path)

    ensure_output_folder(output["raw_iis_csv"])
    ensure_output_folder(output["enriched_csv"])
    ensure_output_folder(output["excel_file"])
    ensure_output_folder(output["summary_csv"])

    raw_iis.to_csv(output["raw_iis_csv"], index=False)
    enriched.to_csv(output["enriched_csv"], index=False)
    summary.to_csv(output["summary_csv"], index=False)

    with pd.ExcelWriter(output["excel_file"], engine="openpyxl") as writer:
        raw_iis.to_excel(writer, sheet_name="Raw_IIS_Logs", index=False)
        enriched.to_excel(writer, sheet_name="Enriched_BI_Logs", index=False)
        summary.to_excel(writer, sheet_name="Generation_Summary", index=False)

    print()
    print("CyberNova synthetic log generation complete.")
    print("=" * 55)
    print(f"Raw IIS logs:       {output['raw_iis_csv']} | rows: {len(raw_iis):,}")
    print(f"Enriched BI logs:   {output['enriched_csv']} | rows: {len(enriched):,}")
    print(f"Excel workbook:     {output['excel_file']}")
    print(f"Generation summary: {output['summary_csv']}")

    sessions = enriched["session_id"].nunique()
    human_sessions = enriched.loc[~enriched["is_bot"], "session_id"].nunique()
    warm_leads = int(enriched["is_warm_lead"].sum())
    warm_lead_rate = warm_leads / max(human_sessions, 1)
    bot_request_ratio = enriched["is_bot"].mean()

    print()
    print("Quick validation")
    print("=" * 55)
    print(f"Unique sessions:    {sessions:,}")
    print(f"Human sessions:     {human_sessions:,}")
    print(f"Warm lead events:   {warm_leads:,}")
    print(f"Warm lead rate:     {warm_lead_rate:.2%}")
    print(f"Bot request ratio:  {bot_request_ratio:.2%}")
    print()


if __name__ == "__main__":
    save_outputs("config.yaml")