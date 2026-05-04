"""
CyberNova Analytics Ltd — BI Portal  (app_final.py)
Full storytelling upgrade per claudedescription.txt.
Run:  streamlit run app_final.py --server.port 8504
"""
from __future__ import annotations
from datetime import date
from io import BytesIO
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors as rl_colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

st.set_page_config(page_title="CyberNova BI Portal", page_icon="CN",
                   layout="wide", initial_sidebar_state="expanded")

# ── Design tokens ──────────────────────────────────────────────────
NAVY      = "#0B1E3D"; DARK_BLUE = "#102A43"; BLUE  = "#2563FF"
CYAN      = "#16B8C7"; GREEN     = "#10B981";  AMBER = "#F59E0B"
RED       = "#EF4444"; LIGHT_GREY= "#F3F4F6";  SOFT_GREY = "#E8EAED"
BORDER    = "#D9E2EC"; WHITE     = "#FFFFFF";   MUTED = "#64748B"
CHART_PAL = [BLUE, CYAN, GREEN, AMBER, "#8B5CF6", RED, "#EC4899", "#14B8A6"]
DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# ── SVG icon system ────────────────────────────────────────────────
_PATHS = {
    "shield":    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "pulse":     '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "target":    '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "globe":     '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "download":  '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    "refresh":   '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
    "search":    '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "lock":      '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "file":      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    "info":      '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    "users":     '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "bar_chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "map_pin":   '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "trending":  '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "report":    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    "export":    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    "activity":  '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "alert":     '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "zap":       '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "check":     '<polyline points="20 6 9 17 4 12"/>',
}

