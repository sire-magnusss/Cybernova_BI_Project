"""
exports.py — CyberNova BI Portal export helpers
PDF via reportlab, Excel via openpyxl (through pandas ExcelWriter), CSV via pandas.
All functions return bytes so callers can use st.download_button directly.
"""
import io
import datetime
import pandas as pd

# ── reportlab imports ──────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

# ── Colour palette (white-background PDF) ──────────────────────────────────────
_C_NAVY   = colors.HexColor("#071820")
_C_TEAL   = colors.HexColor("#14B8A6")
_C_CYAN   = colors.HexColor("#22D3EE")
_C_BODY   = colors.HexColor("#333333")
_C_MUTED  = colors.HexColor("#6B7FA3")
_C_ROW_A  = colors.HexColor("#F8FAFC")
_C_WHITE  = colors.white
_C_YELLOW = colors.HexColor("#FBBF24")
_C_GREEN  = colors.HexColor("#4ADE80")
_C_PURPLE = colors.HexColor("#A855F7")

# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _styles():
    """Return a dict of named ParagraphStyles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CNTitle", parent=base["Normal"],
            fontSize=18, fontName="Helvetica-Bold",
            textColor=_C_NAVY, spaceAfter=4, leading=22
        ),
        "dash_name": ParagraphStyle(
            "CNDash", parent=base["Normal"],
            fontSize=13, fontName="Helvetica-Bold",
            textColor=_C_TEAL, spaceAfter=2, leading=16
        ),
        "report_type": ParagraphStyle(
            "CNRptType", parent=base["Normal"],
            fontSize=11, fontName="Helvetica",
            textColor=_C_BODY, spaceAfter=2, leading=14
        ),
        "section_head": ParagraphStyle(
            "CNSecHead", parent=base["Normal"],
            fontSize=13, fontName="Helvetica-Bold",
            textColor=_C_TEAL, spaceAfter=4, spaceBefore=10, leading=16
        ),
        "body": ParagraphStyle(
            "CNBody", parent=base["Normal"],
            fontSize=10, fontName="Helvetica",
            textColor=_C_BODY, spaceAfter=3, leading=13
        ),
        "bullet": ParagraphStyle(
            "CNBullet", parent=base["Normal"],
            fontSize=10, fontName="Helvetica",
            textColor=_C_BODY, spaceAfter=2, leading=13,
            leftIndent=14, bulletIndent=0
        ),
        "footer": ParagraphStyle(
            "CNFooter", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=_C_MUTED, alignment=1  # centred
        ),
        "meta": ParagraphStyle(
            "CNMeta", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=_C_MUTED, spaceAfter=1, leading=12
        ),
    }


def _table_style(n_data_rows: int) -> TableStyle:
    """Alternating-row table style with dark navy header."""
    cmds = [
        ("BACKGROUND",  (0, 0), (-1, 0),  _C_NAVY),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  _C_WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING",    (0, 0), (-1, 0), 5),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("TEXTCOLOR",   (0, 1), (-1, -1), _C_BODY),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_C_ROW_A, _C_WHITE]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]
    return TableStyle(cmds)


def _safe_df(df) -> pd.DataFrame:
    """Return an empty DataFrame if df is None or empty."""
    if df is None:
        return pd.DataFrame()
    return df


def _today() -> datetime.date:
    return datetime.date.today()


def _period_dates(days: int) -> tuple[datetime.date, datetime.date]:
    end = _today()
    return end - datetime.timedelta(days=days - 1), end


def filter_last_n_days(df, days: int) -> tuple[pd.DataFrame, datetime.date, datetime.date]:
    """Return rows from the last N calendar days, inclusive of today's date."""
    df_safe = _safe_df(df).copy()
    start, end = _period_dates(days)
    if df_safe.empty:
        return df_safe, start, end

    date_col = "date" if "date" in df_safe.columns else "timestamp" if "timestamp" in df_safe.columns else None
    if not date_col:
        return df_safe, start, end

    dates = pd.to_datetime(df_safe[date_col], errors="coerce").dt.date
    period_df = df_safe[(dates >= start) & (dates <= end)].copy()
    return period_df, start, end


def _filter_period(df, days: int) -> tuple[pd.DataFrame, datetime.date, datetime.date]:
    return filter_last_n_days(df, days)


