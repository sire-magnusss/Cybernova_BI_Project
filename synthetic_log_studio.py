"""
CyberNova Synthetic Log Studio

A premium Streamlit interface that lets a client generate synthetic CyberNova web server logs.

Run:
    streamlit run synthetic_log_studio.py
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
import tempfile
import yaml

import pandas as pd
import plotly.express as px
import streamlit as st

from generate_logs import generate_dataset


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CyberNova Synthetic Log Studio",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME CSS
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --navy: #0B1E3D;
        --dark-blue: #102A43;
        --electric-blue: #2563FF;
        --cyan: #16B8C7;
        --green: #10B981;
        --amber: #F59E0B;
        --light-grey: #F3F4F6;
        --soft-grey: #E8EAED;
        --white: #FFFFFF;
        --muted: #64748B;
        --border: #D9E2EC;
    }

    html, body, [class*="css"] {
        font-family: "Segoe UI", Inter, Arial, sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #F3F4F6 0%, #F8FAFC 45%, #EEF6FF 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1E3D 0%, #102A43 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] .stCaption {
        color: white;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #D9E2EC !important;
    }

    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] input[type="text"],
    section[data-testid="stSidebar"] .stDateInput input,
    section[data-testid="stSidebar"] .stNumberInput input {
        color: #0B1E3D !important;
        background: white !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    .hero-card {
        background: linear-gradient(135deg, #0B1E3D 0%, #1F3A5F 55%, #2563FF 120%);
        padding: 2.2rem 2.4rem;
        border-radius: 26px;
        color: white;
        box-shadow: 0 22px 55px rgba(11, 30, 61, 0.20);
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }

    .hero-card::after {
        content: "";
        position: absolute;
        right: -80px;
        top: -80px;
        width: 240px;
        height: 240px;
        border-radius: 999px;
        background: rgba(22,184,199,0.22);
    }

    .hero-title {
        font-size: 2.55rem;
        font-weight: 850;
        letter-spacing: -0.04em;
        margin-bottom: 0.35rem;
    }

    .hero-subtitle {
        color: #D9E2EC;
        font-size: 1.05rem;
        max-width: 880px;
        line-height: 1.6;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.45rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        color: white;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.14);
    }

    .section-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid #D9E2EC;
        border-radius: 22px;
        padding: 1.35rem 1.45rem;
        box-shadow: 0 12px 28px rgba(16, 42, 67, 0.08);
        margin-bottom: 1.2rem;
    }

    .section-title {
        color: #0B1E3D;
        font-size: 1.35rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .section-caption {
        color: #64748B;
        font-size: 0.95rem;
        margin-bottom: 0.8rem;
    }

    .metric-wrap {
        background: white;
        border: 1px solid #D9E2EC;
        border-radius: 20px;
        padding: 1.2rem 1.2rem;
        box-shadow: 0 10px 26px rgba(16, 42, 67, 0.08);
        min-height: 140px;
    }

    .metric-label {
        color: #64748B;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .metric-value {
        color: #0B1E3D;
        font-size: 2rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }

    .metric-note {
        color: #10B981;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .info-box {
        background: #DBEAFE;
        color: #0B1E3D;
        border-left: 5px solid #2563FF;
        padding: 1rem 1.2rem;
        border-radius: 14px;
        margin-bottom: 1.2rem;
    }

    .success-box {
        background: #D1FAE5;
        color: #064E3B;
        border-left: 5px solid #10B981;
        padding: 1rem 1.2rem;
        border-radius: 14px;
        margin-bottom: 1.2rem;
        font-weight: 650;
    }

    .warning-box {
        background: #FEF3C7;
        color: #78350F;
        border-left: 5px solid #F59E0B;
        padding: 1rem 1.2rem;
        border-radius: 14px;
        margin-bottom: 1.2rem;
    }

    .stButton > button {
        border-radius: 14px;
        border: none;
        font-weight: 800;
        padding: 0.75rem 1.15rem;
        background: linear-gradient(135deg, #2563FF, #16B8C7);
        color: white;
        box-shadow: 0 12px 24px rgba(37, 99, 255, 0.22);
        transition: 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 32px rgba(37, 99, 255, 0.28);
        color: white;
    }

    div[data-testid="stDownloadButton"] > button {
        border-radius: 14px;
        border: 1px solid #D9E2EC;
        background: white;
        color: #0B1E3D;
        font-weight: 800;
        padding: 0.72rem 1rem;
        box-shadow: 0 8px 20px rgba(16, 42, 67, 0.08);
    }

    div[data-testid="stDownloadButton"] > button:hover {
        border-color: #2563FF;
        color: #2563FF;
    }

    .small-muted {
        color: #64748B;
        font-size: 0.86rem;
    }

    .step-pill {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        background: #DBEAFE;
        color: #2563FF;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 800;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }

    .role-chip {
        display: inline-block;
        padding: 0.42rem 0.75rem;
        background: #D1FAE5;
        color: #047857;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
        margin-right: 0.35rem;
    }

    hr {
        border: none;
        border-top: 1px solid #D9E2EC;
        margin: 1.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def build_config_from_ui() -> dict:
    """Build config dictionary from sidebar controls."""

    st.sidebar.markdown("## 🛡️ CyberNova Studio")
    st.sidebar.caption("Synthetic IIS log generator")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 1. Date Range")

    start = st.sidebar.date_input("Start date", value=date(2026, 1, 1))
    end = st.sidebar.date_input("End date", value=date(2026, 5, 15))

    st.sidebar.markdown("### 2. Traffic Behaviour")
    base_daily = st.sidebar.slider("Average daily requests", 100, 2000, 500, step=50)
    variation = st.sidebar.slider("Daily fluctuation", 0.05, 0.80, 0.35, step=0.05)
    weekend_factor = st.sidebar.slider("Weekend traffic factor", 0.10, 1.00, 0.45, step=0.05)
    monthly_growth = st.sidebar.slider("Monthly growth rate", 0.00, 0.25, 0.08, step=0.01)

    st.sidebar.markdown("### 3. Bot Traffic")
    bot_min = st.sidebar.slider("Minimum bot ratio", 0.00, 0.30, 0.08, step=0.01)
    bot_max = st.sidebar.slider("Maximum bot ratio", 0.00, 0.40, 0.12, step=0.01)

    st.sidebar.markdown("### 4. Scenario Controls")
    include_campaigns = st.sidebar.checkbox("Include campaign spikes", value=True)
    include_anomalies = st.sidebar.checkbox("Include anomaly events", value=True)
    seed = st.sidebar.number_input("Random seed", value=333, step=1)

    config = {
        "project": {
            "name": "CyberNova Analytics Ltd",
            "random_seed": int(seed),
        },
        "date_range": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        "traffic": {
            "base_daily_requests": int(base_daily),
            "daily_random_variation": float(variation),
            "weekday_factor": 1.00,
            "weekend_factor": float(weekend_factor),
            "monthly_growth_rate": float(monthly_growth),
            "mean_requests_per_session": 4.0,
            "bot_ratio_min": float(bot_min),
            "bot_ratio_max": float(bot_max),
        },
        "countries": {
            "Botswana": 0.32,
            "South Africa": 0.20,
            "Zambia": 0.12,
            "Namibia": 0.09,
            "Zimbabwe": 0.08,
            "Lesotho": 0.04,
            "Eswatini": 0.04,
            "Mozambique": 0.04,
            "Malawi": 0.04,
            "Tanzania": 0.03,
        },
        "services": {
            "AI Cyber Assistant": {
                "uri": "/ai-assistant.php",
                "category": "AI Advisory",
                "weight": 0.28,
                "demo_probability": 0.10,
            },
            "Cybersecurity Monitoring": {
                "uri": "/cybersecurity-monitoring.php",
                "category": "Cybersecurity",
                "weight": 0.22,
                "demo_probability": 0.08,
            },
            "Automated Risk Assessment": {
                "uri": "/risk-assessment.php",
                "category": "Cybersecurity",
                "weight": 0.16,
                "demo_probability": 0.07,
            },
            "Digital Transformation": {
                "uri": "/digital-transformation.php",
                "category": "Digital Transformation",
                "weight": 0.13,
                "demo_probability": 0.05,
            },
            "Predictive Maintenance": {
                "uri": "/predictive-maintenance.php",
                "category": "Infrastructure",
                "weight": 0.10,
                "demo_probability": 0.05,
            },
            "Rapid Prototyping": {
                "uri": "/prototype.php",
                "category": "Prototyping",
                "weight": 0.07,
                "demo_probability": 0.06,
            },
            "Events and Promotions": {
                "uri": "/events.php",
                "category": "Marketing",
                "weight": 0.04,
                "event_probability": 0.15,
            },
        },
        "campaigns": [],
        "anomalies": [],
        "output": {
            "raw_iis_csv": "data/output/cybernova_iis_raw_logs.csv",
            "enriched_csv": "data/output/cybernova_enriched_logs.csv",
            "excel_file": "data/output/cybernova_web_logs.xlsx",
            "summary_csv": "data/output/generation_summary.csv",
        },
    }

    if include_campaigns:
        config["campaigns"] = [
            {
                "name": "SME Cyber Risk Week",
                "start_date": "2026-02-12",
                "end_date": "2026-02-16",
                "boosted_services": ["Automated Risk Assessment", "Cybersecurity Monitoring"],
                "traffic_multiplier": 1.6,
            },
            {
                "name": "AI Cyber Assistant Launch Push",
                "start_date": "2026-03-18",
                "end_date": "2026-03-24",
                "boosted_services": ["AI Cyber Assistant"],
                "traffic_multiplier": 2.0,
            },
            {
                "name": "Government Digital Transformation Expo",
                "start_date": "2026-04-22",
                "end_date": "2026-04-26",
                "boosted_services": ["Digital Transformation", "Events and Promotions"],
                "traffic_multiplier": 1.7,
            },
        ]

    if include_anomalies:
        config["anomalies"] = [
            {
                "name": "Suspicious Prototype Bot Spike",
                "type": "suspicious_bot_spike",
                "date": "2026-03-29",
                "uri": "/prototype.php",
                "multiplier": 4.0,
            },
            {
                "name": "Broken AI Campaign Link",
                "type": "broken_campaign_link",
                "date": "2026-04-03",
                "uri": "/ai-cyber-assistant.php",
                "status_code": 404,
                "multiplier": 3.0,
            },
            {
                "name": "Viral AI Assistant Spike",
                "type": "viral_ai_assistant_spike",
                "date": "2026-05-06",
                "uri": "/ai-assistant.php",
                "multiplier": 3.5,
            },
        ]

    return config


def dataframe_to_excel(raw_df: pd.DataFrame, enriched_df: pd.DataFrame, summary_df: pd.DataFrame) -> bytes:
    """Convert generated datasets into downloadable Excel workbook."""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        raw_df.to_excel(writer, sheet_name="Raw_IIS_Logs", index=False)
        enriched_df.to_excel(writer, sheet_name="Enriched_BI_Logs", index=False)
        summary_df.to_excel(writer, sheet_name="Generation_Summary", index=False)

    return output.getvalue()


def create_download_files(raw_iis: pd.DataFrame, enriched: pd.DataFrame, summary: pd.DataFrame) -> dict:
    """Create downloadable file payloads."""
    return {
        "raw_csv": raw_iis.to_csv(index=False).encode("utf-8"),
        "enriched_csv": enriched.to_csv(index=False).encode("utf-8"),
        "summary_csv": summary.to_csv(index=False).encode("utf-8"),
        "excel": dataframe_to_excel(raw_iis, enriched, summary),
    }


def metric_card(label: str, value: str, note: str) -> None:
    """Render custom metric card."""
    st.markdown(
        f"""
        <div class="metric-wrap">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def make_line_chart(summary: pd.DataFrame):
    """Create daily request line chart."""
    chart_df = summary.copy()
    chart_df["date"] = pd.to_datetime(chart_df["date"])

    fig = px.line(
        chart_df,
        x="date",
        y="actual_requests",
        markers=True,
        title="Daily Request Volume",
    )

    fig.update_traces(line=dict(color="#2563FF", width=3), marker=dict(size=6, color="#16B8C7"))
    fig.update_layout(
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        font=dict(color="#102A43"),
        title_font=dict(size=20, color="#0B1E3D"),
        margin=dict(l=30, r=30, t=60, b=30),
        xaxis=dict(gridcolor="#E8EAED"),
        yaxis=dict(gridcolor="#E8EAED"),
    )

    return fig


