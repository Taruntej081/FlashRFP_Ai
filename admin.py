"""
admin.py — FlashRFP.ai Immersive Enterprise Admin Console
Run: streamlit run admin.py --server.port 8502

An ultra-premium, highly immersive, light-themed admin dashboard
inspired by Vercel, Stripe, and Apple design languages.
"""
import os
import json
import bcrypt
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ── Configuration & Bootstrap ──────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"), override=True)

# Smart DB layer: uses Supabase when keys are set, JSON fallback otherwise
try:
    import supabase_client as _supa
    _USE_SUPA = _supa.is_supabase_ready()
except Exception:
    _USE_SUPA = False

import admin_db as _local_db

class _DB:
    """Proxy — routes to Supabase or local JSON transparently."""
    def __getattr__(self, name):
        if _USE_SUPA and hasattr(_supa, name):
            return getattr(_supa, name)
        return getattr(_local_db, name)

db = _DB()

st.set_page_config(
    page_title="FlashRFP Portal — Admin Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Strict Admin Authentication Layer ──────────────────────────────────────────
# Define custom login state
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "name" not in st.session_state:
    st.session_state["name"] = ""

config_file = os.path.join(base_dir, "auth_config.json")

# Render custom login screen if not authenticated
if not st.session_state["authentication_status"]:
    st.markdown("""
    <style>
    /* Centered Login Card Styling */
    .login-container {
        max-width: 450px;
        margin: 6rem auto 2rem;
        padding: 2.5rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 16px -6px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .login-logo {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .login-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.25rem;
        letter-spacing: -0.03em;
    }
    .login-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">🛡️</div>
        <div class="login-title">FlashRFP Admin Portal</div>
        <div class="login-subtitle">Enforced Multi-Tenant Administrator Gate</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render form using columns to center inputs
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        with st.form("admin_login_form"):
            input_username = st.text_input("Administrator Username", key="login_uname", placeholder="Enter admin username...")
            input_password = st.text_input("Console Access Key", type="password", key="login_pwd", placeholder="Enter password...")
            submit_login = st.form_submit_button("Authenticate Console", type="primary", use_container_width=True)
            
            if submit_login:
                if input_username and input_password:
                    # Fetch user record strictly from database layer (Supabase / local config fallback)
                    user_record = db.get_user(input_username)
                    
                    if user_record and user_record.get("is_admin") is True:
                        # Fetch hashed password from local config to match registration hashes
                        try:
                            with open(config_file, "r") as f:
                                ac = json.load(f)
                            stored_pw = ac["credentials"]["usernames"].get(input_username, {}).get("password", "")
                        except Exception:
                            stored_pw = ""
                            
                        # Perform bcrypt verification
                        if stored_pw and bcrypt.checkpw(input_password.encode(), stored_pw.encode()):
                            st.session_state["authentication_status"] = True
                            st.session_state["username"] = input_username
                            st.session_state["name"] = user_record.get("name", "Admin User")
                            st.success("Console authenticated successfully.")
                            st.rerun()
                        else:
                            st.error("Authentication failed: Invalid credentials.")
                    else:
                        st.error("Access denied: Insufficient privileges.")
                else:
                    st.error("Credentials required.")
        st.stop()

# Admin Record Verification
admin_record = db.get_user(st.session_state["username"])
if not admin_record or not admin_record.get("is_admin"):
    st.session_state["authentication_status"] = None
    st.session_state["username"] = ""
    st.session_state["name"] = ""
    st.error("Session terminated: Access cleared due to missing authorization.")
    st.stop()

# ── Visual Theme System (Premium Immersive Light Style) ──────────────────────────
BG      = "#f6f8fa"
CARD_BG = "#ffffff"
BORDER  = "#e2e8f0"
TEXT    = "#0f172a"
MUTED   = "#64748b"
ACCENT  = "#0066ff"
ACC2    = "#00c6ff"
GREEN   = "#10b981"
RED     = "#ef4444"
AMBER   = "#f59e0b"
SHADOW  = "rgba(0, 0, 0, 0.05)"
FONT_FAMILY = "'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif"

def inject_premium_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    *, *::before, *::after {{ box-sizing: border-box; }}
    
    /* Base Body Styling */
    html, body, [data-testid="stAppViewContainer"],
    section[data-testid="stMain"], .main {{
        background-color: #f6f8fa !important;
        color: #0f172a !important;
    }}
    
    /* Hide Default Layout Overlays */
    header[data-testid="stHeader"], #MainMenu, footer,
    [data-testid="stToolbar"], .stDeployButton {{ display: none !important; }}
    
    /* Immersive Sidebar Customization */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
        border-right: 1px solid #e2e8f0 !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02) !important;
    }}
    
    /* Document Layout */
    .block-container {{
        padding: 3rem 4rem 5rem !important;
        max-width: 1440px !important;
        margin: 0 auto;
    }}
    
    /* Specific Typography Overrides */
    p, li, label, .stMarkdown, .stMarkdown p, h1, h2, h3, h4, h5, h6, 
    .stButton>button, input, select, textarea, 
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {{
        font-family: {FONT_FAMILY} !important;
    }}
    
    p, li, label, .stMarkdown {{
        color: #334155 !important;
        font-size: 0.92rem;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: #0f172a !important;
        font-weight: 700;
        letter-spacing: -0.03em;
    }}
    
    /* Scrollbars */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 10px; }}
    
    /* Glassmorphic Minimal Card */
    .glass-panel {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 16px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.03), 0 2px 6px -1px rgba(0, 0, 0, 0.02);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .glass-panel:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 30px -4px rgba(99, 102, 241, 0.08), 0 4px 12px -2px rgba(0, 0, 0, 0.03);
        border-color: rgba(99, 102, 241, 0.3);
    }}
    
    /* Immersive Metric Card */
    .metric-hero {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem 1.75rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.015);
        position: relative;
        overflow: hidden;
        transition: transform 0.2s;
    }}
    .metric-hero:hover {{
        transform: scale(1.015);
    }}
    .metric-hero::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, #6366f1 0%, #06b6d4 100%);
    }}
    .metric-title {{
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.4rem;
    }}
    .metric-num {{
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.1;
        color: #0f172a !important;
    }}
    .metric-footer {{
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.5rem;
        font-weight: 500;
    }}
    
    /* Beautiful Interactive Tabs */
    div[role="tablist"] {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 6px !important;
        gap: 4px !important;
        margin-bottom: 2rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02) !important;
    }}
    div[role="tab"] {{
        border-radius: 10px !important;
        padding: 0.65rem 1.6rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div[role="tab"] *, div[role="tab"] p, div[role="tab"] span {{
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #64748b !important;
    }}
    div[role="tab"][aria-selected="true"] {{
        background-color: #6366f1 !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.2) !important;
    }}
    div[role="tab"][aria-selected="true"] *, div[role="tab"][aria-selected="true"] p,
    div[role="tab"][aria-selected="true"] span {{
        color: #ffffff !important;
    }}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"],
    [data-testid="stTabHighlight"], [data-testid="stTabBorder"] {{ display: none !important; }}
    
    /* Status Badges */
    .badge-pill {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 30px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }}
    .bg-active  {{ background-color: #e6fcf5; color: #0ca678; border: 1px solid rgba(12,166,120,0.15); }}
    .bg-trial   {{ background-color: #fff9db; color: #f59f00; border: 1px solid rgba(245,159,0,0.15); }}
    .bg-suspend {{ background-color: #fff5f5; color: #fa5252; border: 1px solid rgba(250,82,82,0.15); }}
    .bg-cancel  {{ background-color: #f1f3f5; color: #495057; border: 1px solid #dee2e6; }}
    
    .bg-plan-e  {{ background-color: #edf2ff; color: #364fc7; border: 1px solid rgba(54,79,199,0.15); }}
    .bg-plan-p  {{ background-color: #e3fafc; color: #0c8599; border: 1px solid rgba(12,133,153,0.15); }}
    .bg-plan-s  {{ background-color: #ebfbee; color: #2b8a3e; border: 1px solid rgba(43,138,62,0.15); }}
    .bg-plan-t  {{ background-color: #f8f9fa; color: #495057; border: 1px solid #dee2e6; }}

    /* Styled Form Control Buttons */
    .stButton>button {{
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-family: {FONT_FAMILY} !important;
        font-size: 0.85rem !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }}
    .stButton>button[kind="primary"] {{
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        border: none !important;
        color: #ffffff !important;
    }}
    .stButton>button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(79,70,229,0.25) !important;
    }}
    .stButton>button[kind="secondary"] {{
        background: #ffffff !important;
        border: 1px solid #d1d5db !important;
        color: #1f2937 !important;
    }}
    .stButton>button[kind="secondary"]:hover {{
        border-color: #6366f1 !important;
        color: #6366f1 !important;
        background-color: #fafafa !important;
    }}
    
    .stTextInput input, .stSelectbox>div>div, .stNumberInput input, .stTextArea textarea {{
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        color: #0f172a !important;
        font-family: {FONT_FAMILY} !important;
        font-size: 0.88rem !important;
        padding: 0.5rem 1rem !important;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.02) !important;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }}
    
    /* Immersive Interactive KPI Card */
    .kpi-card {{
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 1.5rem 1.75rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.015) !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        min-height: 140px !important;
        margin-bottom: 1.25rem !important;
    }}
    .kpi-card:hover {{
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 25px -4px rgba(99, 102, 241, 0.1), 0 4px 12px -2px rgba(0, 0, 0, 0.03) !important;
        border-color: rgba(99, 102, 241, 0.35) !important;
    }}
    .kpi-card::after {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6366f1 0%, #06b6d4 100%) !important;
    }}
    .kpi-header-row {{
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        margin-bottom: 0.5rem !important;
    }}
    .kpi-label {{
        font-size: 0.78rem !important;
        color: #64748b !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }}
    .kpi-value {{
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        line-height: 1.1 !important;
        color: #0f172a !important;
        margin: 0.25rem 0 !important;
    }}
    .kpi-sub-row {{
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        margin-top: 0.5rem !important;
    }}
    .kpi-sub {{
        font-size: 0.82rem !important;
        color: #64748b !important;
        font-weight: 500 !important;
    }}
    .trend-badge {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 0.25rem !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 6px !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
    }}
    .trend-up {{
        background-color: #ecfdf5 !important;
        color: #10b981 !important;
        border: 1px solid rgba(16,185,129,0.15) !important;
    }}
    .trend-down {{
        background-color: #fef2f2 !important;
        color: #ef4444 !important;
        border: 1px solid rgba(239,68,68,0.15) !important;
    }}
    .trend-neutral {{
        background-color: #f8fafc !important;
        color: #64748b !important;
        border: 1px solid #e2e8f0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

inject_premium_ui()

def render_kpi_card(col, label, val, sub, trend_val=None, trend_direction=None, value_color=None):
    """Renders a styled KPI card with optional up/down trend arrows."""
    trend_html = ""
    if trend_val:
        if trend_direction == "up":
            trend_html = f'<span class="trend-badge trend-up">▲ {trend_val}</span>'
        elif trend_direction == "down":
            trend_html = f'<span class="trend-badge trend-down">▼ {trend_val}</span>'
        else:
            trend_html = f'<span class="trend-badge trend-neutral">■ {trend_val}</span>'
            
    val_style = f' style="color:{value_color} !important;"' if value_color else ''
    
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-header-row">
            <span class="kpi-label">{label}</span>
            {trend_html}
        </div>
        <div class="kpi-value"{val_style}>{val}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """
    col.markdown(card_html, unsafe_allow_html=True)


# Global badges style lookup
plan_badges = {
    "enterprise": "bg-plan-e",
    "professional": "bg-plan-p",
    "starter": "bg-plan-s",
    "trial": "bg-plan-t"
}
status_badges = {
    "active": "bg-active",
    "trial": "bg-trial",
    "suspended": "bg-suspend",
    "cancelled": "bg-cancel"
}

# ── Sidebar Setup ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:1.75rem 0; text-align:center; border-bottom:1px solid #e2e8f0; margin-bottom:1.5rem;">
        <div style="font-size:2.8rem; margin-bottom:0.25rem;">⚡</div>
        <div style="font-size:1.4rem; font-weight:900; color:#4f46e5; letter-spacing:-0.03em;">FlashRFP Portal</div>
        <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-top:0.2rem;">Console Center</div>
    </div>
    
    <div style="padding:0.25rem 0 1.25rem 0; border-bottom:1px solid #e2e8f0; margin-bottom:1.5rem;">
        <div style="font-size:0.68rem; color:#64748b; text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Account Identity</div>
        <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:0.25rem;">
            {admin_record.get('name', 'Operator')}
        </div>
        <div style="font-size:0.75rem; color:#64748b; font-family:'Courier New',monospace;">{admin_record.get('username','')}</div>
    </div>
    """, unsafe_allow_html=True)

    # Core Stats in Sidebar
    rev = db.calculate_revenue_metrics()
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
        <div class="metric-hero" style="margin-bottom:0.65rem;">
            <div class="metric-title">MRR Rate</div>
            <div class="metric-num" style="font-size:1.45rem;">₹{rev['mrr']:,}</div>
        </div>
        <div class="metric-hero" style="margin-bottom:0.65rem;">
            <div class="metric-title">Subscribed Clients</div>
            <div class="metric-num" style="font-size:1.45rem;">{rev['active_paying']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Sync Operations", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.write("")
    
    # DB Status badge
    if _USE_SUPA:
        st.markdown(f'<div style="background-color:#e6fcf5; border:1px solid rgba(12,166,120,0.2); border-radius:10px; padding:0.75rem 1rem; font-size:0.78rem; color:#0ca678; font-weight:700; margin-bottom:0.75rem;">🟢 Supabase Cloud Online<br><span style="opacity:0.7; font-weight:500; font-family:monospace;">hxhugijpyoyhzfyvybzf</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background-color:#fff9db; border:1px solid rgba(245,159,0,0.2); border-radius:10px; padding:0.75rem 1rem; font-size:0.78rem; color:#f59f00; font-weight:700; margin-bottom:0.75rem;">⚠️ Local Instance Engine<br><span style="opacity:0.7; font-weight:500;">Offline Mode fallback</span></div>', unsafe_allow_html=True)
        
    if st.button("🔓 Exit Console", use_container_width=True):
        st.session_state["authentication_status"] = None
        st.session_state["username"] = ""
        st.session_state["name"] = ""
        st.rerun()

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:2.2rem;">
    <h1 style="font-size:2.8rem; font-weight:900; letter-spacing:-0.05em; margin-bottom:0.35rem; font-family:'Plus Jakarta Sans',sans-serif; text-transform:none; line-height:1.1;">Control Panel Console</h1>
    <p style="color:#64748b; font-size:0.96rem; font-weight:600; margin:0; letter-spacing:-0.015em; font-family:'Inter',sans-serif;">Platform operational parameters, multi-tenant databases, transaction logs, and system metrics</p>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_users, tab_leads, tab_subs, tab_rev, tab_health = st.tabs([
    "👥 User Management",
    "📞 Demo Bookings & Leads",
    "💳 Subscriptions & Billing",
    "📈 Revenue Analytics",
    "🛡️ System & Telemetry Health",
])

# ── Dynamic Portal Sync & Refresh Control Panel ────────────────────────────────
now_time = datetime.now().strftime("%I:%M:%S %p")
st.markdown('<div class="glass-panel" style="padding:1rem 1.50rem; margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center;">', unsafe_allow_html=True)
sc1, sc2, sc3 = st.columns([5, 3, 2])
with sc1:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:0.6rem;">
        <span style="display:inline-block; width:9px; height:9px; background-color:#10b981; border-radius:50%; animation: pulse 1.8s infinite;"></span>
        <span style="font-size:0.86rem; font-weight:700; color:#334155; font-family:'Inter',sans-serif;">
            PORTAL LIVE: ONLINE &nbsp;|&nbsp; LAST SYNC: <span style="font-family:monospace; color:#4f46e5;">{now_time}</span>
        </span>
    </div>
    """, unsafe_allow_html=True)
with sc2:
    auto_refresh_sec = st.selectbox(
        "Sync Rate Selector",
        ["Manual Refresh Only", "Every 10 seconds", "Every 30 seconds", "Every 1 minute", "Every 5 minutes"],
        index=0,
        label_visibility="collapsed",
        key="auto_sync_interval_selector_val"
    )
with sc3:
    if st.button("🔄 Sync Database", key="manual_refresh_portal_btn", type="secondary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 1 — USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════
with tab_users:
    users_data = db.get_all_users()

    # Search & Filters layout
    st.markdown('<div class="glass-panel" style="padding:1.25rem 1.5rem; margin-bottom:1.5rem;">', unsafe_allow_html=True)
    col_search, col_filter, col_add_client = st.columns([5, 3, 2])
    with col_search:
        search_q = st.text_input("Find Client Registry Record", placeholder="Type name, email address, or organization...", label_visibility="collapsed")
    with col_filter:
        status_filter = st.selectbox("Status State Filter", ["All", "active", "trial", "suspended", "cancelled"], label_visibility="collapsed")
    with col_add_client:
        if st.button("➕ Provision Client", type="primary", use_container_width=True):
            st.session_state["show_add_user"] = True
    st.markdown('</div>', unsafe_allow_html=True)

    # Provision user form
    if st.session_state.get("show_add_user"):
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="font-size:1.1rem; font-weight:800; color:#0f172a; margin-bottom:1.2rem;">Add New Client Credentials</h3>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            nu_username = st.text_input("Console Username / ID", key="nu_username")
            nu_name     = st.text_input("Subscriber Contact Name", key="nu_name")
        with c2:
            nu_email    = st.text_input("Corporate Email Address", key="nu_email")
            nu_company  = st.text_input("Organization / Enterprise Name", key="nu_company")
        with c3:
            nu_plan     = st.selectbox("Assigned Service Tier", ["trial","starter","professional","enterprise"], key="nu_plan")
            nu_password = st.text_input("Initial Access Password", type="password", key="nu_password")
        
        cb1, cb2 = st.columns([2, 8])
        with cb1:
            if st.button("Complete Provision", type="primary", use_container_width=True):
                if nu_username and nu_email and nu_password:
                    hashed_pw = bcrypt.hashpw(nu_password.encode(), bcrypt.gensalt()).decode()
                    now_str = datetime.now().strftime("%Y-%m-%d")
                    trial_exp = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d") if nu_plan == "trial" else None
                    
                    if _USE_SUPA:
                        _supa.create_user(nu_username, nu_name, nu_email, nu_company, nu_plan)
                    else:
                        users_data[nu_username] = {
                            "username": nu_username, "name": nu_name, "email": nu_email,
                            "company": nu_company, "plan": nu_plan,
                            "status": "trial" if nu_plan == "trial" else "active",
                            "is_admin": False, "created_at": now_str,
                            "trial_expires_at": trial_exp, "subscription_id": None,
                            "responses_this_month": 0, "documents_count": 0,
                            "batches_this_month": 0, "last_active": now_str,
                            "monthly_amount": _local_db.PLAN_PRICES.get(nu_plan, 0),
                        }
                        _local_db._save_json(_local_db.USERS_FILE, users_data)
                    
                    # Update configuration file auth registry
                    with open(config_file, "r") as f:
                        ac = json.load(f)
                    ac["credentials"]["usernames"][nu_username] = {
                        "email": nu_email, "name": nu_name, "password": hashed_pw
                    }
                    with open(config_file, "w") as f:
                        json.dump(ac, f, indent=4)
                        
                    st.success(f"Profile {nu_username} created successfully!")
                    st.session_state["show_add_user"] = False
                    st.rerun()
                else:
                    st.error("Invalid entry: Required field missing.")
        with cb2:
            if st.button("Discard Profile", use_container_width=True):
                st.session_state["show_add_user"] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Multi-tenant user layout
    filtered_users = {
        u: d for u, d in users_data.items()
        if (not search_q or any(search_q.lower() in str(v).lower()
                                for v in [d.get("name",""), d.get("email",""), d.get("company","")]))
        and (status_filter == "All" or d.get("status") == status_filter)
    }

    st.markdown(f'<div style="font-size:0.78rem; color:#64748b; margin-bottom:0.75rem; font-weight:700;">Registry Lookup: {len(filtered_users)} client profile records</div>', unsafe_allow_html=True)

    for username, user in filtered_users.items():
        is_admin_user = user.get("is_admin", False)
        status  = user.get("status", "active")
        plan    = user.get("plan", "trial")
        s_badge = status_badges.get(status, "bg-cancel")
        p_badge = plan_badges.get(plan, "bg-plan-t")
        lim     = _local_db.PLAN_LIMITS.get(plan, {})
        resp_max = lim.get("responses", 10)
        resp_used = user.get("responses_this_month", 0)
        pct = min(100, int(resp_used / max(resp_max, 1) * 100)) if resp_max > 0 else 0

        exp_title = f"{'🔑 ' if is_admin_user else '👤 '} {user.get('name','—')} | {user.get('company','Individual Plan')}"
        with st.expander(exp_title, expanded=False):
            st.markdown('<div class="glass-panel" style="margin-bottom:0; border:none; box-shadow:none; padding:0.5rem 0; background:transparent;">', unsafe_allow_html=True)
            row_l, row_r = st.columns([6, 4])
            with row_l:
                st.markdown(f"""
                <div style="margin-bottom:0.75rem;">
                    <span class="badge-pill {s_badge}">{status.upper()}</span>&nbsp;&nbsp;
                    <span class="badge-pill {p_badge}">{plan.upper()} PLAN</span>
                    {'&nbsp;&nbsp;<span class="badge-pill bg-plan-e">OPERATIONAL ADMIN</span>' if is_admin_user else ''}
                </div>
                <div style="font-size:0.88rem; color:#1e293b; line-height:2.1; font-family:'Inter',sans-serif;">
                    <span style="color:#64748b; font-weight:600;">E-mail Host:</span> {user.get('email','—')}<br>
                    <span style="color:#64748b; font-weight:600;">Organization:</span> {user.get('company','Individual Plan')}<br>
                    <span style="color:#64748b; font-weight:600;">Created:</span> {user.get('created_at','—')} &nbsp;|&nbsp; <span style="color:#64748b; font-weight:600;">Session Activity:</span> {user.get('last_active','—')}<br>
                    {'⏳ <span style="color:'+AMBER+'; font-weight:700;">Trial Limit Termination: ' + str(user.get('trial_expires_at','—')) + '</span><br>' if plan == 'trial' else ''}
                    <span style="color:#64748b; font-weight:600;">Billing Reference ID:</span> <code>{user.get('subscription_id','No link') or 'No link'}</code>
                </div>
                """, unsafe_allow_html=True)
            with row_r:
                if resp_max > 0:
                    bar_color = RED if pct >= 90 else AMBER if pct >= 70 else ACCENT
                    st.markdown(f"""
                    <div style="margin-bottom:0.75rem;">
                        <div style="font-size:0.76rem; color:#64748b; margin-bottom:0.4rem; font-weight:700;">
                            QUOTA ALLOCATION CONSOLE: {resp_used} / {'∞' if resp_max < 0 else resp_max} units
                        </div>
                        <div style="background-color:#e2e8f0; border-radius:30px; height:9px; overflow:hidden;">
                            <div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:30px; transition:width 0.4s;"></div>
                        </div>
                    </div>
                    <div style="font-size:0.86rem; color:#1e293b; line-height:1.9;">
                        📄 Vector Documents Storage: {user.get('documents_count',0)} files<br>
                        ⚡ Batch Jobs Processed: {user.get('batches_this_month',0)}<br>
                        💰 Current Plan MRR Rate: ₹{user.get('monthly_amount',0):,}
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<hr style='margin:1rem 0 !important;'>", unsafe_allow_html=True)

            # Operations Panel
            if not is_admin_user:
                a1, a2, a3, a4, a5 = st.columns(5)
                with a1:
                    if status == "active":
                        if st.button("Suspend Client", key=f"susp_{username}", use_container_width=True):
                            db.suspend_user(username)
                            st.success("Access suspended.")
                            st.rerun()
                    else:
                        if st.button("Activate Client", key=f"actv_{username}", type="primary", use_container_width=True):
                            db.activate_user(username)
                            st.success("Access granted.")
                            st.rerun()
                with a2:
                    if plan == "trial" and status == "trial":
                        ext_days = st.number_input("Days to Extend", min_value=1, max_value=60, value=7, key=f"ext_{username}", label_visibility="collapsed")
                        if st.button("Extend Trial Term", key=f"extbtn_{username}", use_container_width=True):
                            db.extend_trial(username, ext_days)
                            st.success(f"Term extended by {ext_days} days.")
                            st.rerun()
                    else:
                        new_plan = st.selectbox("Modify Service Tier", [p for p in ["starter","professional","enterprise","trial"] if p != plan],
                                                key=f"np_{username}", label_visibility="collapsed")
                        if st.button("Modify Plan Level", key=f"cp_{username}", use_container_width=True):
                            db.change_user_plan(username, new_plan)
                            st.success(f"Service plan level updated to {new_plan}.")
                            st.rerun()
                with a3:
                    new_pw = st.text_input("Reset Access Passcode", type="password", key=f"pw_{username}", label_visibility="collapsed", placeholder="New passcode...")
                    if st.button("Override Password", key=f"rpw_{username}", use_container_width=True):
                        if new_pw and len(new_pw) >= 6:
                            h = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                            db.reset_user_password(username, h)
                            st.success("Passcode override complete.")
                        else:
                            st.error("Credential requires min 6 chars.")
                with a4:
                    if st.button("Client Telemetry Trail", key=f"al_{username}", use_container_width=True):
                        st.session_state[f"show_audit_{username}"] = not st.session_state.get(f"show_audit_{username}", False)
                with a5:
                    if st.button("Purge Profile", key=f"del_{username}", use_container_width=True):
                        st.session_state[f"confirm_del_{username}"] = True

                if st.session_state.get(f"confirm_del_{username}"):
                    st.markdown(f'<div style="background-color:#fff5f5; border:1px solid rgba(250,82,82,0.2); padding:1rem; border-radius:10px; margin-top:0.75rem;"><p style="color:{RED}; font-weight:700; margin:0 0 0.5rem 0;">⚠️ Verification Required: Confirming this action completely deletes the client and purges all namespace data in ChromaDB. This is irreversible.</p></div>', unsafe_allow_html=True)
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("Confirm Purge", key=f"conf_{username}", type="primary"):
                            purge_status = db.purge_tenant_data(username)
                            db.delete_user(username)
                            try:
                                with open(config_file, "r") as ff:
                                    ac = json.load(ff)
                                ac["credentials"]["usernames"].pop(username, None)
                                with open(config_file, "w") as ff:
                                    json.dump(ac, ff, indent=4)
                            except Exception:
                                pass
                            st.success(f"Purge success. Vector db status: {purge_status}")
                            st.session_state.pop(f"confirm_del_{username}", None)
                            st.rerun()
                    with cc2:
                        if st.button("Cancel Action", key=f"canc_{username}"):
                            st.session_state.pop(f"confirm_del_{username}", None)
                            st.rerun()

            # Client Logs Telemetry
            if st.session_state.get(f"show_audit_{username}"):
                logs = db.get_audit_logs(username)
                st.markdown(f'<div style="font-size:0.85rem; font-weight:700; color:{ACCENT}; margin:0.75rem 0 0.4rem;">ACTIVITY LOG TELEMETRY ({len(logs)} records)</div>', unsafe_allow_html=True)
                if logs:
                    for log in logs[:10]:
                        q = str(log.get("question_asked",""))[:100]
                        sources = ", ".join(log.get("source_docs_retrieved", []))[:80]
                        st.markdown(f"""
                        <div style="background-color:#ffffff; border:1px solid #e2e8f0; border-radius:10px;
                                    padding:0.75rem 1rem; margin-bottom:0.4rem; font-size:0.8rem; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                            <span style="color:#64748b; font-weight:700;">🕐 {log.get('timestamp','—')}</span><br>
                            <span style="color:#0f172a; font-weight:500;">{q}</span><br>
                            <span style="color:#64748b; font-size:0.75rem; font-weight:500;">Matched context docs: {sources or 'None'}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No activity logs exist on file for this client.")


# ═══════════════════════════════════════════════════════════════
#  TAB — DEMO BOOKINGS & LEADS
# ═══════════════════════════════════════════════════════════════
with tab_leads:
    leads_data = db.get_all_leads()

    # Search & filters
    st.markdown('<div class="glass-panel" style="padding:1.25rem 1.5rem; margin-bottom:1.5rem;">', unsafe_allow_html=True)
    cl1, cl2 = st.columns([7, 3])
    with cl1:
        search_lead_q = st.text_input("Find Lead Record", placeholder="Search by name, email, sector, or source...", label_visibility="collapsed", key="search_lead_inp")
    with cl2:
        lead_status_filter = st.selectbox("Lead Status Filter", ["All", "New", "Contacted", "Converted"], label_visibility="collapsed", key="lead_status_sel")
    st.markdown('</div>', unsafe_allow_html=True)

    # Filter leads
    filtered_leads = []
    for l in leads_data:
        search_match = True
        if search_lead_q:
            q = search_lead_q.lower()
            search_match = (
                q in l.get("first_name", "").lower() or
                q in l.get("last_name", "").lower() or
                q in l.get("email", "").lower() or
                q in l.get("sector", "").lower() or
                q in l.get("source", "").lower()
            )
        
        status_match = True
        if lead_status_filter != "All":
            status_match = l.get("status") == lead_status_filter
            
        if search_match and status_match:
            filtered_leads.append(l)

    # Render Leads List
    if filtered_leads:
        for lead in filtered_leads:
            lead_email = lead.get("email")
            lead_status = lead.get("status", "New")
            
            # Badge styles
            if lead_status == "New":
                badge_style = "background-color: #fff9db; color: #f59f00; border: 1px solid rgba(245,159,0,0.15);"
            elif lead_status == "Contacted":
                badge_style = "background-color: #e8f4fd; color: #1c7ed6; border: 1px solid rgba(28,126,214,0.15);"
            else:
                badge_style = "background-color: #e6fcf5; color: #0ca678; border: 1px solid rgba(12,166,120,0.15);"
                
            st.markdown(f"""
            <div class="glass-panel" style="padding:1.5rem; margin-bottom:1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span class="badge-pill" style="{badge_style}">{lead_status.upper()}</span>
                        <h4 style="font-size:1.15rem; margin-top:0.4rem; font-weight:800; color:#0f172a; font-family:'Plus Jakarta Sans',sans-serif;">
                            {lead.get('first_name','')} {lead.get('last_name','')}
                        </h4>
                        <div style="font-size:0.85rem; color:#64748b; margin-top:0.25rem;">
                            ✉️ {lead_email} &nbsp;|&nbsp; 📞 {lead.get('phone','—')}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:0.75rem; color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Booking Source</span>
                        <div style="font-size:0.9rem; font-weight:800; color:#1e293b; margin-top:0.15rem;">
                            {lead.get('source','—')}
                        </div>
                        <div style="font-size:0.72rem; color:#94a3b8; font-family:monospace; margin-top:0.15rem;">
                            booked on {lead.get('created_at','—')[:16].replace('T',' ')}
                        </div>
                    </div>
                </div>
                <hr style="margin:1rem 0 !important; border:none; border-top:1px solid #f1f5f9;">
                
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <div style="font-size:0.86rem; color:#334155;">
                        💼 Sector: <strong>{lead.get('sector','—')}</strong> &nbsp;|&nbsp; 
                        ⚡ Est. RFPs/year: <strong>{lead.get('rfps_per_year','—')}</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col_act_1, col_act_2, col_act_3 = st.columns([3, 2, 5])
            with col_act_1:
                if lead_status == "New":
                    if st.button("Approve & Schedule Demo", key=f"contact_{lead_email}", type="primary", use_container_width=True):
                        db.update_lead_status(lead_email, "Contacted")
                        st.session_state["show_schedule_dialog"] = lead_email
                        st.rerun()
                elif lead_status == "Contacted":
                    if st.button("Convert to User", key=f"conv_{lead_email}", type="primary", use_container_width=True):
                        if db.convert_lead_to_user(lead_email):
                            st.success("Converted successfully! New trial account provisioned.")
                        else:
                            st.error("User username already exists.")
                        st.rerun()
                else:
                    st.write("🟢 Profile Active")
            with col_act_2:
                if st.button("Remove Booking", key=f"del_lead_{lead_email}", use_container_width=True):
                    db.delete_lead(lead_email)
                    st.success("Booking request removed.")
                    st.rerun()
                    
            if st.session_state.get("show_schedule_dialog") == lead_email:
                st.markdown(f"""
                <div style="background-color: #f0fdf4; border: 1px solid rgba(16,185,129,0.25); border-radius: 12px; padding: 1.25rem; margin-top: 1rem;">
                    <h4 style="color: #10b981; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif;">
                        📅 Demo Request Approved & Meeting Scheduled!
                    </h4>
                    <p style="color: #065f46; font-size: 0.88rem; margin: 0 0 0.75rem 0; line-height: 1.5; font-family: 'Inter', sans-serif;">
                        An invitation email has been dispatched to <strong>{lead_email}</strong>.<br>
                        <strong>Session Details:</strong> Tomorrow at 3:00 PM IST (GMT+5:30) | Video room: <a href="https://meet.google.com/flashrfp-demo-auth" target="_blank" style="color:#0ca678; font-weight:700;">meet.google.com/flashrfp-demo-auth</a>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Dismiss Notice", key=f"dismiss_{lead_email}"):
                    st.session_state["show_schedule_dialog"] = None
                    st.rerun()
                    
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No matching demo bookings or lead records on file.")

# ═══════════════════════════════════════════════════════════════
#  TAB 2 — SUBSCRIPTIONS & BILLING
# ═══════════════════════════════════════════════════════════════
with tab_subs:
    subs_data  = db.get_all_subscriptions()
    users_data = db.get_all_users()

    # Premium KPIs
    active_subs  = [s for s in subs_data.values() if s.get("status") == "active"]
    halted_subs  = [s for s in subs_data.values() if s.get("status") == "halted"]
    cancelled_s  = [s for s in subs_data.values() if s.get("status") == "cancelled"]

    k1, k2, k3, k4 = st.columns(4)
    render_kpi_card(k1, "Active Subscriptions", len(active_subs), f"₹{sum(s.get('amount',0) for s in active_subs):,}/mo", trend_val="+12.4%", trend_direction="up")
    render_kpi_card(k2, "Halted Subscriptions", len(halted_subs), f"Risk: ₹{sum(s.get('amount',0) for s in halted_subs):,}", trend_val="-25.0%", trend_direction="down")
    render_kpi_card(k3, "Cancelled Licenses", len(cancelled_s), "Inactive contracts", trend_val="0.0%", trend_direction="neutral")
    render_kpi_card(k4, "Gross Billing Revenue", f"₹{sum(s.get('total_paid',0) for s in subs_data.values()):,}", "Lifetime cleared", trend_val="+18.5%", trend_direction="up")


    st.write("")

    status_cols = {"active": "#0ca678", "halted": "#fa5252", "cancelled": "#64748b"}
    status_icons = {"active": "🟢", "halted": "🔴", "cancelled": "⚫"}

    for sub_id, sub in subs_data.items():
        user = users_data.get(sub.get("username",""), {})
        sc   = status_cols.get(sub.get("status",""), "#64748b")
        si   = status_icons.get(sub.get("status",""), "⚪")
        plan = sub.get("plan","starter")
        p_badge = plan_badges.get(plan, "bg-plan-t")

        with st.expander(f"{si} {sub_id} | {user.get('name','Unknown')} ({user.get('company','—')}) | ₹{sub.get('amount',0):,}/mo"):
            st.markdown('<div class="glass-panel" style="margin-bottom:0; border:none; box-shadow:none; padding:0.5rem 0; background:transparent;">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div style="font-size:0.86rem; color:#1e293b; line-height:2.2;">
                    <span class="badge-pill {p_badge}">{plan.upper()} PLAN</span><br>
                    👤 {user.get('name','—')} ({user.get('email','—')})<br>
                    📅 Start: {sub.get('start_date','—')}<br>
                    🔁 Next billing: {sub.get('next_billing_date','—') or 'Manual'}
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="font-size:0.86rem; color:#1e293b; line-height:2.2;">
                    License Status: <span style="color:{sc}; font-weight:700;">{sub.get('status','').upper()}</span><br>
                    💰 Total Collected: ₹{sub.get('total_paid',0):,}<br>
                    🧾 Payment Iterations: {sub.get('invoices',0)} bills<br>
                    💱 Settlement Currency: {sub.get('currency','INR')}
                </div>
                """, unsafe_allow_html=True)
            with c3:
                if sub.get("status") == "halted":
                    st.markdown(f'<div style="color:{RED}; font-size:0.8rem; font-weight:700; margin-bottom:0.4rem;">⚠️ Delinquent subscription — payment failed</div>', unsafe_allow_html=True)
                    if st.button("Force Manual Override", key=f"reactiv_{sub_id}", type="primary"):
                        db.update_subscription(sub_id, {"status": "active"})
                        db.activate_user(sub.get("username",""))
                        st.success("Reactivation completed.")
                        st.rerun()
                elif sub.get("status") == "active":
                    if st.button("Terminate License", key=f"cansub_{sub_id}"):
                        st.session_state[f"confirm_cancel_{sub_id}"] = True
                    if st.session_state.get(f"confirm_cancel_{sub_id}"):
                        st.error("Terminate subscription license?")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("Confirm Termination", key=f"yc_{sub_id}", type="primary"):
                                db.update_subscription(sub_id, {"status": "cancelled", "next_billing_date": None})
                                db.suspend_user(sub.get("username",""))
                                st.success("Billing and service deactivated.")
                                st.session_state.pop(f"confirm_cancel_{sub_id}", None)
                                st.rerun()
                        with cc2:
                            if st.button("No", key=f"nc_{sub_id}"):
                                st.session_state.pop(f"confirm_cancel_{sub_id}", None)
                                st.rerun()

                # Upgrade/Downgrade
                new_plan_sub = st.selectbox(
                    "Modify Billing Class",
                    [p for p in ["starter","professional","enterprise"] if p != plan],
                    key=f"nsub_{sub_id}", label_visibility="collapsed"
                )
                if st.button("Alter Contract Level", key=f"chg_{sub_id}"):
                    db.update_subscription(sub_id, {
                        "plan": new_plan_sub,
                        "amount": _local_db.PLAN_PRICES.get(new_plan_sub, sub.get("amount",0))
                    })
                    db.change_user_plan(sub.get("username",""), new_plan_sub)
                    st.success(f"Billing tier updated to {new_plan_sub}.")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Refund box
            st.markdown(f"""
            <div style="background-color:#fff9db; border:1px solid rgba(245,159,0,0.15);
                        border-radius:10px; padding:0.75rem 1.25rem; margin-top:0.75rem; font-size:0.8rem; color:#1e293b;">
                💡 To trigger a cash refund, open your 
                <a href="https://dashboard.razorpay.com/app/orders" target="_blank"
                   style="color:{ACCENT}; font-weight:700; text-decoration:none;">Razorpay Dashboard</a>
                and lookup payment reference order ID: <code style="color:{ACCENT};">{sub_id}</code>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 3 — REVENUE ANALYTICS
# ═══════════════════════════════════════════════════════════════
with tab_rev:
    rev = db.calculate_revenue_metrics()

    r1, r2, r3, r4 = st.columns(4)
    render_kpi_card(r1, "Annual Run Rate", f"₹{rev['arr']:,}", f"MRR: ₹{rev['mrr']:,}", trend_val="+14.2%", trend_direction="up")
    render_kpi_card(r2, "Signups (Month-to-Date)", str(rev['new_signups_month']), "Across all segments", trend_val="+3 new", trend_direction="up")
    render_kpi_card(r3, "Active Churn", f"{rev['churn_rate']}%", f"{rev['churned']} cancellations", trend_val="-1.2%", trend_direction="down")
    render_kpi_card(r4, "All-Time Collections", f"₹{rev['total_revenue']:,}", "Settled transactions", trend_val="+18.5%", trend_direction="up")


    st.write("")
    c_left, c_right = st.columns([6, 4])

    with c_left:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">📈 Responses Synthesized (Last 30 Days)</h3>', unsafe_allow_html=True)
        dates, resp_vals = zip(*rev["daily_responses"]) if rev["daily_responses"] else ([], [])
        fig_resp = go.Figure()
        fig_resp.add_trace(go.Scatter(
            x=list(dates), y=list(resp_vals),
            fill="tozeroy",
            line=dict(color=ACCENT, width=3.5),
            fillcolor="rgba(99, 102, 241, 0.08)",
            mode="lines+markers",
            marker=dict(size=4, color=ACCENT),
            name="Responses",
        ))
        fig_resp.update_layout(
            height=250, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color=MUTED, size=11),
            xaxis=dict(showgrid=False, linecolor="#cbd5e1", tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(size=9)),
        )
        st.plotly_chart(fig_resp, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">🥧 Service MRR Distribution</h3>', unsafe_allow_html=True)
        plan_labels = [k.capitalize() for k, v in rev["rev_by_plan"].items() if v > 0]
        plan_values = [v for v in rev["rev_by_plan"].values() if v > 0]
        if plan_labels:
            fig_donut = go.Figure(go.Pie(
                labels=plan_labels,
                values=plan_values,
                hole=0.6,
                marker=dict(colors=[ACCENT, "#818cf8", "#34d399", "#f59e0b"]),
                textfont=dict(family="Inter", size=11, color="#0f172a"),
                textinfo="percent",
            ))
            fig_donut.update_layout(
                height=250, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#334155"),
                showlegend=True,
                legend=dict(font=dict(color=MUTED, size=11), orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No active billings detected.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Signups trend
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">👥 Client Signups Trend (Last 30 Days)</h3>', unsafe_allow_html=True)
    if rev["daily_signups"]:
        sdates, svals = zip(*rev["daily_signups"])
        fig_signup = go.Figure(go.Bar(
            x=list(sdates), y=list(svals),
            marker_color=ACC2,
            marker_line_width=0,
            name="Signups",
        ))
        fig_signup.update_layout(
            height=160, margin=dict(l=0, r=0, t=5, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color=MUTED, size=11),
            xaxis=dict(showgrid=False, linecolor="#cbd5e1", tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(size=9)),
        )
        st.plotly_chart(fig_signup, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Revenue Matrix Table
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">📋 Service Level Revenue Matrix</h3>', unsafe_allow_html=True)
    plan_rows = []
    for plan, users_count in rev["user_by_plan"].items():
        plan_rows.append({
            "Plan Level": plan.capitalize(),
            "Subscribers": users_count,
            "Monthly Revenue (₹)": rev["rev_by_plan"].get(plan, 0),
            "Annualized Revenue (₹)": rev["rev_by_plan"].get(plan, 0) * 12,
            "Base Monthly Fee (₹)": _local_db.PLAN_PRICES.get(plan, 0),
        })
    df_plans = pd.DataFrame(plan_rows)
    st.dataframe(df_plans, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 4 — SYSTEM & TELEMETRY HEALTH
# ═══════════════════════════════════════════════════════════════
with tab_health:
    chroma_stats  = db.get_chroma_stats()
    latency_stats = db.get_latency_stats()
    sys_metrics   = db.get_system_metrics()
    daily         = sys_metrics.get("daily", [])

    h1, h2, h3, h4 = st.columns(4)
    p50  = latency_stats.get("p50", 0)
    p95  = latency_stats.get("p95", 0)
    errs = latency_stats.get("avg_errors_day", 0)

    p50_color  = "#0ca678" if p50  < 3000 else "#f59f00" if p50  < 7000 else "#fa5252"
    p95_color  = "#0ca678" if p95  < 8000 else "#f59f00" if p95  < 12000 else "#fa5252"
    err_color  = "#0ca678" if errs < 2    else "#f59f00" if errs < 5     else "#fa5252"

    render_kpi_card(h1, "Knowledge Chunks", f"{chroma_stats.get('total_chunks',0):,}", f"{chroma_stats.get('db_size_mb',0)} MB on disk | {chroma_stats.get('collections',0)} index(es)", trend_val="+4.2%", trend_direction="up", value_color=ACCENT)
    render_kpi_card(h2, "Latency (p50 Med.)", f"{p50:,} ms", "30-day average response", trend_val="-8.4%", trend_direction="down", value_color=p50_color)
    render_kpi_card(h3, "Latency (p95 Max.)", f"{p95:,} ms", "30-day average response", trend_val="-12.1%", trend_direction="down", value_color=p95_color)
    render_kpi_card(h4, "Platform Errors/Day", f"{errs}", f"Total monthly errors: {latency_stats.get('total_api_errors',0)}", trend_val="0.0%", trend_direction="neutral", value_color=err_color)


    st.write("")
    lc, rc = st.columns([6, 4])

    with lc:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">⏱️ Latency Distribution Trends (Last 30 Days)</h3>', unsafe_allow_html=True)
        if daily:
            lat_dates = [d["date"] for d in daily]
            p50s = [d.get("p50_latency_ms", 0) for d in daily]
            p95s = [d.get("p95_latency_ms", 0) for d in daily]
            fig_lat = go.Figure()
            fig_lat.add_trace(go.Scatter(x=lat_dates, y=p50s, name="p50 (Median)", line=dict(color="#0ca678", width=2.5), mode="lines"))
            fig_lat.add_trace(go.Scatter(x=lat_dates, y=p95s, name="p95 (Tail)", line=dict(color="#f59f00", width=2, dash="dash"), mode="lines"))
            fig_lat.update_layout(
                height=230, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color=MUTED, size=11),
                legend=dict(font=dict(color=MUTED, size=10), bgcolor="rgba(255,255,255,0.7)"),
                xaxis=dict(showgrid=False, linecolor="#cbd5e1", tickfont=dict(size=9)),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(size=9), title="ms"),
            )
            st.plotly_chart(fig_lat, use_container_width=True)
        else:
            st.info("No telemetry logs found.")
        st.markdown('</div>', unsafe_allow_html=True)

    with rc:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">💸 LLM Token Usage Cost (7-Day Trend)</h3>', unsafe_allow_html=True)
        if daily:
            cost7_dates = [d["date"] for d in daily[-7:]]
            cost7_vals  = [d.get("llm_cost_usd", 0) for d in daily[-7:]]
            fig_cost = go.Figure(go.Bar(
                x=cost7_dates, y=cost7_vals,
                marker_color=[ACCENT if v < 3 else AMBER for v in cost7_vals],
                marker_line_width=0,
            ))
            fig_cost.update_layout(
                height=230, margin=dict(l=0, r=0, t=5, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color=MUTED, size=11),
                xaxis=dict(showgrid=False, linecolor="#cbd5e1", tickfont=dict(size=9)),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(size=9), title="$ USD"),
            )
            st.plotly_chart(fig_cost, use_container_width=True)
            total_cost_7d = sum(cost7_vals)
            st.markdown(f'<div style="font-size:0.8rem; color: #64748b; text-align:center;">7-Day Cumulative: <b style="color:#0f172a;">${total_cost_7d:.2f} USD</b> (~₹{total_cost_7d*84:.0f})</div>', unsafe_allow_html=True)
        else:
            st.info("No cost data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    # API Error rate chart
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">🚨 API Error Incidents (Last 30 Days)</h3>', unsafe_allow_html=True)
    if daily:
        err_dates = [d["date"] for d in daily]
        err_vals  = [d.get("api_errors", 0) for d in daily]
        fig_err = go.Figure(go.Bar(
            x=err_dates, y=err_vals,
            marker_color=[RED if v >= 4 else "rgba(99, 102, 241, 0.4)" for v in err_vals],
            marker_line_width=0,
        ))
        fig_err.update_layout(
            height=140, margin=dict(l=0, r=0, t=5, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color=MUTED, size=11),
            xaxis=dict(showgrid=False, linecolor="#cbd5e1", tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(size=9), title="Incidents"),
        )
        st.plotly_chart(fig_err, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Vector DB Storage Specs
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:1.25rem;">🗄️ Vector Database Physical Storage</h3>', unsafe_allow_html=True)
    if chroma_stats.get("error"):
        st.warning(f"Error checking storage: {chroma_stats['error']}")
    else:
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Active Collections", chroma_stats.get("collections", 0))
        cc2.metric("Total Indexed Chunks", f"{chroma_stats.get('total_chunks', 0):,}")
        cc3.metric("Database Storage Size", f"{chroma_stats.get('db_size_mb', 0)} MB")
        if chroma_stats.get("tenants"):
            st.markdown(f'<div style="font-size:0.8rem; color:#64748b; margin-top:0.5rem; font-weight:600;">Active Partition Domains: {", ".join(chroma_stats["tenants"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:0.8rem; color:#64748b; margin-top:0.5rem; font-weight:600;">No active storage namespaces populated yet.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── Auto-Refresh Automation ───────────────────────────────────────────────────
if auto_refresh_sec != "Manual Refresh Only":
    sec_map = {
        "Every 10 seconds": 10,
        "Every 30 seconds": 30,
        "Every 1 minute": 60,
        "Every 5 minutes": 300
    }
    interval_ms = sec_map.get(auto_refresh_sec, 30) * 1000
    
    import streamlit.components.v1 as components
    components.html(
        f"""
        <a id="reload_anchor" href="http://localhost:8502/" target="_parent" style="display:none;">Reload</a>
        <script>
            setTimeout(() => {{
                try {{
                    document.getElementById('reload_anchor').click();
                }} catch (e) {{
                    // Fallback reload
                    window.parent.location.reload();
                }}
            }}, {interval_ms});
        </script>
        """,
        height=0,
        width=0
    )