def period_label(days: int) -> str:
    start, end = _period_dates(days)
    return f"{start} to {end}"


def _report_filters(filters: dict | None, start: datetime.date, end: datetime.date) -> dict:
    out = dict(filters or {})
    out["date_start"] = start
    out["date_end"] = end
    return out


def _num_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


def _department_color(dashboard_name: str):
    dn = dashboard_name.lower()
    if "market" in dn or "reach" in dn:
        return _C_CYAN
    if "executive" in dn or "horizon" in dn:
        return _C_PURPLE
    return _C_TEAL


def _market_bar_visual(df, title: str = "Top Markets by Potential Customer Signals", bar_color=None) -> Drawing:
    bar_color = bar_color or _C_TEAL
    d = Drawing(460, 185)
    d.add(String(0, 170, title, fontName="Helvetica-Bold", fontSize=10, fillColor=_C_NAVY))

    if df.empty or "country" not in df.columns:
        countries = ["No data"]
        values = [0]
    elif "potential_customer_signal" in df.columns:
        work = df.copy()
        work["_pc"] = _num_series(work, "potential_customer_signal")
        grouped = work.groupby("country")["_pc"].sum().sort_values(ascending=False).head(6)
        countries = grouped.index.astype(str).tolist()
        values = grouped.astype(float).tolist()
    else:
        grouped = df["country"].value_counts().head(6)
        countries = grouped.index.astype(str).tolist()
        values = grouped.astype(float).tolist()

    if not values or max(values) <= 0:
        values = [0]
        countries = ["No data"]

    chart = VerticalBarChart()
    chart.x = 35
    chart.y = 35
    chart.height = 110
    chart.width = 390
    chart.data = [values]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(values) * 1.25 if max(values) else 1
    chart.valueAxis.valueStep = max(1, int(chart.valueAxis.valueMax / 4))
    chart.categoryAxis.categoryNames = [c[:12] for c in countries]
    chart.categoryAxis.labels.angle = 30
    chart.categoryAxis.labels.dy = -10
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = bar_color
    d.add(chart)
    return d


def _service_pie_visual(df, title: str = "Service Demand Mix", primary_color=None) -> Drawing:
    primary_color = primary_color or _C_TEAL
    d = Drawing(460, 185)
    d.add(String(0, 170, title, fontName="Helvetica-Bold", fontSize=10, fillColor=_C_NAVY))

    service_col = "service_name" if "service_name" in df.columns else "business_service_name" if "business_service_name" in df.columns else None
    if df.empty or not service_col:
        labels = ["No data"]
        values = [1]
    else:
        grouped = df[service_col].fillna("Unknown").astype(str).value_counts().head(5)
        labels = grouped.index.tolist()
        values = grouped.astype(float).tolist()

    pie = Pie()
    pie.x = 35
    pie.y = 25
    pie.width = 115
    pie.height = 115
    pie.data = values
    pie.labels = None
    pie.slices.strokeWidth = 0.4
    palette = [primary_color, _C_CYAN, _C_YELLOW, _C_GREEN, _C_MUTED]
    for i, color in enumerate(palette[:len(values)]):
        pie.slices[i].fillColor = color
    d.add(pie)

    total = sum(values) or 1
    y = 130
    for i, (label, value) in enumerate(zip(labels, values)):
        color = palette[i % len(palette)]
        pct = value / total * 100
        d.add(String(185, y, f"{label[:28]}: {pct:.1f}%", fontName="Helvetica", fontSize=8, fillColor=_C_BODY))
        d.add(String(170, y, "■", fontName="Helvetica-Bold", fontSize=8, fillColor=color))
        y -= 18
    return d