def make_bar_chart(data: pd.Series, title: str, color: str = "#2563FF"):
    """Create horizontal bar chart."""
    plot_df = data.reset_index()
    plot_df.columns = ["label", "value"]

    fig = px.bar(
        plot_df.sort_values("value", ascending=True),
        x="value",
        y="label",
        orientation="h",
        title=title,
        text="value",
    )

    fig.update_traces(marker_color=color, textposition="outside")
    fig.update_layout(
        height=390,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        font=dict(color="#102A43"),
        title_font=dict(size=20, color="#0B1E3D"),
        margin=dict(l=20, r=60, t=60, b=30),
        xaxis=dict(gridcolor="#E8EAED"),
        yaxis=dict(title=None),
    )

    return fig


def make_segment_chart(enriched: pd.DataFrame):
    """Create segment distribution chart."""
    session_segments = enriched.drop_duplicates("session_id")["segment"].value_counts()

    colors = {
        "General browser": "#2563FF",
        "Product-curious": "#16B8C7",
        "Bot": "#F59E0B",
        "High-intent": "#10B981",
    }

    fig = px.pie(
        values=session_segments.values,
        names=session_segments.index,
        hole=0.55,
        title="Session Segment Mix",
        color=session_segments.index,
        color_discrete_map=colors,
    )

    fig.update_layout(
        height=390,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#102A43"),
        title_font=dict(size=20, color="#0B1E3D"),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-badge">🛡️ CyberNova Analytics Ltd · Synthetic Data Generator</div>
        <div class="hero-title">CyberNova Synthetic Log Studio</div>
        <div class="hero-subtitle">
            Generate realistic IIS-style web server logs for CyberNova’s BI dashboard prototype.
            This tool simulates SADC traffic, CyberNova product interest, warm leads, bot activity,
            campaigns, anomaly events, and enriched session-level analytics.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GUIDANCE SECTION
# ============================================================

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">How to use this generator</div>
        <div class="section-caption">
            Follow the steps below to generate a realistic dataset for the Sales, Marketing, and Management dashboards.
        </div>
        <span class="step-pill">1. Set date range</span>
        <span class="step-pill">2. Adjust traffic behaviour</span>
        <span class="step-pill">3. Keep campaigns/anomalies enabled</span>
        <span class="step-pill">4. Generate dataset</span>
        <span class="step-pill">5. Download CSV/Excel files</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="info-box">
        <strong>Recommended default scenario:</strong>
        January 1 to May 15, average 500 requests per day, 8–12% bot traffic, campaigns enabled,
        and anomalies enabled. This gives enough variation for trend analysis, segmentation,
        forecasting, and anomaly detection.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# BUILD CONFIG
# ============================================================

config = build_config_from_ui()

with st.expander("Preview current generator configuration"):
    st.code(yaml.dump(config, sort_keys=False), language="yaml")


# ============================================================
# GENERATION ACTION
# ============================================================

@st.cache_data(show_spinner=False)
def cached_generate(config_yaml: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(config_yaml)
        path = f.name
    return generate_dataset(path)


generate_clicked = st.button("Generate Synthetic Dataset", type="primary", use_container_width=True)

if generate_clicked:
    config_yaml = yaml.dump(config, sort_keys=False)
    with st.spinner("Generating synthetic CyberNova web server logs..."):
        cached_generate(config_yaml)
    st.session_state["last_config_yaml"] = config_yaml
    st.session_state["has_results"] = True

if not st.session_state.get("has_results"):
    st.markdown(
        """
        <div class="warning-box">
            Use the sidebar to review the generation settings, then click
            <strong>Generate Synthetic Dataset</strong>. The tool will create raw IIS logs,
            enriched BI logs, summary statistics, charts, and downloadable files.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    raw_iis, enriched, summary = cached_generate(st.session_state["last_config_yaml"])

    if generate_clicked:
        st.markdown(
            """
            <div class="success-box">
                Dataset generated successfully. Review the summary below, then download the raw IIS logs,
                enriched BI dataset, daily summary, or Excel workbook.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # METRICS
    # ========================================================

    total_requests = len(raw_iis)
    sessions = enriched["session_id"].nunique()
    warm_leads = int(enriched["is_warm_lead"].sum())
    bot_ratio = enriched["is_bot"].mean()
    human_sessions = enriched.loc[~enriched["is_bot"], "session_id"].nunique()
    warm_lead_rate = warm_leads / max(human_sessions, 1)

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        metric_card("Total Requests", f"{total_requests:,}", "Raw IIS-style rows")
    with c2:
        metric_card("Unique Sessions", f"{sessions:,}", "Session-based journeys")
    with c3:
        metric_card("Warm Lead Events", f"{warm_leads:,}", f"{warm_lead_rate:.1%} per human session")
    with c4:
        metric_card("Bot Request Ratio", f"{bot_ratio:.1%}", "Crawler/scanner activity")
    with c5:
        metric_card("Date Range", f"{summary['date'].min()} → {summary['date'].max()}", "Generated period")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ========================================================
    # CHARTS
    # ========================================================

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Generated Dataset Overview</div>
            <div class="section-caption">
                These charts give quick evidence that the synthetic data contains realistic variation,
                country demand, service interest, bot traffic, and audience segmentation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_col1, chart_col2 = st.columns([1.4, 1])

    with chart_col1:
        st.plotly_chart(make_line_chart(summary), use_container_width=True)

    with chart_col2:
        st.plotly_chart(make_segment_chart(enriched), use_container_width=True)

    country_col, service_col = st.columns(2)

    with country_col:
        top_countries = enriched["country"].value_counts().head(10)
        st.plotly_chart(make_bar_chart(top_countries, "Top Countries by Request Volume", "#2563FF"), use_container_width=True)

    with service_col:
        top_services = enriched["service_name"].value_counts().head(10)
        st.plotly_chart(make_bar_chart(top_services, "Top Services by Request Volume", "#16B8C7"), use_container_width=True)

    # ========================================================
    # VALIDATION SUMMARY
    # ========================================================

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Validation Notes</div>
            <div class="section-caption">
                Use this section as evidence in your Testing and Evaluation report section.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    v1, v2, v3 = st.columns(3)

    with v1:
        if 0.05 <= bot_ratio <= 0.18:
            st.success("Bot traffic ratio is realistic.")
        else:
            st.warning("Bot traffic ratio may need adjustment.")

    with v2:
        if warm_lead_rate > 0:
            st.success("Warm lead events were generated.")
        else:
            st.warning("No warm lead events generated.")

    with v3:
        if summary["campaign_name"].fillna("None").ne("None").any():
            st.success("Campaign periods are present.")
        else:
            st.warning("No campaigns included.")

    anomaly_rows = enriched[enriched["is_anomaly"] == True]

    if not anomaly_rows.empty:
        st.info(f"Anomaly records detected: {len(anomaly_rows):,}. These support the Management dashboard anomaly view.")
    else:
        st.warning("No anomaly rows detected. Enable anomalies in the sidebar for richer dashboard testing.")

    # ========================================================
    # DATA PREVIEW
    # ========================================================

    tab1, tab2, tab3 = st.tabs(["Raw IIS Logs", "Enriched BI Logs", "Generation Summary"])

    with tab1:
        st.caption("This table matches the assignment-style server log output.")
        st.dataframe(raw_iis.head(150), use_container_width=True)

    with tab2:
        st.caption("This table powers the BI dashboards with session, segment, campaign, and lead fields.")
        st.dataframe(enriched.head(150), use_container_width=True)

    with tab3:
        st.caption("This table explains daily traffic volume, campaigns, bot sessions, and anomalies.")
        st.dataframe(summary, use_container_width=True)

    # ========================================================
    # DOWNLOADS
    # ========================================================

    files = create_download_files(raw_iis, enriched, summary)

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Download Generated Files</div>
            <div class="section-caption">
                Download the raw web logs, enriched BI dataset, daily summary, or full Excel workbook.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.download_button(
            "Download Raw IIS CSV",
            data=files["raw_csv"],
            file_name="cybernova_iis_raw_logs.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_raw",
        )

    with d2:
        st.download_button(
            "Download Enriched BI CSV",
            data=files["enriched_csv"],
            file_name="cybernova_enriched_logs.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_enriched",
        )

    with d3:
        st.download_button(
            "Download Summary CSV",
            data=files["summary_csv"],
            file_name="generation_summary.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_summary",
        )

    with d4:
        st.download_button(
            "Download Excel Workbook",
            data=files["excel"],
            file_name="cybernova_web_logs.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_excel",
        )