def svg_icon(name: str, size: int = 18, color: str = "#2563FF") -> str:
    path = _PATHS.get(name, _PATHS["info"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" style="vertical-align:middle;display:inline-block;">'
            f'{path}</svg>')

# ── CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
html,body,[class*="css"]{font-family:"Segoe UI",Inter,Arial,sans-serif;}
.stApp{background:linear-gradient(135deg,#F3F4F6 0%,#F8FAFC 50%,#EEF6FF 100%);}
.block-container{padding-top:1.4rem;padding-bottom:4rem;max-width:1540px;}

/* Sidebar */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B1E3D 0%,#102A43 100%);border-right:1px solid rgba(255,255,255,0.07);}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] .stCaption{color:white;}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] .stMarkdown p{color:#D9E2EC !important;}
section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] .stDateInput input{color:#0B1E3D !important;background:white !important;}

/* Nav pills */
section[data-testid="stSidebar"] .stRadio > label{display:none !important;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"]{display:flex;flex-direction:column;gap:0.3rem;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label{
  background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:12px;
  padding:0.72rem 1rem 0.72rem 1.1rem;cursor:pointer;display:flex !important;align-items:center;
  margin:0 !important;transition:background 0.15s,border-color 0.15s;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover{background:rgba(37,99,255,0.18);border-color:rgba(37,99,255,0.4);}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child{display:none !important;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:last-child p{color:#D9E2EC !important;font-weight:600 !important;font-size:0.88rem !important;margin:0 !important;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked){background:rgba(37,99,255,0.25) !important;border-color:#2563FF !important;border-left:3px solid #2563FF !important;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) > div:last-child p{color:white !important;font-weight:800 !important;}

/* Hero */
.dash-hero{background:linear-gradient(135deg,#0B1E3D 0%,#1F3A5F 55%,#2563FF 120%);padding:1.8rem 2.2rem 1.4rem;border-radius:20px;color:white;box-shadow:0 16px 44px rgba(11,30,61,0.18);margin-bottom:0.6rem;position:relative;overflow:hidden;}
.dash-hero::after{content:"";position:absolute;right:-60px;top:-60px;width:200px;height:200px;border-radius:999px;background:rgba(22,184,199,0.16);}
.dash-hero-badge{display:inline-flex;align-items:center;gap:0.4rem;padding:0.3rem 0.7rem;border-radius:999px;background:rgba(255,255,255,0.12);color:rgba(255,255,255,0.9);font-size:0.74rem;font-weight:700;margin-bottom:0.55rem;border:1px solid rgba(255,255,255,0.15);position:relative;z-index:1;}
.dash-hero-title{font-size:1.85rem;font-weight:900;letter-spacing:-0.04em;margin-bottom:0.18rem;position:relative;z-index:1;}
.dash-hero-sub{font-size:0.88rem;color:#D9E2EC;line-height:1.6;max-width:760px;position:relative;z-index:1;}

/* KPI cards */
.kpi-card{background:white;border:1px solid #D9E2EC;border-radius:18px;padding:1.3rem 1.4rem 1.15rem;box-shadow:0 6px 22px rgba(16,42,67,0.07);min-height:148px;display:flex;flex-direction:column;justify-content:space-between;}
.kpi-label{color:#64748B;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;font-weight:800;margin-bottom:0.45rem;display:flex;align-items:center;gap:0.3rem;}
.kpi-value{color:#0B1E3D;font-size:2rem;font-weight:900;letter-spacing:-0.04em;margin-bottom:0.12rem;}
.kpi-delta{font-size:0.81rem;font-weight:700;}
.kpi-green{color:#10B981;}.kpi-amber{color:#F59E0B;}.kpi-blue{color:#2563FF;}.kpi-cyan{color:#16B8C7;}.kpi-red{color:#EF4444;}

/* Context chips */
.ctx-bar{background:white;border:1px solid #D9E2EC;border-radius:13px;padding:0.6rem 1.1rem;font-size:0.8rem;color:#0B1E3D;margin-bottom:1.2rem;box-shadow:0 3px 10px rgba(16,42,67,0.04);display:flex;flex-wrap:wrap;gap:0.4rem;align-items:center;}
.ctx-chip{display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;font-size:0.73rem;font-weight:700;background:#DBEAFE;color:#1E40AF;}
.ctx-chip-role{background:#EDE9FE;color:#5B21B6;}.ctx-chip-green{background:#D1FAE5;color:#065F46;}.ctx-chip-amber{background:#FEF3C7;color:#78350F;}

/* Section cards */
.section-card{background:rgba(255,255,255,0.95);border:1px solid #D9E2EC;border-radius:18px;padding:1.3rem 1.4rem 1.1rem;box-shadow:0 8px 24px rgba(16,42,67,0.06);margin-bottom:1rem;}
.section-title{color:#0B1E3D;font-size:1.12rem;font-weight:800;margin-bottom:0.12rem;display:flex;align-items:center;gap:0.35rem;}
.section-caption{color:#64748B;font-size:0.87rem;margin-top:0.06rem;}

/* Insight card */
.insight-card{background:linear-gradient(135deg,#EEF6FF 0%,#E0F2FE 100%);border:1px solid #BFDBFE;border-radius:18px;padding:1.3rem 1.5rem;margin-bottom:1rem;}
.insight-title{font-size:1rem;font-weight:800;color:#1E40AF;margin-bottom:0.7rem;display:flex;align-items:center;gap:0.35rem;}
.insight-bullet{display:flex;align-items:flex-start;gap:0.55rem;padding:0.38rem 0;border-bottom:1px solid rgba(37,99,255,0.1);font-size:0.86rem;color:#1E3A5F;line-height:1.55;}
.insight-bullet:last-child{border-bottom:none;}
.insight-dot{width:7px;height:7px;border-radius:50%;background:#2563FF;flex-shrink:0;margin-top:0.4rem;}

/* Chart insight */
.chart-insight{background:#F0F7FF;border-radius:10px;padding:0.55rem 0.85rem;font-size:0.81rem;color:#1E40AF;margin-top:0.5rem;line-height:1.5;}

/* Story panel */
.story-panel{background:white;border:1px solid #D9E2EC;border-radius:18px;padding:1.4rem 1.5rem;box-shadow:0 8px 24px rgba(16,42,67,0.06);margin-bottom:1rem;}
.story-panel-blue{border-top:4px solid #2563FF;}.story-panel-cyan{border-top:4px solid #16B8C7;}.story-panel-green{border-top:4px solid #10B981;}.story-panel-amber{border-top:4px solid #F59E0B;}
.story-title{font-size:1.05rem;font-weight:800;color:#0B1E3D;margin-bottom:0.22rem;display:flex;align-items:center;gap:0.35rem;}
.story-subtitle{color:#64748B;font-size:0.84rem;margin-bottom:0.9rem;}
.story-bullet{display:flex;align-items:flex-start;gap:0.5rem;padding:0.35rem 0;border-bottom:1px solid #F3F4F6;font-size:0.84rem;color:#0B1E3D;line-height:1.55;}
.story-bullet:last-child{border-bottom:none;}
.story-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;margin-top:0.42rem;}
.story-dot-blue{background:#2563FF;}.story-dot-cyan{background:#16B8C7;}.story-dot-green{background:#10B981;}.story-dot-amber{background:#F59E0B;}
.story-action-chip{display:inline-flex;align-items:center;gap:0.3rem;padding:0.32rem 0.85rem;border-radius:999px;font-size:0.78rem;font-weight:700;margin-top:0.8rem;}
.story-action-blue{background:#DBEAFE;color:#1E40AF;border:1px solid #93C5FD;}.story-action-cyan{background:#CFFAFE;color:#0E7490;border:1px solid #67E8F9;}.story-action-green{background:#D1FAE5;color:#065F46;border:1px solid #6EE7B7;}.story-action-amber{background:#FEF3C7;color:#78350F;border:1px solid #FCD34D;}

/* Story flow strip */
.story-strip{display:flex;align-items:center;background:white;border:1px solid #D9E2EC;border-radius:12px;padding:0.42rem 0.9rem;margin-bottom:1rem;overflow-x:auto;white-space:nowrap;box-shadow:0 3px 10px rgba(16,42,67,0.04);gap:0;}
.strip-stage{font-size:0.69rem;font-weight:700;color:#94A3B8;padding:0.18rem 0.52rem;border-radius:999px;}
.strip-active-blue{background:#DBEAFE;color:#1E40AF;}.strip-active-cyan{background:#CFFAFE;color:#0E7490;}.strip-active-green{background:#D1FAE5;color:#065F46;}
.strip-arrow{color:#D9E2EC;font-size:0.69rem;padding:0 0.12rem;flex-shrink:0;}

/* Section label */
.section-label{font-size:0.63rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:0.14em;margin:1.1rem 0 0.38rem;display:flex;align-items:center;gap:0.3rem;}

/* Action table card */
.action-table-card{background:white;border:1px solid #D9E2EC;border-radius:18px;padding:1.3rem 1.4rem 0.9rem;box-shadow:0 8px 24px rgba(16,42,67,0.06);margin-bottom:0.7rem;}

/* Live feed */
.feed-container{background:white;border-radius:14px;padding:0.4rem 0.2rem;}
.feed-item{display:flex;gap:0.8rem;padding:0.7rem 0.5rem;border-bottom:1px solid #F3F4F6;align-items:flex-start;}
.feed-item:last-child{border-bottom:none;}
.feed-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;margin-top:0.32rem;}
.feed-dot-green{background:#10B981;}.feed-dot-blue{background:#2563FF;}.feed-dot-amber{background:#F59E0B;}
.feed-time{color:#94A3B8;font-size:0.7rem;font-weight:600;margin-bottom:0.08rem;}
.feed-main{color:#0B1E3D;font-size:0.82rem;font-weight:700;}
.feed-meta{color:#64748B;font-size:0.73rem;margin-top:0.06rem;}
.feed-warm{display:inline-block;background:#D1FAE5;color:#065F46;font-size:0.66rem;font-weight:800;padding:0.08rem 0.4rem;border-radius:999px;margin-left:0.3rem;}
.feed-anom{display:inline-block;background:#FEF3C7;color:#78350F;font-size:0.65rem;font-weight:800;padding:0.08rem 0.35rem;border-radius:999px;margin-left:0.3rem;}
.live-badge{display:inline-flex;align-items:center;gap:0.38rem;padding:0.28rem 0.7rem;border-radius:999px;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.4);color:#10B981;font-size:0.75rem;font-weight:900;letter-spacing:0.08em;}
.live-dot{width:7px;height:7px;background:#10B981;border-radius:50%;display:inline-block;animation:pulse-dot 1.4s ease-in-out infinite;}
@keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.35;transform:scale(0.6);}}

/* Report card */
.report-card{background:white;border:1px solid #D9E2EC;border-radius:18px;padding:1.4rem 1.5rem;box-shadow:0 8px 22px rgba(16,42,67,0.07);margin-top:1rem;}
.report-card-title{font-size:1.05rem;font-weight:800;color:#0B1E3D;margin-bottom:0.9rem;display:flex;align-items:center;gap:0.35rem;}

/* Restricted / empty */
.restricted-card{background:white;border:1px solid #FECACA;border-radius:20px;padding:3rem 2rem;text-align:center;box-shadow:0 8px 24px rgba(16,42,67,0.08);margin-top:2rem;}
.restricted-title{font-size:1.35rem;font-weight:800;color:#0B1E3D;margin:0.7rem 0 0.5rem;}
.restricted-text{color:#64748B;font-size:0.93rem;}
.empty-card{background:white;border:1px dashed #D9E2EC;border-radius:18px;padding:2.8rem 2rem;text-align:center;margin-top:0.8rem;}
.empty-title{font-size:1.1rem;font-weight:800;color:#0B1E3D;margin:0.5rem 0 0.35rem;}
.empty-text{color:#64748B;font-size:0.88rem;}

/* Role badge */
.role-badge{display:inline-block;padding:0.35rem 0.8rem;border-radius:999px;font-size:0.8rem;font-weight:800;background:rgba(37,99,255,0.18);color:#93C5FD;border:1px solid rgba(37,99,255,0.3);}

/* Demo credentials */
.cred-bar{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);border-radius:12px;padding:0.75rem 0.9rem;margin-bottom:0.4rem;}
.cred-bar-title{font-size:0.66rem;font-weight:800;color:#94A3B8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.45rem;}
.cred-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:0.28rem;}
.cred-role{font-size:0.71rem;color:#CBD5E1;font-weight:600;}
.cred-pwd{font-size:0.68rem;font-family:"Consolas",monospace;font-weight:700;background:rgba(37,99,255,0.22);color:#93C5FD;padding:0.1rem 0.38rem;border-radius:5px;border:1px solid rgba(37,99,255,0.28);}

/* Login */
.login-outer{max-width:490px;margin:2.2rem auto 0;}
.login-card{background:white;border-radius:26px;overflow:hidden;box-shadow:0 28px 72px rgba(11,30,61,0.22),0 0 0 1px rgba(37,99,255,0.07);}
.login-card-header{background:linear-gradient(135deg,#0B1E3D 0%,#1F3A5F 50%,#2563FF 120%);padding:2.2rem 2.2rem 2rem;text-align:center;position:relative;overflow:hidden;}
.login-card-header::before{content:"";position:absolute;right:-55px;top:-55px;width:190px;height:190px;border-radius:999px;background:rgba(22,184,199,0.18);}
.login-card-header::after{content:"";position:absolute;left:-35px;bottom:-45px;width:150px;height:150px;border-radius:999px;background:rgba(37,99,255,0.14);}
.login-card-title{font-size:1.75rem;font-weight:900;color:white;letter-spacing:-0.04em;margin-bottom:0.28rem;position:relative;z-index:1;}
.login-card-sub{color:#94C3E8;font-size:0.88rem;line-height:1.55;max-width:320px;margin:0 auto;position:relative;z-index:1;}
.login-card-body{padding:1.8rem 2.2rem 2.2rem;}
.login-note{background:#FEF3C7;border-left:4px solid #F59E0B;padding:0.65rem 0.9rem;border-radius:8px;color:#78350F;font-size:0.76rem;line-height:1.5;margin-top:1.1rem;}

/* Buttons */
.stButton>button{border-radius:11px;border:none;font-weight:800;padding:0.65rem 1.1rem;background:linear-gradient(135deg,#2563FF,#16B8C7);color:white;box-shadow:0 8px 20px rgba(37,99,255,0.22);transition:0.2s ease;}
.stButton>button:hover{transform:translateY(-1px);box-shadow:0 12px 26px rgba(37,99,255,0.28);color:white;}
div[data-testid="stDownloadButton"]>button{border-radius:11px;border:1px solid #D9E2EC;background:white;color:#0B1E3D;font-weight:800;padding:0.6rem 0.9rem;box-shadow:0 4px 14px rgba(16,42,67,0.06);}
div[data-testid="stDownloadButton"]>button:hover{border-color:#2563FF;color:#2563FF;}
hr{border:none;border-top:1px solid #D9E2EC;margin:1.4rem 0;}
</style>
""", unsafe_allow_html=True)

# ── Auth & routing config ──────────────────────────────────────────
ROLES: dict[str, dict] = {
    "Sales Team Lead":       {"password": "sales123",     "access": ["CyberNova Pulse"]},
    "Marketing Lead":        {"password": "marketing123", "access": ["CyberNova Reach"]},
    "Executive Management":  {"password": "exec123",      "access": ["CyberNova Horizon"]},
    "Admin / Lecturer View": {"password": "admin123",     "access": ["CyberNova Pulse","CyberNova Reach","CyberNova Horizon"]},
}
DASHBOARDS    = ["CyberNova Pulse", "CyberNova Reach", "CyberNova Horizon"]
DATA_PATH     = "data/output/cybernova_enriched_logs.csv"
LIVE_CSV_PATH = "data/output/cybernova_live_feed.csv"
SERVICE_URIS  = ["/ai-assistant.php","/cybersecurity-monitoring.php","/risk-assessment.php",
                 "/digital-transformation.php","/predictive-maintenance.php","/prototype.php","/events.php"]
REQUIRED_COLS = ["request_id","timestamp","date","hour","day_of_week","country","is_sadc","uri",
                 "service_name","service_category","status_class","device_type","is_bot","session_id",
                 "session_number_for_ip","distinct_pages_session","entry_page","segment","is_warm_lead",
                 "event_type","converted_to_lead","campaign_name","is_campaign_period","is_anomaly",
                 "anomaly_name","response_time_ms","ip_address"]

# ── Data loading ───────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame | None:
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["date"]      = pd.to_datetime(df["date"],      errors="coerce")
    for col in ["first_request_ts","last_request_ts"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "anomaly_name" in df.columns:
        df["anomaly_name"] = df["anomaly_name"].fillna("None").astype(str)
    if "session_number_for_ip" in df.columns:
        df["session_number_for_ip"] = pd.to_numeric(df["session_number_for_ip"], errors="coerce").fillna(1).astype(int)
    return df

@st.cache_data(ttl=5, show_spinner=False)
def load_live_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(LIVE_CSV_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ("is_bot","is_warm_lead","is_anomaly"):
        if col in df.columns:
            df[col] = df[col].astype(bool)
    return df

# ── Filter helpers ─────────────────────────────────────────────────
def apply_filters(df, start, end, countries, services, status_classes, include_bots, segments):
    fdf = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)].copy()
    if countries:      fdf = fdf[fdf["country"].isin(countries)]
    if services:       fdf = fdf[fdf["service_name"].isin(services)]
    if status_classes: fdf = fdf[fdf["status_class"].isin(status_classes)]
    if not include_bots: fdf = fdf[~fdf["is_bot"]]
    if segments:       fdf = fdf[fdf["segment"].isin(segments)]
    return fdf.reset_index(drop=True)

def week_label(ts):  return ts.dt.strftime("%Y-W%V")
def month_label(ts): return ts.dt.strftime("%Y-%m")
def df_to_csv(df):   return df.to_csv(index=False).encode("utf-8")
def has_access(role, dashboard): return dashboard in ROLES.get(role, {}).get("access", [])

# ── Safe data helpers ──────────────────────────────────────────────
def safe_col(df: pd.DataFrame, col: str, default=None):
    return df[col] if col in df.columns else pd.Series([default]*len(df), index=df.index)

def get_latest_timestamp(df: pd.DataFrame):
    if df.empty or "timestamp" not in df.columns:
        return None
    ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
    return ts.max() if not ts.empty else None

def get_warm_lead_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "is_warm_lead" not in df.columns:
        return pd.DataFrame()
    return df[df["is_warm_lead"]].copy()

def calc_ai_demo_conversion(df: pd.DataFrame) -> float:
    if df.empty or "session_id" not in df.columns:
        return 0.0
    ai_sess = set(df[df["uri"] == "/ai-assistant.php"]["session_id"]) if "uri" in df.columns else set()
    if not ai_sess:
        return 0.0
    demo = df[df["session_id"].isin(ai_sess) & (df.get("uri","") == "/scheduledemo.php")]["session_id"].nunique() if "uri" in df.columns else 0
    return demo / max(len(ai_sess), 1)

def calc_engaged_session_rate(df: pd.DataFrame) -> float:
    if df.empty or "distinct_pages_session" not in df.columns:
        return 0.0
    sess = df.drop_duplicates("session_id")["distinct_pages_session"] if "session_id" in df.columns else df["distinct_pages_session"]
    return float((sess >= 3).mean())

def calc_bot_ratio(df: pd.DataFrame) -> float:
    if df.empty or "is_bot" not in df.columns:
        return 0.0
    return float(df["is_bot"].mean())

def get_top_country(df: pd.DataFrame, by: str = "warm_leads") -> str:
    if df.empty or "country" not in df.columns:
        return "—"
    if by == "warm_leads" and "is_warm_lead" in df.columns:
        warm = df[df["is_warm_lead"]]
        if not warm.empty:
            return str(warm["country"].value_counts().index[0])
    if "ip_address" in df.columns:
        return str(df.groupby("country")["ip_address"].nunique().idxmax())
    return str(df["country"].value_counts().index[0])

def get_top_service(df: pd.DataFrame) -> str:
    if df.empty or "service_name" not in df.columns:
        return "—"
    warm = df[df["is_warm_lead"]] if "is_warm_lead" in df.columns else df
    src  = warm if not warm.empty else df
    return str(src["service_name"].value_counts().index[0])

# ── Story generators ───────────────────────────────────────────────
def generate_sales_story(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No data in the selected filter range."]
    warm = get_warm_lead_df(df)
    bullets: list[str] = []
    if not warm.empty and "country" in warm.columns:
        top_c   = warm["country"].value_counts().index[0]
        top_cnt = int(warm["country"].value_counts().iloc[0])
        bullets.append(f"<strong>{top_c}</strong> is currently producing the highest warm-lead activity with <strong>{top_cnt:,}</strong> warm-lead events.")
    else:
        bullets.append("No warm-lead events detected in the current filter range — check date and status filters.")
    if not warm.empty and "service_name" in warm.columns:
        top_svc = warm["service_name"].value_counts().index[0]
        bullets.append(f"The strongest service interest is <strong>{top_svc}</strong>, making it the best product to lead with.")
    conv = calc_ai_demo_conversion(df)
    strength = "strong" if conv >= 0.15 else ("moderate" if conv >= 0.05 else "weak")
    bullets.append(f"AI Assistant sessions converted to demo at <strong>{conv:.1%}</strong>, indicating <strong>{strength}</strong> product-led interest.")
    svc_sess  = df[df["uri"].isin(SERVICE_URIS)]["session_id"].nunique() if "uri" in df.columns and "session_id" in df.columns else 0
    demo_sess = df[df["uri"] == "/scheduledemo.php"]["session_id"].nunique() if "uri" in df.columns and "session_id" in df.columns else 0
    if svc_sess > 0 and (demo_sess / svc_sess) < 0.10:
        bullets.append("The main sales opportunity is to <strong>reduce drop-off</strong> between service interest and demo request.")
    else:
        bullets.append("Demo movement is healthy — prioritise <strong>rapid follow-up</strong> on recent warm leads.")
    demo_df = df[df["uri"] == "/scheduledemo.php"] if "uri" in df.columns else pd.DataFrame()
    if not demo_df.empty and "hour" in demo_df.columns:
        top_h = int(demo_df["hour"].value_counts().index[0])
        bullets.append(f"Demo requests are most active around <strong>{top_h:02d}:00</strong> — follow-up capacity should be strongest around that period.")
    return bullets

def generate_marketing_story(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No data in the selected filter range."]
    bullets: list[str] = []
    if "country" in df.columns and "ip_address" in df.columns:
        vc = df.groupby("country")["ip_address"].nunique()
        top_c, top_v = str(vc.idxmax()), int(vc.max())
        bullets.append(f"<strong>{top_c}</strong> has the largest audience volume with <strong>{top_v:,}</strong> unique visitors.")
    eng = calc_engaged_session_rate(df)
    quality = "strong" if eng >= 0.35 else ("moderate" if eng >= 0.18 else "low")
    bullets.append(f"Engaged session rate is <strong>{eng:.1%}</strong>, suggesting <strong>{quality}</strong> content depth.")
    if "entry_page" in df.columns and "distinct_pages_session" in df.columns and "session_id" in df.columns:
        try:
            depth  = df.drop_duplicates("session_id").groupby("entry_page")["distinct_pages_session"].mean()
            top_ep = depth.idxmax()
            bullets.append(f"The strongest entry path is <strong>{top_ep}</strong>, making it an important campaign landing page.")
        except Exception:
            pass
    if "segment" in df.columns:
        human_segs = df[df["segment"] != "Bot"]["segment"].value_counts() if "Bot" in df["segment"].values else df["segment"].value_counts()
        if not human_segs.empty:
            dom = human_segs.index[0]
            desc = {"High-intent":"high-intent","Product-curious":"product-curious","General browser":"general"}.get(dom,"general")
            bullets.append(f"The dominant human segment is <strong>{dom}</strong>, indicating <strong>{desc}</strong> traffic.")
    bot_r = calc_bot_ratio(df)
    if bot_r > 0.15:
        bullets.append(f"Bot activity is <strong>high ({bot_r:.1%})</strong> and may distort marketing reach metrics.")
    else:
        bullets.append(f"Bot activity is controlled at <strong>{bot_r:.1%}</strong> and unlikely to dominate marketing interpretation.")
    return bullets

def generate_executive_story(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No data in the selected filter range."]
    bullets: list[str] = []
    total_warm = int(df["is_warm_lead"].sum()) if "is_warm_lead" in df.columns else 0
    bullets.append(f"CyberNova generated <strong>{total_warm:,}</strong> warm-lead events in the selected period.")
    ai_reqs  = int((df["uri"] == "/ai-assistant.php").sum()) if "uri" in df.columns else 0
    svc_reqs = int(df["uri"].isin(SERVICE_URIS).sum()) if "uri" in df.columns else 1
    ai_share = ai_reqs / max(svc_reqs, 1)
    traction = "strong" if ai_share >= 0.18 else ("moderate" if ai_share >= 0.10 else "emerging")
    bullets.append(f"AI Assistant represents <strong>{ai_share:.1%}</strong> of service activity, showing <strong>{traction}</strong> traction.")
    if "country" in df.columns and "ip_address" in df.columns and "is_warm_lead" in df.columns:
        top_c = df.groupby("country")["ip_address"].nunique().idxmax()
        top_v = int(df.groupby("country")["ip_address"].nunique().max())
        top_wl = int(df[df["is_warm_lead"]]["country"].value_counts().get(top_c, 0))
        bullets.append(f"The strongest regional market is <strong>{top_c}</strong>, with {top_v:,} unique visitors and {top_wl:,} warm leads.")
    anom_count = int(df["is_anomaly"].sum()) if "is_anomaly" in df.columns else 0
    if anom_count > 0:
        bullets.append(f"<strong>{anom_count:,}</strong> anomaly events were flagged and should be reviewed for operational or security context.")
    else:
        bullets.append("No anomaly events are visible in the selected filter context.")
    if "is_warm_lead" in df.columns and "date" in df.columns:
        wc = df[df["is_warm_lead"]].copy()
        wc["d"] = wc["date"].dt.date
        dl = wc.groupby("d").size()
        dl.index = pd.to_datetime(dl.index)
        if len(dl) >= 7:
            x, y = np.arange(len(dl), dtype=float), dl.values.astype(float)
            m, b = np.polyfit(x, y, 1)
            fx = np.arange(len(x), len(x)+30, dtype=float)
            ft = max(int(sum(np.maximum(m*fx+b, 0))), 0)
            bullets.append(f"The next 30-day warm-lead forecast is approximately <strong>{ft:,}</strong> leads based on recent daily activity.")
    return bullets

def generate_story_bullets(df: pd.DataFrame, dashboard_type: str) -> list[str]:
    if dashboard_type == "sales":     return generate_sales_story(df)
    if dashboard_type == "marketing": return generate_marketing_story(df)
    if dashboard_type == "executive": return generate_executive_story(df)
    return []

# ── Render component functions ─────────────────────────────────────
def render_section_label(text: str, icon: str = "") -> None:
    ico = f'{svg_icon(icon, 11, "#94A3B8")} ' if icon else ""
    st.markdown(f'<div class="section-label">{ico}{text}</div>', unsafe_allow_html=True)

def render_story_flow_strip(accent: str = "blue") -> None:
    stages = ["Context","KPIs","Diagnosis","Action","Evidence","Export"]
    cls = f"strip-active-{accent}"
    pills = ""
    for i, s in enumerate(stages):
        pills += f'<span class="{cls} strip-stage">{s}</span>'
        if i < len(stages)-1:
            pills += '<span class="strip-arrow">&#8594;</span>'
    st.markdown(f'<div class="story-strip">{pills}</div>', unsafe_allow_html=True)

def render_story_panel(title: str, subtitle: str, bullets: list[str],
                       accent: str = "blue", action_label: str | None = None) -> None:
    icons  = {"blue":"zap","cyan":"globe","green":"trending","amber":"report"}
    colors = {"blue":BLUE,"cyan":CYAN,"green":GREEN,"amber":AMBER}
    ico    = svg_icon(icons.get(accent,"zap"), 16, colors.get(accent, BLUE))
    dot    = f"story-dot-{accent}" if accent in ("blue","cyan","green","amber") else "story-dot-blue"
    items  = "".join(
        f'<div class="story-bullet"><div class="story-dot {dot}"></div><div>{b}</div></div>'
        for b in bullets
    )
    action_html = ""
    if action_label:
        chip_cls = f"story-action-{accent}" if accent in ("blue","cyan","green","amber") else "story-action-blue"
        chk = svg_icon("check", 12, colors.get(accent, BLUE))
        action_html = f'<div><span class="{chip_cls} story-action-chip">{chk}&nbsp;{action_label}</span></div>'
    st.markdown(
        f'<div class="story-panel story-panel-{accent}">'
        f'<div class="story-title">{ico} {title}</div>'
        f'<div class="story-subtitle">{subtitle}</div>'
        f'{items}{action_html}</div>',
        unsafe_allow_html=True,
    )

def render_kpi_card(label, value, delta, status="neutral", icon="bar_chart"):
    cmap = {"good":"kpi-green","warn":"kpi-amber","bad":"kpi-red","info":"kpi-cyan","neutral":"kpi-blue"}
    ico  = svg_icon(icon, 13, "#64748B")
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{ico} {label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-delta {cmap.get(status,"kpi-blue")}">{delta}</div></div>',
        unsafe_allow_html=True,
    )

def render_section_header(title, subtitle="", icon="bar_chart"):
    ico = svg_icon(icon, 15, "#64748B")
    st.markdown(
        f'<div class="section-card"><div class="section-title">{ico} {title}</div>'
        + (f'<div class="section-caption">{subtitle}</div>' if subtitle else "")
        + "</div>", unsafe_allow_html=True,
    )

def render_chart_insight(text):
    st.markdown(f'<div class="chart-insight">{svg_icon("info",13,"#2563FF")} {text}</div>',
                unsafe_allow_html=True)

def render_insight_card(title, bullets, icon="zap"):
    ico   = svg_icon(icon, 16, "#1E40AF")
    items = "".join(
        f'<div class="insight-bullet"><div class="insight-dot"></div><div>{b}</div></div>'
        for b in bullets
    )
    st.markdown(
        f'<div class="insight-card"><div class="insight-title">{ico} {title}</div>{items}</div>',
        unsafe_allow_html=True,
    )

def render_empty_state(title="No data", text="Adjust the date range or filter selections."):
    ico = svg_icon("search", 32, "#D9E2EC")
    st.markdown(
        f'<div class="empty-card"><div style="font-size:2rem;margin-bottom:0.5rem;">{ico}</div>'
        f'<div class="empty-title">{title}</div><div class="empty-text">{text}</div></div>',
        unsafe_allow_html=True,
    )

def render_restricted(dashboard, role):
    ico = svg_icon("lock", 42, "#EF4444")
    st.markdown(
        f'<div class="restricted-card"><div>{ico}</div>'
        f'<div class="restricted-title">Access Restricted</div>'
        f'<div class="restricted-text"><strong>{role}</strong> does not have access to <strong>{dashboard}</strong>.</div></div>',
        unsafe_allow_html=True,
    )

def render_filter_chips(filters, role=""):
    c_str  = ", ".join(filters["countries"])      if filters["countries"]      else "All"
    s_str  = ", ".join(filters["services"])       if filters["services"]       else "All"
    sc_str = ", ".join(filters["status_classes"]) if filters["status_classes"] else "All"
    sg_str = ", ".join(filters["segments"])       if filters["segments"]       else "All"
    bot_lbl = "Incl." if filters["include_bots"] else "Excl."
    now_str = pd.Timestamp.now().strftime("%H:%M:%S")
    rchip   = f'<span class="ctx-chip ctx-chip-role">{role}</span>' if role else ""
    bcls    = "ctx-chip-amber" if filters["include_bots"] else ""
    st.markdown(
        f'<div class="ctx-bar">{rchip}'
        f'<span class="ctx-chip">{filters["start"]} to {filters["end"]}</span>'
        f'<span class="ctx-chip">Countries: {c_str[:30]}{"..." if len(c_str)>30 else ""}</span>'
        f'<span class="ctx-chip">Services: {s_str[:28]}{"..." if len(s_str)>28 else ""}</span>'
        f'<span class="ctx-chip">Status: {sc_str}</span>'
        f'<span class="ctx-chip {bcls}">Bots: {bot_lbl}</span>'
        f'<span class="ctx-chip ctx-chip-green">Updated: {now_str}</span>'
        f'</div>', unsafe_allow_html=True,
    )

def render_dash_hero(title, subtitle, description, icon):
    ico = svg_icon(icon, 20, "rgba(255,255,255,0.85)")
    st.markdown(
        f'<div class="dash-hero"><div class="dash-hero-badge">{ico} {subtitle}</div>'
        f'<div class="dash-hero-title">{title}</div>'
        f'<div class="dash-hero-sub">{description}</div></div>',
        unsafe_allow_html=True,
    )

def chart_style(fig, height=380):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=WHITE,
        font=dict(color=DARK_BLUE, family="Segoe UI, Inter, Arial, sans-serif"),
        margin=dict(l=20,r=20,t=52,b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    fig.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False)
    fig.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False)
    return fig

# ── Sales Action Queue ─────────────────────────────────────────────
def render_sales_action_queue(df: pd.DataFrame) -> None:
    if df.empty:
        render_empty_state("No action items", "No events in current filter range.")
        return
    q = df.copy()
    def _rec(row):
        et = str(row.get("event_type","")).lower()
        if "demo" in et:     return "Contact within 24 hours"
        if "contact" in et:  return "Assign to sales representative"
        if "event" in et:    return "Invite to product demo follow-up"
        if "ai" in et:       return "Send AI Assistant solution brief"
        return "Monitor session activity"
    def _pri(row):
        if row.get("is_warm_lead", False):       return "High"
        if str(row.get("segment","")) == "Product-curious": return "Medium"
        return "Low"
    q["recommended_action"] = q.apply(_rec, axis=1)
    q["priority"]           = q.apply(_pri, axis=1)
    q["_pord"] = q["priority"].map({"High":0,"Medium":1,"Low":2}).fillna(2)
    q = q.sort_values(["_pord","timestamp"], ascending=[True, False])
    cols = ["priority","timestamp","country","service_name","event_type","segment","recommended_action"]
    show = q[[c for c in cols if c in q.columns]].head(50)
    render_section_label("EVIDENCE", "users")
    st.markdown(
        f'<div class="action-table-card">'
        f'<div class="section-title">{svg_icon("target",15,"#0B1E3D")} Sales Action Queue</div>'
        f'<div class="section-caption">Prioritised lead events requiring follow-up.</div></div>',
        unsafe_allow_html=True,
    )
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.download_button("Download Action Queue CSV", data=df_to_csv(show),
                       file_name="sales_action_queue.csv", mime="text/csv",
                       key="dl_sales_action_queue")

# ── Campaign Opportunity Matrix ────────────────────────────────────
def render_campaign_opportunity_matrix(df: pd.DataFrame) -> None:
    if df.empty or "country" not in df.columns:
        render_empty_state("No campaign data", "No events in current filter range.")
        return
    rows = []
    for ctry, cdf in df.groupby("country"):
        uv  = cdf["ip_address"].nunique() if "ip_address" in cdf.columns else len(cdf)
        sd  = cdf.drop_duplicates("session_id") if "session_id" in cdf.columns else cdf
        eng = int((sd["distinct_pages_session"] >= 3).sum()) if "distinct_pages_session" in sd.columns else 0
        wl  = int(cdf["is_warm_lead"].sum()) if "is_warm_lead" in cdf.columns else 0
        br  = float(cdf["is_bot"].mean())   if "is_bot" in cdf.columns else 0.0
        rows.append({"country":ctry,"unique_visitors":uv,"engaged_sessions":eng,"warm_leads":wl,"bot_ratio":br})
    mx = pd.DataFrame(rows).sort_values("unique_visitors", ascending=False)
    if mx.empty:
        return
    mx["uv_rank"]  = mx["unique_visitors"].rank(pct=True)
    mx["eng_rank"] = mx["engaged_sessions"].rank(pct=True)
    mx["wl_rank"]  = mx["warm_leads"].rank(pct=True)
    mx["bot_pen"]  = mx["bot_ratio"].clip(0,1) * 0.5
    mx["opportunity_score"] = (mx["uv_rank"] + mx["eng_rank"] + mx["wl_rank"] - mx["bot_pen"]).round(2)
    def _act(s):
        if s >= 2.0: return "Prioritise paid/organic campaign test"
        if s >= 1.2: return "Nurture with content and retargeting"
        return "Monitor before spending"
    mx["recommended_action"] = mx["opportunity_score"].apply(_act)
    mx["bot_ratio"] = mx["bot_ratio"].map("{:.1%}".format)
    show = mx[["country","unique_visitors","engaged_sessions","warm_leads","bot_ratio","opportunity_score","recommended_action"]]
    render_section_label("EVIDENCE", "map_pin")
    st.markdown(
        f'<div class="action-table-card">'
        f'<div class="section-title">{svg_icon("globe",15,"#0B1E3D")} Campaign Opportunity Matrix</div>'
        f'<div class="section-caption">Country-level scoring for campaign prioritisation.</div></div>',
        unsafe_allow_html=True,
    )
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.download_button("Download Campaign Matrix CSV", data=df_to_csv(show),
                       file_name="campaign_opportunity_matrix.csv", mime="text/csv",
                       key="dl_campaign_matrix")

# ── Executive Decision Brief ───────────────────────────────────────
def render_executive_decision_brief(df: pd.DataFrame, kd: dict) -> None:
    if df.empty:
        return
    mg   = kd.get("mom_growth", 0.0)
    ais  = kd.get("ai_share", 0.0)
    sadc = kd.get("sadc_total", 0)
    anom = kd.get("anom_days", 0)
    rows = [
        {"Strategic Signal": "Growth improving" if mg >= 0 else "Growth declining",
         "Evidence": f"MoM visitor change: {mg:+.1f}%",
         "Leadership Action": "Sustain current acquisition momentum." if mg >= 0 else "Investigate traffic drop and act.",
         "Risk / Dependency": "Seasonal variation may affect trend."},
        {"Strategic Signal": "AI Assistant gaining traction" if ais >= 0.10 else "AI Assistant needs promotion",
         "Evidence": f"AI share of service traffic: {ais:.1%}",
         "Leadership Action": "Scale AI positioning in high-performing SADC markets." if ais >= 0.10 else "Increase AI Assistant visibility in campaigns.",
         "Risk / Dependency": "Conversion quality must be tracked alongside volume."},
        {"Strategic Signal": "Regional reach broadening" if sadc >= 7 else "Regional penetration limited",
         "Evidence": f"{sadc} SADC markets active",
         "Leadership Action": "Activate targeted content per SADC market." if sadc >= 7 else "Focus on top 3 SADC markets first.",
         "Risk / Dependency": "Country-specific regulatory factors apply."},
        {"Strategic Signal": "Operational review required" if anom > 0 else "Operations nominal",
         "Evidence": f"{anom} anomaly days flagged",
         "Leadership Action": "Review anomaly log for security or infrastructure issues." if anom > 0 else "No immediate action required.",
         "Risk / Dependency": "Anomaly patterns may require IT security review." if anom > 0 else "Continue standard monitoring."},
    ]
    brief = pd.DataFrame(rows)
    render_section_label("EVIDENCE", "report")
    st.markdown(
        f'<div class="action-table-card">'
        f'<div class="section-title">{svg_icon("report",15,"#0B1E3D")} Executive Decision Brief</div>'
        f'<div class="section-caption">Board-level strategic signals with recommended leadership actions.</div></div>',
        unsafe_allow_html=True,
    )
    st.dataframe(brief, use_container_width=True, hide_index=True)
    st.download_button("Download Decision Brief CSV", data=df_to_csv(brief),
                       file_name="executive_decision_brief.csv", mime="text/csv",
                       key="dl_exec_brief")

# ── Export card ────────────────────────────────────────────────────
def render_export_card(dashboard, filters, kpis, fdf, narrative=None):
    ico = svg_icon("report", 16, "#0B1E3D")
    st.markdown(
        f'<div class="report-card"><div class="report-card-title">{ico} Report &amp; Export</div></div>',
        unsafe_allow_html=True,
    )
    r1, r2, r3 = st.columns(3)
    with r1:
        st.download_button("Download CSV", data=df_to_csv(fdf),
                           file_name=f"{dashboard.lower().replace(' ','_')}.csv",
                           mime="text/csv", use_container_width=True,
                           key=f"exp_csv_{dashboard}")
    with r2:
        try:
            pdf = _generate_pdf(dashboard, filters, kpis, narrative)
            st.download_button("Download PDF Report", data=pdf,
                               file_name=f"{dashboard.lower().replace(' ','_')}.pdf",
                               mime="application/pdf", use_container_width=True,
                               key=f"exp_pdf_{dashboard}")
        except Exception as e:
            st.error(f"PDF error: {e}")
    with r3:
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            fdf.to_excel(w, sheet_name="Data", index=False)
            if kpis:
                pd.DataFrame(kpis).to_excel(w, sheet_name="KPIs", index=False)
        st.download_button("Download Excel", data=buf.getvalue(),
                           file_name=f"{dashboard.lower().replace(' ','_')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True, key=f"exp_xlsx_{dashboard}")
    st.caption(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}  |  "
               f"Rows: {len(fdf):,}  |  Rule-based insights only — not AI generated.")

# ── PDF generation ─────────────────────────────────────────────────
def _generate_pdf(dashboard, filters, kpis, narrative=None):
    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    sty  = getSampleStyleSheet()
    navy = rl_colors.HexColor("#0B1E3D"); blue = rl_colors.HexColor("#2563FF"); grey = rl_colors.HexColor("#64748B")
    h1   = ParagraphStyle("h1", parent=sty["Heading1"], textColor=navy, fontSize=20, spaceAfter=4)
    h2   = ParagraphStyle("h2", parent=sty["Heading2"], textColor=blue, fontSize=13, spaceAfter=4)
    bdy  = ParagraphStyle("bd", parent=sty["Normal"],   textColor=navy, fontSize=10, spaceAfter=3)
    cap  = ParagraphStyle("cp", parent=sty["Normal"],   textColor=grey, fontSize=8,  spaceAfter=2)
    els  = [Paragraph("CyberNova Analytics Ltd", h1), Paragraph(f"{dashboard} — Report", h2),
            Paragraph(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}  |  "
                      f"Period: {filters['start']} to {filters['end']}", cap),
            HRFlowable(width="100%", thickness=1, color=rl_colors.HexColor("#D9E2EC"), spaceAfter=10),
            Paragraph("Active Filters", h2)]
    frows = [["Countries", ", ".join(filters["countries"]) or "All"],
             ["Services",  ", ".join(filters["services"])  or "All"],
             ["Status",    ", ".join(filters["status_classes"]) or "All"],
             ["Bots",      "Included" if filters["include_bots"] else "Excluded"]]
    ft = Table([["Filter","Value"]]+frows, colWidths=[4*cm,13*cm])
    ft.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),rl_colors.HexColor("#0B1E3D")),
                             ("TEXTCOLOR",(0,0),(-1,0),rl_colors.white),("FONTSIZE",(0,0),(-1,-1),9),
                             ("ROWBACKGROUNDS",(0,1),(-1,-1),[rl_colors.HexColor("#F3F4F6"),rl_colors.white]),
                             ("GRID",(0,0),(-1,-1),0.4,rl_colors.HexColor("#D9E2EC")),("PADDING",(0,0),(-1,-1),5)]))
    els.append(ft); els.append(Spacer(1,12))
    if kpis:
        els.append(Paragraph("Key Performance Indicators", h2))
        krows = [[k.get("label",""),k.get("value",""),k.get("note","")] for k in kpis]
        kt = Table([["Metric","Value","Note"]]+krows, colWidths=[7*cm,4*cm,6*cm])
        kt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),rl_colors.HexColor("#2563FF")),
                                 ("TEXTCOLOR",(0,0),(-1,0),rl_colors.white),("FONTSIZE",(0,0),(-1,-1),9),
                                 ("ROWBACKGROUNDS",(0,1),(-1,-1),[rl_colors.HexColor("#EEF6FF"),rl_colors.white]),
                                 ("GRID",(0,0),(-1,-1),0.4,rl_colors.HexColor("#D9E2EC")),("PADDING",(0,0),(-1,-1),5)]))
        els.append(kt); els.append(Spacer(1,12))
    if narrative:
        els.append(Paragraph("Insights", h2))
        for b in narrative:
            els.append(Paragraph(f"• {b.replace('<strong>','').replace('</strong>','')}", bdy))
    els.append(Spacer(1,16))
    els.append(Paragraph("Rule-based insights only — not AI-generated. Prototype access — not for production.", cap))
    doc.build(els)
    return buf.getvalue()

# ── Live Activity Feed (embedded, role-aware) ──────────────────────
def _prioritise_feed_df(df: pd.DataFrame, role: str) -> pd.DataFrame:
    if df.empty:
        return df
    if "Sales" in role:
        mask = (df.get("is_warm_lead", pd.Series(False, index=df.index)) |
                df.get("event_type", pd.Series("", index=df.index)).str.contains("demo|contact|event|ai", na=False))
        hi = df[mask]
        lo = df[~mask]
        return pd.concat([hi, lo]).drop_duplicates()
    if "Marketing" in role:
        mask = (~df.get("is_bot", pd.Series(False, index=df.index)) |
                df.get("campaign_name", pd.Series("", index=df.index)).notna())
        hi = df[mask]
        lo = df[~mask]
        return pd.concat([hi, lo]).drop_duplicates()
    if "Executive" in role or "Admin" in role:
        mask = (df.get("is_anomaly", pd.Series(False, index=df.index)) |
                df.get("is_warm_lead", pd.Series(False, index=df.index)) |
                df.get("uri", pd.Series("", index=df.index)).str.contains("ai-assistant", na=False) |
                df.get("is_sadc", pd.Series(False, index=df.index)))
        hi = df[mask]
        lo = df[~mask]
        return pd.concat([hi, lo]).drop_duplicates()
    return df

@st.fragment(run_every="5s")
def _live_feed_fragment(filtered_df: pd.DataFrame, role: str = "", subtitle: str = "") -> None:
    ldf = load_live_data()
    now = pd.Timestamp.now()
    is_live = False
    if not ldf.empty and "timestamp" in ldf.columns:
        recent = ldf[ldf["timestamp"] >= now - pd.Timedelta(minutes=10)]
        is_live = not recent.empty
        source  = recent if is_live else filtered_df
    else:
        source = filtered_df
    source = _prioritise_feed_df(source, role)
    source = source.copy()
    source["timestamp"] = pd.to_datetime(source["timestamp"], errors="coerce")
    source = source.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False).head(12)
    live_badge = '<span class="live-badge"><span class="live-dot"></span>LIVE</span>' if is_live else ""
    hist_note  = "" if is_live else '<span style="color:#94A3B8;font-size:0.73rem;">Historical data — run python live_feed.py for live stream</span>'
    sub_text   = subtitle or "Operational pulse from latest filtered events."
    st.markdown(
        f'<div class="section-card">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.55rem;">'
        f'<div class="section-title">{svg_icon("activity",15,"#64748B")} Live Activity Feed</div>'
        f'<div>{live_badge}{hist_note}</div></div>'
        f'<div style="font-size:0.78rem;color:#64748B;margin-bottom:0.7rem;">{sub_text}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="font-size:0.72rem;color:#94A3B8;margin-bottom:0.4rem;">Operational pulse from latest filtered events.</div>', unsafe_allow_html=True)
    if source.empty:
        st.markdown('<div style="text-align:center;color:#94A3B8;padding:1.2rem;font-size:0.85rem;">No activity events found.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return
    items_html = ""
    for _, row in source.iterrows():
        is_warm  = bool(row.get("is_warm_lead", False))
        is_bot   = bool(row.get("is_bot", False))
        is_anom  = bool(row.get("is_anomaly", False))
        evt      = str(row.get("event_type", "page_request"))
        status   = str(row.get("status_class", "2xx"))
        if is_bot or is_anom or status in ("4xx","5xx"):
            dot = "feed-dot-amber"
        elif is_warm or any(k in evt for k in ("demo","contact","ai","event")):
            dot = "feed-dot-green"
        else:
            dot = "feed-dot-blue"
        warm_tag = '<span class="feed-warm">warm lead</span>' if is_warm else ""
        anom_tag = '<span class="feed-anom">anomaly</span>' if is_anom else ""
        ts_str   = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(row.get("timestamp")) else "—"
        items_html += (
            f'<div class="feed-item"><div class="feed-dot {dot}"></div><div style="flex:1;">'
            f'<div class="feed-time">{ts_str}</div>'
            f'<div class="feed-main">{row.get("country","—")} &middot; {str(row.get("service_name","—"))[:32]}{warm_tag}{anom_tag}</div>'
            f'<div class="feed-meta">{evt} &middot; {row.get("segment","—")} &middot; <strong>{status}</strong></div>'
            f'</div></div>'
        )
    st.markdown(f'<div class="feed-container">{items_html}</div></div>', unsafe_allow_html=True)
    st.caption(f"Auto-refreshes every 5 s · {now.strftime('%H:%M:%S')}")

def render_live_feed(filtered_df, role="", subtitle=""):
    _live_feed_fragment(filtered_df, role, subtitle)

# ── Forecast helper ────────────────────────────────────────────────
def _simple_forecast(daily: pd.Series, days: int = 30) -> pd.Series:
    if len(daily) < 7:
        return pd.Series(dtype=float)
    x, y = np.arange(len(daily), dtype=float), daily.values.astype(float)
    m, b = np.polyfit(x, y, 1)
    fx   = np.arange(len(x), len(x)+days, dtype=float)
    fdates = pd.date_range(pd.Timestamp(daily.index[-1]) + pd.Timedelta(days=1), periods=days)
    return pd.Series(np.maximum(m*fx+b, 0), index=fdates)