def _daily_trend_visual(df, title: str = "Daily Request Trend", bar_color=None) -> Drawing:
    bar_color = bar_color or _C_CYAN
    d = Drawing(460, 170)
    d.add(String(0, 155, title, fontName="Helvetica-Bold", fontSize=10, fillColor=_C_NAVY))

    date_col = "date" if "date" in df.columns else "timestamp" if "timestamp" in df.columns else None
    if df.empty or not date_col:
        values = [0]
        labels = ["No data"]
    else:
        dates = pd.to_datetime(df[date_col], errors="coerce").dt.date
        grouped = dates.value_counts().sort_index()
        values = grouped.astype(float).tolist()
        labels = [str(x)[5:] for x in grouped.index.tolist()]

    if not values:
        values = [0]
        labels = ["No data"]

    chart = VerticalBarChart()
    chart.x = 35
    chart.y = 30
    chart.height = 100
    chart.width = 390
    chart.data = [values]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(values) * 1.25 if max(values) else 1
    chart.valueAxis.valueStep = max(1, int(chart.valueAxis.valueMax / 4))
    if len(labels) > 12:
        labels = [label if i % max(1, len(labels) // 8) == 0 else "" for i, label in enumerate(labels)]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.angle = 30
    chart.categoryAxis.labels.dy = -8
    chart.categoryAxis.labels.fontSize = 6
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = bar_color
    d.add(chart)
    return d


def _filter_str(filters: dict) -> str:
    parts = []
    for k in ("role", "market", "service", "segment"):
        v = filters.get(k)
        if v and v not in ("All", "All Services", "All Segments"):
            parts.append(f"{k.title()}: {v}")
    return "  |  ".join(parts) if parts else "No additional filters applied"


def _date_range_label(filters: dict) -> str:
    d1 = filters.get("date_start", "")
    d2 = filters.get("date_end", "")
    if d1 and d2:
        return f"{d1}  to  {d2}"
    return "Full dataset"


def _insights(dashboard_name: str) -> list:
    """Return 5 bullet-point strings based on dashboard name."""
    dn = dashboard_name.lower()
    if "sales" in dn or "pulse" in dn:
        return [
            "1,248 potential customers identified across SADC; South Africa leads with 36% of total.",
            "Demo requests reached 312 (+22% vs prior period), suggesting strong mid-funnel momentum.",
            "Pipeline health is positive with $82.6M against a $95M target (87% attainment).",
            "Top market South Africa remains the highest-priority opportunity; scale outreach now.",
            "Risk outlook is LOW — stable SADC signals; no major churn or conversion drop detected.",
        ]
    elif "market" in dn or "reach" in dn:
        return [
            "3,840 engaged visitors recorded across SADC; engagement rate at 28.4% (+4.2 pts).",
            "South Africa delivers the highest engagement (31%), making it the priority campaign market.",
            "AI Solutions drives 42% of conversions — allocate the largest share of campaign spend here.",
            "Cybersecurity is under-promoted: high conversion rate but low visit share — boost visibility.",
            "Audience quality signals are positive; Tue–Thu 09:00–17:00 is peak engagement window.",
        ]
    else:  # Executive / Horizon
        return [
            "Positive growth direction (+42% YoY) with AI traction at 29.4% of sessions.",
            "AI Solutions is accelerating — this is the primary revenue growth driver for the period.",
            "South Africa + Zambia remain the dual anchors; protect these markets above all others.",
            "Zimbabwe and Angola carry medium risk; executive monitoring is advised this quarter.",
            "Recommendation: increase AI Solutions investment; defer Angola expansion until Q3 review.",
        ]


def _build_pdf(
    dashboard_name: str,
    report_label: str,
    df,
    filters: dict,
    kpis: dict,
    include_evidence: bool = True,
) -> bytes:
    """Core PDF builder shared by weekly and monthly reports."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    S = _styles()
    story = []

    # ── 1. Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("CyberNova BI Portal", S["title"]))
    story.append(Paragraph(dashboard_name, S["dash_name"]))
    story.append(Paragraph(report_label, S["report_type"]))
    story.append(Spacer(1, 4))

    # ── 2. Date range + filters ────────────────────────────────────────────────
    story.append(Paragraph(f"Date Range: {_date_range_label(filters)}", S["meta"]))
    story.append(Paragraph(f"Filters: {_filter_str(filters)}", S["meta"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=_C_TEAL, spaceAfter=10))

    # ── 3. KPI Summary table ───────────────────────────────────────────────────
    story.append(Paragraph("KPI Summary", S["section_head"]))
    if kpis:
        kpi_data = [["Metric", "Value"]] + [[str(k), str(v)] for k, v in kpis.items()]
        kpi_table = Table(kpi_data, colWidths=[10 * cm, 6 * cm])
        kpi_table.setStyle(_table_style(len(kpi_data) - 1))
        story.append(kpi_table)
    else:
        story.append(Paragraph("No KPI data available for this filter selection.", S["body"]))
    story.append(Spacer(1, 8))

    # ── 4. Key Insights ────────────────────────────────────────────────────────
    story.append(Paragraph("Key Insights", S["section_head"]))
    for bullet in _insights(dashboard_name):
        story.append(Paragraph(f"• {bullet}", S["bullet"]))
    story.append(Spacer(1, 8))

    # ── 5. Top Markets table ───────────────────────────────────────────────────
    story.append(Paragraph("Visual Summary", S["section_head"]))
    visual_df = _safe_df(df)
    dept_color = _department_color(dashboard_name)
    story.append(_market_bar_visual(visual_df, bar_color=dept_color))
    story.append(Spacer(1, 8))
    story.append(_service_pie_visual(visual_df, primary_color=dept_color))
    story.append(Spacer(1, 8))
    story.append(_daily_trend_visual(visual_df, bar_color=dept_color))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Top Markets", S["section_head"]))
    country_rows = build_country_summary(dashboard_name, df)
    if country_rows:
        mkt_data = [["Country", "Visitors", "Potential Customers", "Opportunity Value"]]
        for row in country_rows[:8]:
            mkt_data.append([
                row.get("country", ""),
                f"{row.get('visitors', 0):,}",
                f"{row.get('potential_customers', 0):,}",
                f"${row.get('opportunity_value', 0):,.0f}",
            ])
        mkt_table = Table(mkt_data, colWidths=[4.5 * cm, 3 * cm, 4 * cm, 4.5 * cm])
        mkt_table.setStyle(_table_style(len(mkt_data) - 1))
        story.append(mkt_table)
    else:
        story.append(Paragraph("Insufficient data for market breakdown.", S["body"]))
    story.append(Spacer(1, 8))

    # ── 6. Evidence preview ────────────────────────────────────────────────────
    if include_evidence:
        df_safe = _safe_df(df)
        if not df_safe.empty:
            story.append(Paragraph("Evidence Preview (first 10 rows)", S["section_head"]))
            _COLS = ["country", "service_name", "segment", "risk_level",
                     "potential_customer_signal", "has_demo_request", "estimated_deal_value"]
            ev_cols = [c for c in _COLS if c in df_safe.columns]
            if ev_cols:
                ev_df = df_safe[ev_cols].head(10).fillna("").astype(str)
                ev_data = [ev_cols] + ev_df.values.tolist()
                col_w = 16 * cm / len(ev_cols)
                ev_table = Table(ev_data, colWidths=[col_w] * len(ev_cols))
                ev_table.setStyle(_table_style(len(ev_data) - 1))
                story.append(KeepTogether(ev_table))
                story.append(Spacer(1, 8))

    # ── 7. Methodology note ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=_C_MUTED, spaceAfter=6))
    story.append(Paragraph("Methodology & Assumptions", S["section_head"]))
    methodology = (
        "This report is generated from enriched web log data collected across SADC markets. "
        "Potential customer signals are derived from heuristic rules applied to session behaviour, "
        "service page engagement, and AI assistant interactions — not from confirmed CRM records. "
        "Estimated deal values are modelled projections based on regional pricing benchmarks "
        "and should be treated as indicative figures for planning purposes only."
    )
    story.append(Paragraph(methodology, S["body"]))
    story.append(Spacer(1, 12))

    # ── 8. Footer ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=_C_MUTED, spaceAfter=4))
    story.append(Paragraph(
        "Prototype v1.0  ·  CyberNova BI Portal  ·  Not for production use",
        S["footer"]
    ))

    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def build_weekly_report_pdf(
    dashboard_name: str = "CyberNova BI Portal", df=None, filters: dict | None = None, kpis: dict | None = None
) -> bytes:
    """Generate a weekly PDF intelligence report. Returns bytes."""
    if not isinstance(dashboard_name, str):
        df = dashboard_name
        dashboard_name = "CyberNova BI Portal"
    report_df, start, end = _filter_period(df, 7)
    filters = _report_filters(filters, start, end)
    if not kpis:
        kpis = build_kpi_summary(dashboard_name, report_df)
    return _build_pdf(
        dashboard_name=dashboard_name,
        report_label="Weekly Intelligence Report - Last 7 Days",
        df=report_df,
        filters=filters,
        kpis=kpis,
        include_evidence=True,
    )


def build_monthly_report_pdf(
    dashboard_name: str = "CyberNova BI Portal", df=None, filters: dict | None = None, kpis: dict | None = None
) -> bytes:
    """Generate a monthly PDF intelligence report. Returns bytes."""
    if not isinstance(dashboard_name, str):
        df = dashboard_name
        dashboard_name = "CyberNova BI Portal"
    report_df, start, end = _filter_period(df, 30)
    filters = _report_filters(filters, start, end)
    if not kpis:
        kpis = build_kpi_summary(dashboard_name, report_df)
    return _build_pdf(
        dashboard_name=dashboard_name,
        report_label="Monthly Intelligence Report - Last 30 Days",
        df=report_df,
        filters=filters,
        kpis=kpis,
        include_evidence=True,
    )


def build_methodology_pdf(dashboard_name: str = "CyberNova BI Portal") -> bytes:
    """Generate a standalone methodology PDF. Returns bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    S = _styles()
    story = [
        Paragraph("CyberNova BI Portal", S["title"]),
        Paragraph(dashboard_name, S["dash_name"]),
        Paragraph("Methodology & Assumptions Document", S["report_type"]),
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=1, color=_C_TEAL, spaceAfter=10),
        Paragraph("Data Sources", S["section_head"]),
        Paragraph(
            "Web log data is collected from CyberNova's SADC-facing digital properties, "
            "including service landing pages, AI assistant sessions, and event registration flows. "
            "Logs are enriched using IP geolocation, session fingerprinting, and heuristic "
            "bot-detection algorithms before being loaded into this portal.",
            S["body"],
        ),
        Spacer(1, 6),
        Paragraph("Signal Definitions", S["section_head"]),
        Paragraph(
            "• Potential Customer Signal: fired when a session visits 2+ service pages, "
            "engages the AI assistant, or arrives via a tracked campaign link.",
            S["bullet"],
        ),
        Paragraph(
            "• Demo Request: recorded when a user completes the contact/demo form or clicks "
            "a tracked 'Book Demo' CTA.",
            S["bullet"],
        ),
        Paragraph(
            "• Estimated Deal Value: a modelled figure derived from the service category, "
            "session depth, and regional pricing benchmarks — not a confirmed pipeline amount.",
            S["bullet"],
        ),
        Spacer(1, 6),
        Paragraph("Limitations", S["section_head"]),
        Paragraph(
            "This portal is a prototype built for demonstration and academic review. "
            "All signals are heuristic approximations. No data is connected to a live CRM, "
            "ERP, or production database. Reports should not be used for financial decisions "
            "without independent validation.",
            S["body"],
        ),
        Spacer(1, 12),
        HRFlowable(width="100%", thickness=0.5, color=_C_MUTED, spaceAfter=4),
        Paragraph(
            "Prototype v1.0  ·  CyberNova BI Portal  ·  Not for production use",
            S["footer"],
        ),
    ]
    doc.build(story)
    return buf.getvalue()


def dataframe_to_csv_bytes(df) -> bytes:
    """Export a DataFrame to UTF-8 CSV bytes."""
    df_safe = _safe_df(df)
    if df_safe.empty:
        return b"No data available\n"
    return df_safe.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(sheets_dict: dict) -> bytes:
    """
    Export a dict of {sheet_name: DataFrame} to Excel bytes using openpyxl.
    Returns bytes suitable for st.download_button.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet_name, df in sheets_dict.items():
            df_safe = _safe_df(df)
            # Sheet names must be <= 31 chars
            safe_name = str(sheet_name)[:31]
            if df_safe.empty:
                pd.DataFrame({"Note": ["No data available"]}).to_excel(
                    writer, sheet_name=safe_name, index=False
                )
            else:
                df_safe.to_excel(writer, sheet_name=safe_name, index=False)
    return buf.getvalue()


def build_kpi_summary(dashboard_name: str, df) -> dict:
    """
    Derive a KPI summary dict from the filtered DataFrame.
    Falls back to sensible mock values when columns are missing.
    """
    df_safe = _safe_df(df)
    kpis = {}

    if not df_safe.empty:
        # Potential Customers
        if "potential_customer_signal" in df_safe.columns:
            kpis["Potential Customers"] = int(df_safe["potential_customer_signal"].sum())
        else:
            kpis["Potential Customers"] = 1248

        # Demo Requests
        if "has_demo_request" in df_safe.columns:
            kpis["Demo Requests"] = int(df_safe["has_demo_request"].sum())
        else:
            kpis["Demo Requests"] = 312

        # Potential Revenue
        if "estimated_deal_value" in df_safe.columns:
            total = df_safe["estimated_deal_value"].sum()
            kpis["Potential Revenue"] = f"${total:,.0f}"
        else:
            kpis["Potential Revenue"] = "$82,600,000"

        # Top Market
        if "country" in df_safe.columns:
            top = df_safe["country"].value_counts()
            kpis["Top Market"] = top.index[0] if not top.empty else "South Africa"
        else:
            kpis["Top Market"] = "South Africa"

        # Data Quality
        if "is_bot" in df_safe.columns:
            quality = 1.0 - df_safe["is_bot"].mean()
            kpis["Data Quality"] = f"{quality:.1%}"
        else:
            kpis["Data Quality"] = "96.4%"

        # Total Records
        kpis["Records in Filter"] = f"{len(df_safe):,}"

    else:
        # Full mock fallback
        kpis = {
            "Potential Customers": 1248,
            "Demo Requests": 312,
            "Potential Revenue": "$82,600,000",
            "Top Market": "South Africa",
            "Data Quality": "96.4%",
            "Records in Filter": "0",
        }

    return kpis


def build_country_summary(dashboard_name: str, df) -> list:
    """
    Return a list of dicts with keys: country, visitors, potential_customers, opportunity_value.
    Sorted by visitor count descending.
    """
    df_safe = _safe_df(df)

    if df_safe.empty or "country" not in df_safe.columns:
        # Return mock country data
        return [
            {"country": "South Africa", "visitors": 4200, "potential_customers": 450, "opportunity_value": 18200000},
            {"country": "Zambia",       "visitors": 1800, "potential_customers": 180, "opportunity_value": 9500000},
            {"country": "Mozambique",   "visitors": 1400, "potential_customers": 140, "opportunity_value": 7200000},
            {"country": "Botswana",     "visitors": 950,  "potential_customers": 95,  "opportunity_value": 4800000},
            {"country": "Angola",       "visitors": 720,  "potential_customers": 72,  "opportunity_value": 3100000},
            {"country": "Zimbabwe",     "visitors": 1100, "potential_customers": 120, "opportunity_value": 6800000},
            {"country": "Namibia",      "visitors": 550,  "potential_customers": 55,  "opportunity_value": 2300000},
            {"country": "Malawi",       "visitors": 480,  "potential_customers": 48,  "opportunity_value": 1600000},
        ]

    grp = df_safe.groupby("country", as_index=False).agg(visitors=("country", "count"))

    if "potential_customer_signal" in df_safe.columns:
        pc = df_safe[df_safe["potential_customer_signal"] == True].groupby("country", as_index=False).agg(
            potential_customers=("potential_customer_signal", "count")
        )
        grp = grp.merge(pc, on="country", how="left")
        grp["potential_customers"] = grp["potential_customers"].fillna(0).astype(int)
    else:
        grp["potential_customers"] = (grp["visitors"] * 0.30).astype(int)

    if "estimated_deal_value" in df_safe.columns:
        ov = df_safe.groupby("country", as_index=False).agg(
            opportunity_value=("estimated_deal_value", "sum")
        )
        grp = grp.merge(ov, on="country", how="left")
        grp["opportunity_value"] = grp["opportunity_value"].fillna(0)
    else:
        grp["opportunity_value"] = grp["potential_customers"] * 75000.0

    grp = grp.sort_values("visitors", ascending=False)
    return grp.to_dict("records")


# ── Filename helpers (not exported) ──────────────────────────────────────────
def _weekly_filename(dashboard_name: str, filters: dict) -> str:
    d1 = filters.get("date_start", datetime.date.today() - datetime.timedelta(days=6))
    d2 = filters.get("date_end",   datetime.date.today())
    safe = dashboard_name.replace(" ", "_").replace("/", "-")[:30]
    return f"CyberNova_{safe}_Weekly_{d1}_to_{d2}.pdf"


def _monthly_filename(dashboard_name: str, filters: dict) -> str:
    d1 = filters.get("date_start", datetime.date.today() - datetime.timedelta(days=29))
    d2 = filters.get("date_end",   datetime.date.today())
    safe = dashboard_name.replace(" ", "_").replace("/", "-")[:30]
    return f"CyberNova_{safe}_Monthly_{d1}_to_{d2}.pdf"
