import os
import time
import uuid
# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from rag_engine import (
    get_chroma_client,
    get_or_create_collection,
    ingest_document,
    query_knowledge_base,
    generate_rfp_response,
    extract_questions_from_pdf,
    batch_process_rfp_questions,
    ingest_documents_batch,
    delete_document_from_kb,
    build_provider_pool
)
from exporter import (
    generate_docx_stream,
    generate_batch_docx_stream,
    fill_rfp_docx_template,
    generate_advanced_proposal_docx,
    render_export_button
)
from roi_tracker import (
    init_roi_tracker,
    log_ai_performance,
    calculate_roi,
    render_roi_dashboard,
    render_roi_dashboard_main
)

# Load environment variables — local .env first, then Streamlit Cloud secrets override
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

def _cfg(key: str, default: str = "") -> str:
    """Read config from st.secrets (Streamlit Cloud) first, then os.environ/.env."""
    try:
        val = st.secrets.get(key, None)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

# Page configuration
st.set_page_config(
    page_title="FlashRFP AI — Proposal Engine",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================= Authentication Layer =================
# pyrefly: ignore [missing-import]
import streamlit_authenticator as stauth
import json

config_file = os.path.join(base_dir, "auth_config.json")
if not os.path.exists(config_file):
    # Default admin user with bcrypt password: 'admin123'
    default_config = {
        "credentials": {
            "usernames": {
                "admin": {
                    "email": "admin@flashrfp.ai",
                    "name": "Administrator",
                    "password": "$2b$12$EZTELUZjs78b28YedCXD3OgAl5/SvQcVtUsy48huU5THS4MzR2CBe"
                }
            }
        },
        "cookie": {
            "expiry_days": 30,
            "key": "flashrfp_cookie_key_secret_987654",
            "name": "flashrfp_auth_cookie"
        }
    }
    with open(config_file, "w") as f:
        json.dump(default_config, f, indent=4)
else:
    with open(config_file, "r") as f:
        try:
            default_config = json.load(f)
        except Exception:
            default_config = {
                "credentials": {"usernames": {}},
                "cookie": {"expiry_days": 30, "key": "flashrfp_cookie_key_secret_987654", "name": "flashrfp_auth_cookie"}
            }

authenticator = stauth.Authenticate(
    default_config['credentials'],
    default_config['cookie']['name'],
    default_config['cookie']['key'],
    default_config['cookie']['expiry_days']
)

# Render login widget
try:
    authenticator.login(location='main')
except Exception as login_err:
    st.error(f"Login widget error: {login_err}")

if not st.session_state.get("authentication_status"):
    if st.session_state.get("authentication_status") is False:
        st.error("Username/password is incorrect")
    elif st.session_state.get("authentication_status") is None:
        st.info("Welcome! Please log in or create an account to start using the RFP Response Engine.")
        
    st.write("")
    # Allow registration of new user
    show_reg = st.toggle("Create an Account / Register New User")
    if show_reg:
        try:
            reg_res = authenticator.register_user(
                location='main',
                captcha=False
            )
            if reg_res:
                email_of_registered_user, username_of_registered_user, name_of_registered_user = reg_res
                if username_of_registered_user:
                    default_config['credentials'] = authenticator.credentials
                    with open(config_file, "w") as f:
                        json.dump(default_config, f, indent=4)
                    st.success("Registration successful! You can now log in using the form above.")
        except Exception as e:
            st.error(f"Registration error: {e}")
    st.stop()

# ── 7-Day Trial & Razorpay Subscription Paywall Gate ─────────────────────────
from auth_db import add_user, check_trial_status, upgrade_user_plan, get_trial_days_remaining

# Resolve email from user session credentials
curr_username = st.session_state.get("username", "")
user_email = default_config.get('credentials', {}).get('usernames', {}).get(curr_username, {}).get("email", "")
if not user_email:
    user_email = f"{curr_username}@flashrfp.ai"

# Initialize in local trial database
add_user(user_email)

# Verify trial status
is_trial_active, current_plan = check_trial_status(user_email)
trial_days = get_trial_days_remaining(user_email)

# Razorpay subscription direct payment endpoints
RAZORPAY_LINKS = {
    "Growth": "https://rzp.io/rzp/4tjCO7XE",
    "Scale": "https://rzp.io/rzp/ZJmTZz3",
    "Enterprise": "https://rzp.io/rzp/oYCY6c2"
}

if not is_trial_active and current_plan == 'trial_expired':
    st.markdown("""
    <style>
    .paywall-bg {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2f6 100%);
        min-height: 100vh;
        padding: 4rem 2rem;
    }
    .paywall-container {
        max-width: 1100px;
        margin: 0 auto;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    .paywall-header {
        text-align: center;
        margin-bottom: 3.5rem;
    }
    .paywall-badge {
        display: inline-block;
        background-color: #fee2e2;
        color: #ef4444;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 0.35rem 0.85rem;
        border-radius: 30px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
        border: 1px solid rgba(239, 68, 68, 0.15);
    }
    .paywall-title {
        font-size: 2.25rem;
        font-weight: 900;
        color: #0f172a;
        letter-spacing: -0.04em;
        margin-bottom: 0.5rem;
    }
    .paywall-subtitle {
        font-size: 1rem;
        color: #64748b;
        font-weight: 500;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Paywall Pricing Cards */
    .paywall-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 480px;
        position: relative;
    }
    .paywall-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: rgba(99, 102, 241, 0.35);
    }
    .paywall-card.featured {
        border-color: #6366f1;
        box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.15);
    }
    .paywall-card.featured::before {
        content: 'RECOMMENDED';
        position: absolute;
        top: 1rem; right: 1rem;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: #ffffff;
        font-size: 0.65rem;
        font-weight: 800;
        padding: 0.25rem 0.65rem;
        border-radius: 30px;
        letter-spacing: 0.05em;
    }
    .plan-name {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    .plan-price {
        font-size: 2.25rem;
        font-weight: 900;
        color: #0f172a;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
    }
    .plan-period {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }
    .plan-features {
        list-style: none;
        padding: 0; margin: 0 0 2rem;
        border-top: 1px solid #e2e8f0;
        padding-top: 1.5rem;
    }
    .plan-features li {
        font-size: 0.88rem;
        color: #334155;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;
    }
    .plan-features li::before {
        content: '✓';
        color: #10b981;
        font-weight: 800;
    }
    .discount-ribbon {
        background-color: #ecfdf5;
        color: #065f46;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.4rem 0.85rem;
        border-radius: 8px;
        border: 1px solid rgba(16, 185, 129, 0.2);
        margin-bottom: 1.5rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="paywall-container">
        <div class="paywall-header">
            <span class="paywall-badge">Trial Expired</span>
            <div class="paywall-title">Choose Your Service Plan</div>
            <div class="paywall-subtitle">Upgrade to continue generating enterprise-grade winning RFP proposals in seconds with secure tenant isolation.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="paywall-card">
            <div>
                <div class="plan-name">Growth Tier</div>
                <div class="plan-price">₹15,000</div>
                <div class="plan-period">per month, billed annually</div>
                <div class="discount-ribbon">🎁 10% Launch Discount Applied</div>
                <ul class="plan-features">
                    <li>5 Active Concurrent RFPs</li>
                    <li>3 Consolidated User Seats</li>
                    <li>50 Document Indexes</li>
                    <li>Secure RAG Vector Partition</li>
                    <li>Standard SLA Support</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Upgrade to Growth", RAZORPAY_LINKS["Growth"], use_container_width=True, type="secondary")
        
    with col2:
        st.markdown("""
        <div class="paywall-card featured">
            <div>
                <div class="plan-name">Scale Tier</div>
                <div class="plan-price">₹25,000</div>
                <div class="plan-period">per month, billed annually</div>
                <div class="discount-ribbon">🔥 Recommended & Best Value Plan</div>
                <ul class="plan-features">
                    <li>20 Active Concurrent RFPs</li>
                    <li>10 Consolidated User Seats</li>
                    <li>500 Document Indexes</li>
                    <li>Dedicated Priority Vector Index</li>
                    <li>24/7 SLA Priority Support</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Upgrade to Scale", RAZORPAY_LINKS["Scale"], use_container_width=True, type="primary")
        
    with col3:
        st.markdown("""
        <div class="paywall-card">
            <div>
                <div class="plan-name">Enterprise Tier</div>
                <div class="plan-price">₹55,000</div>
                <div class="plan-period">per month, billed annually</div>
                <div class="discount-ribbon">💼 Complete Dedicated Architecture</div>
                <ul class="plan-features">
                    <li>Unlimited RFPs & Batches</li>
                    <li>30 Consolidated User Seats</li>
                    <li>Unlimited Documents</li>
                    <li>Dedicated Vector Instance</li>
                    <li>Custom Legal SLA Contracts</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Upgrade to Enterprise", RAZORPAY_LINKS["Enterprise"], use_container_width=True, type="secondary")

    # Developer Testing Simulator Block
    st.write("")
    st.write("")
    with st.expander("🔧 [For Testing] Upgrade Simulator Console"):
        st.markdown("<p style='font-size:0.85rem; color:#64748b;'>Select a paid tier to simulate a successful Razorpay callback settlement and bypass the paywall gate.</p>", unsafe_allow_html=True)
        sim_plan = st.selectbox("Simulated Plan", ["starter", "professional", "enterprise"])
        if st.button("Unlock Sandbox Mode", type="primary"):
            upgrade_user_plan(user_email, sim_plan)
            st.success(f"Sandbox upgraded user plan to {sim_plan.upper()}!")
            st.rerun()
            
    st.stop()  # Lock out app execution

# ── Theme Settings & Presets ───────────────────────────────────────────────────
if "theme_preset" not in st.session_state:
    st.session_state.theme_preset = "emerald_aurora"

preset = st.session_state.theme_preset

if preset == "midnight_obsidian":
    IS_DARK = True
    page_bg      = "radial-gradient(at 10% 10%, rgba(16, 185, 129, 0.12) 0px, transparent 50%), radial-gradient(at 90% 90%, rgba(15, 23, 42, 0.95) 0px, transparent 50%), linear-gradient(135deg, #070B12 0%, #0F172A 50%, #030806 100%)"
    glass_bg     = "rgba(15, 23, 42, 0.75)"
    glass_border = "rgba(16, 185, 129, 0.22)"
    glass_hover  = "rgba(16, 185, 129, 0.08)"
    text         = "#F8FAFC"
    text_muted   = "#94A3B8"
    text_dim     = "#64748B"
    accent       = "#10B981"
    accent2      = "#059669"
    glow         = "rgba(16, 185, 129, 0.35)"
    glow2        = "rgba(5, 150, 105, 0.25)"
    badge_bg     = "rgba(16, 185, 129, 0.15)"
    badge_text   = "#34D399"
    green        = "#34D399"
    green_bg     = "rgba(52, 211, 153, 0.14)"
    red          = "#F87171"
    red_bg       = "rgba(248, 113, 113, 0.14)"
    tab_active   = "rgba(16, 185, 129, 0.2)"
    tab_bg       = "rgba(15, 23, 42, 0.6)"
    input_bg     = "#0F172A"
    metric_bg    = "rgba(16, 185, 129, 0.08)"
    glossy_tab_bg = "linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(7, 11, 18, 0.9) 100%)"
    glossy_tab_border = "rgba(16, 185, 129, 0.25)"
    glossy_tab_active = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
    glossy_tab_active_border = "#10B981"

elif preset == "nordic_slate":
    IS_DARK = False
    page_bg      = "linear-gradient(180deg, #F1F5F9 0%, #E2E8F0 100%)"
    glass_bg     = "#FFFFFF"
    glass_border = "#CBD5E1"
    glass_hover  = "#F8FAFC"
    text         = "#0F172A"
    text_muted   = "#475569"
    text_dim     = "#94A3B8"
    accent       = "#10B981"
    accent2      = "#059669"
    glow         = "rgba(16, 185, 129, 0.15)"
    glow2        = "rgba(5, 150, 105, 0.1)"
    badge_bg     = "rgba(16, 185, 129, 0.08)"
    badge_text   = "#059669"
    green        = "#10B981"
    green_bg     = "rgba(16, 185, 129, 0.08)"
    red          = "#EF4444"
    red_bg       = "rgba(239, 68, 68, 0.08)"
    tab_active   = "#E2E8F0"
    tab_bg       = "#F1F5F9"
    input_bg     = "#FFFFFF"
    metric_bg    = "#F8FAFC"
    glossy_tab_bg = "#FFFFFF"
    glossy_tab_border = "#CBD5E1"
    glossy_tab_active = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
    glossy_tab_active_border = "#10B981"

elif preset == "royal_indigo":
    IS_DARK = False
    page_bg      = "radial-gradient(at 10% 10%, rgba(99, 102, 241, 0.12) 0px, transparent 50%), radial-gradient(at 90% 90%, rgba(16, 185, 129, 0.10) 0px, transparent 50%), #F8FAFC"
    glass_bg     = "rgba(255, 255, 255, 0.95)"
    glass_border = "rgba(99, 102, 241, 0.18)"
    glass_hover  = "#FFFFFF"
    text         = "#1E1B4B"
    text_muted   = "#4338CA"
    text_dim     = "#6366F1"
    accent       = "#10B981"
    accent2      = "#6366F1"
    glow         = "rgba(99, 102, 241, 0.2)"
    glow2        = "rgba(16, 185, 129, 0.12)"
    badge_bg     = "rgba(99, 102, 241, 0.1)"
    badge_text   = "#4338CA"
    green        = "#10B981"
    green_bg     = "rgba(16, 185, 129, 0.08)"
    red          = "#EF4444"
    red_bg       = "rgba(239, 68, 68, 0.08)"
    tab_active   = "rgba(99, 102, 241, 0.1)"
    tab_bg       = "#F1F5F9"
    input_bg     = "#FFFFFF"
    metric_bg    = "rgba(99, 102, 241, 0.05)"
    glossy_tab_bg = "#FFFFFF"
    glossy_tab_border = "rgba(99, 102, 241, 0.2)"
    glossy_tab_active = "linear-gradient(135deg, #10B981 0%, #6366F1 100%)"
    glossy_tab_active_border = "#10B981"

else:  # "emerald_aurora" (Default)
    IS_DARK = False
    page_bg      = "radial-gradient(at 10% 10%, rgba(16, 185, 129, 0.08) 0px, transparent 50%), radial-gradient(at 90% 90%, rgba(59, 130, 246, 0.06) 0px, transparent 50%), #FAFAFA"
    glass_bg     = "rgba(255, 255, 255, 0.95)"
    glass_border = "#E5E7EB"
    glass_hover  = "#FFFFFF"
    text         = "#111827"
    text_muted   = "#4B5563"
    text_dim     = "#9CA3AF"
    accent       = "#10B981"
    accent2      = "#059669"
    glow         = "rgba(16, 185, 129, 0.15)"
    glow2        = "rgba(5, 150, 105, 0.1)"
    badge_bg     = "rgba(16, 185, 129, 0.08)"
    badge_text   = "#059669"
    green        = "#10B981"
    green_bg     = "rgba(16, 185, 129, 0.08)"
    red          = "#EF4444"
    red_bg       = "rgba(239, 68, 68, 0.08)"
    tab_active   = "rgba(16, 185, 129, 0.08)"
    tab_bg       = "#F5F5F5"
    input_bg     = "#FFFFFF"
    metric_bg    = "#F5F5F5"
    glossy_tab_bg = "#FFFFFF"
    glossy_tab_border = "#E5E7EB"
    glossy_tab_active = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
    glossy_tab_active_border = "#10B981"

def inject_custom_css():
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
    
    *, *::before, *::after {{ box-sizing: border-box; }}
    
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], main, .main {{
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: {page_bg} !important;
        min-height: 100vh;
        color: {text} !important;
    }}
    
    section[data-testid="stSidebar"] {{
        background: {glass_bg} !important;
        border-right: 1px solid {glass_border} !important;
    }}
    
    header[data-testid="stHeader"], #MainMenu, footer,
    [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], .stDeployButton {{ display: none !important; }}
    
    /* Remove Streamlit default top spacing above main block container */
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"],
    div[data-testid="stMain"] > div:first-child,
    .main .block-container,
    .block-container {{
        padding-top: 0.5rem !important;
        margin-top: 0px !important;
    }}
    
    .block-container {{
        padding: 0.5rem 2.5rem 4rem !important;
        max-width: 1320px !important;
        margin: 0 auto;
        position: relative; z-index: 1;
    }}
    
    /* HeroUI v3 Typography */
    p, li, label, .stMarkdown {{
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif !important;
        color: {text} !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        color: {text} !important; font-weight: 800; letter-spacing: -0.035em;
    }}
    
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {accent}; border-radius: 10px; }}
    
    /* HeroUI v3 Cards & Glassmorphic Panels */
    .glass-card {{
        background: {glass_bg};
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid {glass_border};
        border-radius: 20px;
        padding: 1.85rem 2.25rem;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        margin-bottom: 1.5rem;
        position: relative; overflow: hidden;
    }}
    .glass-card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #10b981 0%, #06b6d4 100%);
        border-radius: 20px 20px 0 0; opacity: 0.85;
    }}
    .glass-card:hover {{
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: 0 16px 36px -4px rgba(16, 185, 129, 0.12), 0 4px 12px -2px rgba(0, 0, 0, 0.03);
        transform: translateY(-2px);
    }}
    
    .brand-logo {{
        display: flex; align-items: center; justify-content: center;
        width: 44px; height: 44px;
        flex-shrink: 0;
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .brand-logo:hover {{
        transform: translateY(-2px) scale(1.08);
    }}
    .brand-name {{
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        font-size: 1.85rem; 
        font-weight: 800; 
        letter-spacing: -0.03em;
        color: {text} !important;
        background: none !important;
        -webkit-text-fill-color: {text} !important;
        display: inline-block;
        line-height: 1.1;
    }}
    .brand-tagline {{ 
        display: none !important;
    }}
    
    /* HeroUI v3 Floating Segmented Nav Tabs */
    div[role="tablist"] {{
        gap: 6px !important; 
        background: {glossy_tab_bg} !important;
        backdrop-filter: blur(28px) saturate(210%) !important;
        border: 1px solid {glossy_tab_border} !important;
        border-radius: 16px !important; padding: 6px !important;
        margin-bottom: 2rem !important;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.05), 0 2px 6px -1px rgba(0, 0, 0, 0.03) !important;
    }}
    div[role="tab"] {{
        background: transparent !important;
        padding: 0.75rem 1.65rem !important; 
        border: 1px solid transparent !important;
        border-bottom: none !important;
        box-shadow: none !important;
        border-radius: 12px !important; 
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
    }}
    div[role="tab"] > div {{
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }}
    div[role="tab"] *, 
    div[role="tab"] p, 
    div[role="tab"] span {{
        font-size: 1.02rem !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        color: #4b5563 !important;
        transition: color 0.25s ease !important;
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
    }}
    div[role="tab"]:hover {{ 
        background: rgba(16, 185, 129, 0.08) !important; 
        transform: translateY(-1px) !important;
    }}
    div[role="tab"]:hover *, 
    div[role="tab"]:hover p, 
    div[role="tab"]:hover span {{
        color: {accent} !important;
    }}
    div[role="tab"][aria-selected="true"] {{
        background: {glossy_tab_active} !important;
        border: 1px solid {glossy_tab_active_border} !important;
        box-shadow: 0 6px 20px -2px rgba(16, 185, 129, 0.35) !important;
        transform: scale(1.01) !important;
    }}
    div[role="tab"][aria-selected="true"] *, 
    div[role="tab"][aria-selected="true"] p, 
    div[role="tab"][aria-selected="true"] span {{
        font-weight: 800 !important;
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25) !important;
    }}
    
    /* Hide Streamlit native underline indicator completely */
    div[data-testid="stTabHeader"] div,
    div[data-testid="stTabHeader"] div *,
    div[role="tablist"] > div,
    div[role="tablist"] div,
    div[role="tablist"] div * {{
        border-bottom: none !important;
        box-shadow: none !important;
    }}
    div[role="tablist"] > div[style*="absolute"],
    div[role="tablist"] > div[style*="position: absolute"],
    div[role="tablist"] div[style*="rgb(255, 75, 75)"],
    div[role="tablist"] div[style*="#ff4b4b"],
    div[role="tablist"] div[data-testid="stTabHighlight"],
    div[role="tablist"] div[data-testid="stTabHighlight"] *,
    div[role="tab"] > div:nth-child(2),
    div[role="tablist"] [style*="background-color"],
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"], [role="tablist"]::after, [data-testid="stTabHighlight"], [data-testid="stTabBorder"], button[role="tab"]::after, div[role="tab"]::after,
    [data-testid="stTabHighlight"], [data-testid="stTabBorder"], div[data-testid="stTabHighlight"] {{
        display: none !important;
        height: 0px !important;
        background: transparent !important;
        background-color: transparent !important;
        border-color: transparent !important;
        color: transparent !important;
        opacity: 0 !important;
        visibility: hidden !important;
    }}
    
    /* HeroUI v3 Metric Cards */
    .citation-card, .metric-card {{
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease !important;
    }}
    .citation-card:hover, .metric-card:hover {{
        transform: translateY(-2px) scale(1.008) !important;
    }}
    .metric-card {{
        background: {metric_bg}; backdrop-filter: blur(20px);
        border: 1px solid {glass_border}; border-radius: 18px;
        padding: 1.5rem 1.75rem; position: relative; overflow: hidden; transition: all 0.25s;
        box-shadow: 0 4px 14px rgba(0,0,0,0.02);
    }}
    .metric-card::after {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, {accent}, {accent2}); border-radius: 18px 18px 0 0;
    }}
    .metric-card:hover {{ border-color: {accent}; box-shadow: 0 8px 24px {glow2}; }}
    .metric-label {{
        font-size: 0.73rem; color: {text_muted} !important; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;
    }}
    .metric-value {{
        font-size: 2.1rem; font-weight: 800; letter-spacing: -0.04em;
        background: linear-gradient(135deg, {accent}, {accent2});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }}
    
    /* HeroUI v3 Solid & Gradient Primary Buttons */
    .stButton > button[kind="primary"], 
    button[kind="primary"],
    input[type="submit"],
    div.stButton button,
    form button[type="submit"],
    .stLoginButton > button,
    a.custom-dl-btn-primary {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important; 
        color: #ffffff !important; 
        font-weight: 800 !important;
        letter-spacing: 0.05em !important;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important; 
        font-size: 0.88rem !important;
        border-radius: 14px !important; 
        padding: 0.8rem 1.85rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important; 
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.38), 0 4px 10px -2px rgba(16, 185, 129, 0.2) !important;
        text-transform: uppercase !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        width: 100% !important;
    }}
    .stButton > button[kind="primary"]:hover, a.custom-dl-btn-primary:hover {{ 
        transform: translateY(-2px) scale(1.01) !important; 
        box-shadow: 0 14px 30px -4px rgba(16, 185, 129, 0.5), 0 6px 14px -2px rgba(16, 185, 129, 0.3) !important;
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        border-color: rgba(16, 185, 129, 0.45) !important;
        filter: brightness(1.05) !important;
        color: #ffffff !important;
        text-decoration: none !important;
    }}
    .stButton > button[kind="primary"]:active, a.custom-dl-btn-primary:active {{
        transform: scale(0.97) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }}
    .stButton > button[kind="primary"] *, button[kind="primary"] * {{
        color: #ffffff !important;
    }}
    
    /* HeroUI v3 Bordered & Secondary Buttons */
    .stButton > button[kind="secondary"], button[kind="secondary"], .stDownloadButton > button, a.custom-dl-btn {{
        background: #ffffff !important; backdrop-filter: blur(12px) !important;
        border: 1px solid {glass_border} !important; color: {text} !important;
        font-weight: 700 !important; font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        border-radius: 14px !important; padding: 0.75rem 1.6rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        font-size: 0.88rem !important;
        width: 100% !important;
    }}
    .stButton > button[kind="secondary"]:hover, .stDownloadButton > button:hover, a.custom-dl-btn:hover {{
        border-color: {accent} !important; color: {accent} !important;
        background: rgba(16, 185, 129, 0.05) !important; transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.15) !important;
        text-decoration: none !important;
    }}
    .stButton > button[kind="secondary"]:active, .stDownloadButton > button:active, a.custom-dl-btn:active {{
        transform: scale(0.97) !important;
    }}
    
    /* HeroUI v3 Inputs & Textareas Container Border Fix */
    div[data-baseweb="textarea"], 
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    .stTextArea > div,
    .stTextInput > div {{
        background: #ffffff !important;
        border: 1px solid {glass_border} !important;
        border-radius: 14px !important;
        box-shadow: none !important;
        outline: none !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }}
    
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div {{
        background: transparent !important;
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
        border-radius: 14px !important;
    }}

    div[data-baseweb="textarea"]:focus-within, 
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within,
    .stTextArea > div:focus-within,
    .stTextInput > div:focus-within {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.18) !important;
    }}

    .stTextArea textarea, .stTextInput input {{
        background: #ffffff !important;
        background-color: #ffffff !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-radius: 14px !important;
        color: {text} !important;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        font-size: 0.92rem !important;
        padding: 0.85rem 1.1rem !important;
        caret-color: {accent} !important;
    }}
    
    /* Force white background on all BaseUI inner wrappers */
    div[data-baseweb="textarea"] > div > div,
    div[data-baseweb="input"] > div > div,
    div[data-baseweb="base-input"] > div > div {{
        background: #ffffff !important;
        background-color: #ffffff !important;
    }}

    .stTextArea textarea:focus, .stTextInput input:focus {{
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }}
    
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {{ color: {text_dim} !important; }}
    
    div[data-baseweb="select"] > div {{
        background: #ffffff !important;
        border: 1px solid {glass_border} !important;
        border-radius: 14px !important;
        color: {text} !important;
    }}
    div[data-baseweb="select"]:focus-within > div {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.18) !important;
    }}

    .stTextArea label, .stTextInput label, .stFileUploader label, .stSelectbox label {{
        font-size: 0.78rem !important; font-weight: 700 !important;
        color: {text_muted} !important; letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }}
    
    /* Checkbox Styling & Size */
    .stCheckbox label p, [data-testid="stCheckbox"] label p {{
        font-size: 0.96rem !important;
        font-weight: 700 !important;
        color: {text} !important;
        line-height: 1.4 !important;
    }}
    
    /* HeroUI v3 Drag and Drop Uploaders */
    [data-testid="stFileUploader"] {{
        background: transparent !important;
    }}
    [data-testid="stFileUploader"] > section, [data-testid="stFileUploader"] section {{
        background: #ffffff !important; 
        background-color: #ffffff !important;
        border: 2px dashed {glass_border} !important;
        border-radius: 16px !important; 
        transition: all 0.25s !important;
        padding: 1.5rem !important;
    }}
    [data-testid="stFileUploader"] section:hover {{
        border-color: {accent} !important; 
        background: rgba(16, 185, 129, 0.04) !important;
        background-color: rgba(16, 185, 129, 0.04) !important;
    }}
    [data-testid="stFileUploader"] button {{
        background-color: #ffffff !important;
        color: {text} !important;
        border: 1px solid {glass_border} !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }}
    
    /* HeroUI v3 Expanders & Alerts */
    .streamlit-expanderHeader {{
        background: #ffffff !important; border: 1px solid {glass_border} !important;
        border-radius: 14px !important; color: {text} !important;
        font-weight: 700 !important; transition: all 0.2s !important;
    }}
    .streamlit-expanderHeader:hover {{ border-color: {accent} !important; background: rgba(16, 185, 129, 0.04) !important; }}
    .streamlit-expanderContent {{
        background: #ffffff !important; border: 1px solid {glass_border} !important;
        border-top: none !important; border-radius: 0 0 14px 14px !important;
    }}
    [data-testid="stAlert"] {{
        background: #ffffff !important; backdrop-filter: blur(12px) !important;
        border-radius: 14px !important; border-left: 4px solid {accent} !important;
        color: {text} !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.03) !important;
    }}
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {accent}, {accent2}) !important;
        border-radius: 99px !important;
    }}
    hr {{ border: none !important; border-top: 1px solid {glass_border} !important; margin: 1.5rem 0 !important; }}
    
    /* HeroUI v3 Citation Cards & Badges */
    .citation-card {{
        background: #ffffff; border: 1px solid {glass_border}; border-radius: 14px;
        padding: 1.15rem 1.35rem; margin-bottom: 0.85rem; transition: all 0.25s;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }}
    .citation-card:hover {{ border-color: {accent}; box-shadow: 0 6px 20px {glow2}; }}
    .citation-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }}
    .citation-source {{ font-weight: 700; color: {text} !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 72%; font-size: 0.85rem; }}
    .citation-text {{ font-size: 0.82rem; color: {text_muted} !important; font-style: italic; line-height: 1.55; border-left: 3px solid {accent}; padding-left: 0.75rem; margin: 0; }}
    
    /* HeroUI Pill Badges */
    .badge {{ display: inline-flex; align-items: center; padding: 3px 11px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.03em; }}
    .badge-blue {{ color: {badge_text}; background: {badge_bg}; border: 1px solid {accent}33; }}
    .badge-green {{ color: {green}; background: {green_bg}; border: 1px solid {green}33; }}
    .badge-red {{ color: {red}; background: {red_bg}; border: 1px solid {red}33; }}
    .badge-yellow {{ color: #d97706; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.25); }}
    
    .data-table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.85rem; margin-top: 0.75rem; }}
    .data-table th {{
        text-align: left; padding: 0.75rem 1.1rem; color: {text_muted} !important;
        font-weight: 700; font-size: 0.73rem; text-transform: uppercase; letter-spacing: 0.08em;
        border-bottom: 1px solid {glass_border}; background: {metric_bg};
    }}
    .data-table th:first-child {{ border-radius: 12px 0 0 0; }}
    .data-table th:last-child {{ border-radius: 0 12px 0 0; }}
    .data-table td {{ padding: 0.75rem 1.1rem; color: {text} !important; border-bottom: 1px solid {glass_border}; }}
    .data-table tr:last-child td {{ border-bottom: none; }}
    .data-table tr:hover td {{ background: {glass_hover}; }}
    
    .section-title {{ font-size: 1.5rem; font-weight: 800; color: {text} !important; letter-spacing: -0.035em; margin-bottom: 0.35rem; }}
    .section-sub {{ font-size: 0.9rem; color: {text_muted} !important; margin-bottom: 1.5rem; line-height: 1.6; }}
    [data-testid="stHorizontalBlock"] {{ gap: 1.25rem !important; }}
    .rfp-output, .rfp-output * {{ font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important; color: {text} !important; line-height: 1.75; }}
    .gradient-divider {{ height: 1px; background: linear-gradient(90deg, transparent, {accent}55, {accent2}55, transparent); margin: 1.5rem 0; border: none; }}
    
    .engine-pill {{
        display: inline-flex; align-items: center; gap: 0.45rem; background: {badge_bg};
        border: 1px solid {accent}44; color: {badge_text} !important; border-radius: 9999px;
        padding: 4px 12px; font-size: 0.75rem; font-weight: 700;
    }}
    .engine-dot {{
        width: 7px; height: 7px; background: {accent}; border-radius: 50%;
        display: inline-block; box-shadow: 0 0 8px {glow};
        animation: pulse-dot 2s ease-in-out infinite;
    }}
    @keyframes pulse-dot {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50%        {{ opacity: 0.5; transform: scale(0.7); }}
    }}
    .empty-state {{ text-align: center; padding: 3.5rem 1.5rem; }}
    .empty-state-icon {{ font-size: 2.75rem; margin-bottom: 0.85rem; opacity: 0.65; }}
    .empty-state-text {{ font-size: 0.92rem; color: {text_muted} !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css()

# Engine config
provider_models = {
    "Google Gemini": ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
    "Groq LPU": ["llama-3.3-70b-versatile", "llama-3-8b-8192", "mixtral-8x7b-32768"],
    "OpenRouter": ["google/gemini-2.5-flash", "google/gemini-2.5-pro", "meta-llama/llama-3.3-70b-instruct"]
}

# Resolve active provider — reads st.secrets on Streamlit Cloud, os.getenv locally
env_provider = _cfg("ACTIVE_PROVIDER", "Google Gemini").strip()
if env_provider not in ["Google Gemini", "Groq LPU", "OpenRouter"]:
    env_provider = "Google Gemini"
st.session_state.active_provider = env_provider

# Resolve active configuration
active_provider = st.session_state.active_provider
if f"model_{active_provider}" not in st.session_state:
    st.session_state[f"model_{active_provider}"] = provider_models[active_provider][0]
selected_model = st.session_state[f"model_{active_provider}"]

if active_provider == "Google Gemini":
    provider_key = "gemini"
    api_key = _cfg("GEMINI_API_KEY")
    provider = "Google Gemini"
elif active_provider == "Groq LPU":
    provider_key = "groq"
    api_key = _cfg("GROQ_API_KEY")
    provider = "Groq LPU"
else:
    provider_key = "openrouter"
    api_key = _cfg("OPENROUTER_API_KEY")
    provider = "OpenRouter"

# Toggle demo mode based on environment variable
env_demo_mode = _cfg("DEMO_MODE", "False").strip().lower() == "true"
if env_demo_mode:
    st.session_state.demo_mode = True
    api_key = "demo_mode_key"
else:
    st.session_state.demo_mode = False

is_demo_mode = st.session_state.get("demo_mode", False)
comparison_mode = False

# Helper UI Functions
def metric_card(label, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def glass_card_open():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

def glass_card_close():
    st.markdown('</div>', unsafe_allow_html=True)

def section_header(title, subtitle=""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)

def gradient_divider():
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ── Rate Limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_MAX     = 10   # max requests per window
RATE_LIMIT_WINDOW  = 60  # seconds

def check_rate_limit(action_key: str = "generate") -> tuple[bool, int]:
    """
    Checks whether the current user has exceeded the rate limit for a given action.
    Uses st.session_state to track timestamps of recent requests.
    Returns (allowed: bool, seconds_remaining: int).
    """
    import time
    now = time.time()
    history_key = f"_rl_{action_key}_history"
    history: list = st.session_state.get(history_key, [])
    # Prune timestamps outside the rolling window
    history = [t for t in history if now - t < RATE_LIMIT_WINDOW]
    if len(history) >= RATE_LIMIT_MAX:
        oldest = history[0]
        wait = int(RATE_LIMIT_WINDOW - (now - oldest)) + 1
        st.session_state[history_key] = history
        return False, wait
    history.append(now)
    st.session_state[history_key] = history
    return True, 0

@st.cache_resource
def get_db_client():
    return get_chroma_client(db_path="chroma_db")

db_client = get_db_client()

# Brand Header & Theme Studio Bar
col_hdr_brand, col_hdr_theme = st.columns([7, 5])
with col_hdr_brand:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.6rem; padding: 0.2rem 0 0.5rem 0;">
        <div class="brand-logo">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="logo-flash-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#34d399" />
                        <stop offset="100%" stop-color="#10b981" />
                    </linearGradient>
                </defs>
                <path d="M14.5 2L5.5 13H11.5L9.5 22L18.5 11H12.5L14.5 2Z" fill="url(#logo-flash-grad)" stroke="url(#logo-flash-grad)" stroke-width="1.5" stroke-linejoin="round" />
            </svg>
        </div>
        <div>
            <div class="brand-name">FlashRFP.ai</div>
            <div style="font-size:0.8rem; color:#64748b; font-weight:600;">Enterprise Automated Proposal Engine</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_hdr_theme:
    theme_options = {
        "emerald_aurora": "🌿 Emerald Aurora (Default Glass)",
        "midnight_obsidian": "🌃 Midnight Obsidian (Deep Dark)",
        "nordic_slate": "🧊 Nordic Slate (Corporate)",
        "royal_indigo": "🔮 Royal Indigo (Luxury Mesh)"
    }
    current_preset = st.session_state.get("theme_preset", "emerald_aurora")
    selected_top_preset = st.selectbox(
        "🎨 Select App Visual Theme:",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(current_preset) if current_preset in theme_options else 0,
        key="top_header_theme_preset_selector"
    )
    if selected_top_preset != current_preset:
        st.session_state.theme_preset = selected_top_preset
        st.rerun()

st.markdown('<div class="gradient-divider" style="margin-bottom:1.5rem;"></div>', unsafe_allow_html=True)

# API Key Gate for Selected Provider
if not api_key:
    glass_card_open()
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <div style="font-size:3rem; margin-bottom:1rem;">🛡️</div>
        <div class="section-title" style="text-align:center;">Proposal Engine Offline</div>
        <div class="section-sub" style="text-align:center; max-width:480px; margin:0.5rem auto 1.5rem;">
            The FlashRFP AI generation service is currently offline or undergoing maintenance. 
            Please contact your system administrator to configure the connection.
        </div>
    </div>
    """, unsafe_allow_html=True)
    glass_card_close()
    st.stop()

# Tenant Data Isolation & Cached DB Stats
tenant_id = st.session_state.username

def refresh_db_stats():
    if "collection" not in st.session_state:
        st.session_state.collection = get_or_create_collection(db_client, api_key)
    coll = st.session_state.collection
    try:
        data = coll.get(where={"tenant_id": tenant_id or ""}, include=["metadatas"])
        st.session_state.total_chunks = len(data["ids"]) if (data and data["ids"]) else 0
        unique_srcs = set(meta.get("source") for meta in data["metadatas"] if meta) if (data and data["metadatas"]) else set()
        st.session_state.total_docs = len(unique_srcs)
        st.session_state.sources_list = sorted(list(unique_srcs))
    except Exception as e:
        st.session_state.total_chunks = 0
        st.session_state.total_docs = 0
        st.session_state.sources_list = []

if "total_chunks" not in st.session_state or "collection" not in st.session_state:
    refresh_db_stats()

total_chunks = st.session_state.total_chunks
total_docs = st.session_state.total_docs
sources_list = st.session_state.sources_list
collection = st.session_state.collection

# Render Sidebar with User Profile, Theme Switcher, Logout, and Bottom Metrics
with st.sidebar:
    # Determine plan pill
    if current_plan == "trial":
        plan_badge_html = f'<span class="badge badge-yellow" style="margin-top:0.4rem; padding:3px 10px; font-size:0.75rem;">⏳ 7-Day Trial ({trial_days} Days Left)</span>'
    else:
        plan_badge_html = f'<span class="badge badge-green" style="margin-top:0.4rem; padding:3px 10px; font-size:0.75rem;">🟢 Plan: {current_plan.upper()}</span>'

    st.markdown(f"""
    <div style="padding: 1.5rem 0 1rem 0; text-align: center; border-bottom: 1px solid {glass_border}; margin-bottom: 2rem;">
        <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">⚡</div>
        <div class="brand-name" style="font-size: 1.4rem; color: {text}; text-align: center;">FlashRFP.ai</div>
        <div class="brand-tagline" style="font-size: 0.78rem; color: {text_muted}; text-align: center; display: block !important;">Automated Proposal Engine</div>
    </div>
    <div style="padding: 0.5rem 0; text-align: center;">
        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: {text_dim};">Logged in as</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: {text};">👤 {st.session_state.get('name', 'User')}</div>
        <div style="font-size: 0.8rem; color: {text_muted}; margin-bottom: 0.25rem;">{st.session_state.get('username')}</div>
        {plan_badge_html}
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    theme_options = {
        "emerald_aurora": "🌿 Emerald Aurora (Default Glass)",
        "midnight_obsidian": "🌃 Midnight Obsidian (Deep Dark)",
        "nordic_slate": "🧊 Nordic Slate (Corporate)",
        "royal_indigo": "🔮 Royal Indigo (Luxury Mesh)"
    }
    current_preset = st.session_state.get("theme_preset", "emerald_aurora")
    selected_preset = st.selectbox(
        "🎨 App Visual Theme",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(current_preset) if current_preset in theme_options else 0,
        key="sidebar_theme_preset_selector"
    )
    if selected_preset != current_preset:
        st.session_state.theme_preset = selected_preset
        st.rerun()

    authenticator.logout(button_name="🔓 Logout", location="sidebar", key="sidebar_logout_btn")
    
    # Render ROI & Time Saved Dashboard in sidebar
    render_roi_dashboard()
    
    st.write("")
    st.write("")
    st.markdown(f'<div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid {glass_border};">', unsafe_allow_html=True)
    
    st.markdown(f'<div class="metric-card" style="margin-bottom:0.75rem;"><div class="metric-label">Indexed Documents</div><div class="metric-value">{total_docs}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card" style="margin-bottom:0.75rem;"><div class="metric-label">Chunked Segments</div><div class="metric-value">{total_chunks}</div></div>', unsafe_allow_html=True)
    
    status_val = '<span style="color:#34d399">●</span> Active' if total_chunks > 0 else '<span style="color:#f87171">●</span> Empty'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Engine Status</div>
        <div class="metric-value" style="font-size:1.2rem; -webkit-text-fill-color: unset; background: none;">{status_val}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Main Tabs
tab_qa, tab_batch, tab_boq, tab_copilot, tab_kb, tab_roi = st.tabs([
    "RFP Response Engine",
    "⚡ Upload Full RFP",
    "📊 BOQ / Excel Auto-Fill",
    "🤖 FlashRFP Copilot",
    "📚 Knowledge Base",
    "📈 ROI & Time Saved"
])

# ================= TAB 1: RFP Response Engine =================
with tab_qa:
    glass_card_open()
    section_header(
        "Draft Proposal Response",
        "Enter an RFP question and FlashRFP AI will retrieve relevant context from your knowledge base and synthesize a structured, professional response."
    )
    question = st.text_area(
        "RFP QUESTION",
        height=120,
        placeholder="e.g. Describe your information security policies, encryption standards, and compliance certifications."
    )
    single_win_themes = st.text_input(
        "Key Win Themes (Optional)",
        value="",
        placeholder="e.g. We are the cheapest, We have 24/7 support",
        key="single_win_themes"
    )
    col_run, col_hint = st.columns([3.5, 6.5])
    with col_run:
        generate_btn = st.button("⚡ Generate Response", type="primary", use_container_width=True)
    with col_hint:
        if total_chunks == 0:
            st.markdown(f'<span class="badge badge-red" style="margin-top:0.55rem; display:inline-block;">⚠ Knowledge base empty — upload documents first</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="badge badge-green" style="margin-top:0.55rem; display:inline-block;">✓ {total_docs} documents · {total_chunks} chunks ready</span>', unsafe_allow_html=True)
    glass_card_close()

    if generate_btn:
        if not question.strip():
            st.warning("Please enter an RFP question.")
        elif total_chunks == 0:
            st.error("Your knowledge base is empty. Please upload historical proposal files in the **Knowledge Base** tab first.")
        else:
            _allowed, _wait = check_rate_limit("generate")
            if not _allowed:
                st.error(f"⏱️ **Rate limit reached** — You've sent {RATE_LIMIT_MAX} requests in the last {RATE_LIMIT_WINDOW}s. Please wait **{_wait} second(s)** before generating again.")
                st.stop()
            with st.spinner("Searching knowledge base & synthesising bid response..."):
                try:
                    import time
                    contexts = query_knowledge_base(question, collection, top_k=15, tenant_id=tenant_id)
                    st.session_state.current_question = question
                    st.session_state.current_sources  = contexts
                    t0 = time.time()
                    response_text = generate_rfp_response(api_key, question, contexts, provider=provider_key, model=selected_model, win_themes=single_win_themes)
                    t1 = time.time()
                    log_ai_performance(t0, t1, "question", quantity=1)
                    st.session_state.current_time     = t1 - t0
                    st.session_state.current_response = response_text
                    st.session_state.active_engine    = f"{provider} ({selected_model})"
                    if "groq_response" in st.session_state:
                        del st.session_state.groq_response
                except Exception as e:
                    err_msg = str(e)
                    st.error(f"Failed to generate response: {err_msg}")
                    if any(term in err_msg.lower() for term in ["restricted", "unauthorized", "400", "401"]):
                        st.warning("💡 **Troubleshooting Tip**: If your active API key has been restricted, suspended, or is invalid, please open the **⚙️ Engine & API Settings** expander at the top of the page to switch providers/keys, or **Enable Demo Mode (No API Key Required)** to run the app using local simulation.")

    if "current_response" in st.session_state:
        gradient_divider()
        col_ans, col_cit = st.columns([7, 5])

        with col_ans:
            glass_card_open()
            time_pill = f'<div class="engine-pill"><span class="engine-dot"></span>Generated in {st.session_state.current_time:.2f}s</div>' if "current_time" in st.session_state else ""
            
            # Confidence badge logic based on max similarity match in Vector DB
            max_sim = max([src['similarity'] for src in st.session_state.current_sources]) if st.session_state.get("current_sources") else 0.0
            if max_sim >= 0.85:
                confidence_badge = f'<span class="badge badge-green">High Confidence ({int(max_sim*100)}% match)</span>'
            elif max_sim >= 0.70:
                confidence_badge = f'<span class="badge badge-yellow">Medium Confidence ({int(max_sim*100)}% match - Review recommended)</span>'
            else:
                confidence_badge = '<span class="badge badge-red">Low Confidence (No historical data found - Manual input required)</span>'
                
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap; margin-bottom:1rem;">
                <div class="section-title" style="margin:0;">📝 Draft Response</div>
                {time_pill}
                {confidence_badge}
            </div>
            """, unsafe_allow_html=True)
            st.success(st.session_state.current_response)
            if st.session_state.current_sources:
                sources_list_str = [f"{src['source']} (Match Score: {int(src['similarity'] * 100)}%)" for src in st.session_state.current_sources]
                st.caption(f"ℹ️ **Sources**: {', '.join(sources_list_str)}")
            gradient_divider()
            from exporter import generate_docx_stream
            try:
                docx_bytes = generate_docx_stream(
                    st.session_state.current_question,
                    st.session_state.current_response,
                    st.session_state.current_sources
                )
                import base64
                b64_docx = base64.b64encode(docx_bytes).decode()
                st.markdown(f'<a href="data:application/octet-stream;base64,{b64_docx}" download="FlashRFP_Response.docx" class="custom-dl-btn">📥 Download as Word (.docx)</a>', unsafe_allow_html=True)
            except Exception as ex:
                st.error(f"Export error: {str(ex)}")
            glass_card_close()

        with col_cit:
            glass_card_open()
            st.markdown('<div class="section-title" style="margin-bottom:1rem;">🔍 Source References</div>', unsafe_allow_html=True)
            if st.session_state.current_sources:
                for idx, src in enumerate(st.session_state.current_sources):
                    score_pct = f"{int(src['similarity'] * 100)}%"
                    st.markdown(f"""
                    <div class="citation-card">
                        <div class="citation-header">
                            <span class="citation-source">📄 [{idx+1}] {src['source']}</span>
                            <span class="badge badge-blue">{score_pct}</span>
                        </div>
                        <p class="citation-text">&ldquo;{src['text']}&rdquo;</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state"><div class="empty-state-icon">🔎</div><div class="empty-state-text">No sources cited for this response.</div></div>', unsafe_allow_html=True)
            glass_card_close()
    else:
        st.markdown("""
        <div class="empty-state" style="padding: 4rem 2rem;">
            <div class="empty-state-icon">✶</div>
            <div class="section-title" style="text-align:center; margin-bottom:0.5rem;">Ready to Draft</div>
            <div class="empty-state-text">Enter an RFP question above and click Generate Response to begin.</div>
        </div>
        """, unsafe_allow_html=True)


# ================= TAB 2: Upload Full RFP =================
with tab_batch:
    glass_card_open()
    section_header(
        "Auto-Extract & Answer Full RFP",
        "Upload a complete RFP PDF. FlashRFP AI will extract all questions, search your knowledge base, and generate draft responses ready for export."
    )
    c1, c2 = st.columns(2)
    with c1:
        rfp_pdf_file = st.file_uploader(
            "RFP PDF DOCUMENT",
            type=["pdf"],
            key="rfp_pdf_uploader"
        )
    with c2:
        rfp_word_template = st.file_uploader(
            "WORD TEMPLATE (OPTIONAL)",
            type=["docx"],
            key="rfp_word_uploader"
        )
    
    win_themes_input = st.text_input(
        "Key Win Themes (Optional)",
        value="",
        placeholder="e.g. We are the cheapest, We have 24/7 support",
        key="batch_win_themes"
    )

    col_process, _ = st.columns([4.2, 5.8])
    with col_process:
        process_batch_btn = st.button("⚡ Extract & Auto-Respond", type="primary", use_container_width=True)
    glass_card_close()

    if process_batch_btn:
        if not rfp_pdf_file:
            st.warning("Please upload an RFP PDF document first.")
        elif rfp_pdf_file.size > 50000000:
            st.error("❌ File too large: The RFP PDF exceeds the 50MB limit.")
        elif not rfp_pdf_file.getvalue().startswith(b"%PDF"):
            st.error("❌ Security violation: The uploaded RFP file is not a valid PDF document.")
        elif rfp_word_template and rfp_word_template.size > 50000000:
            st.error("❌ File too large: The Word template exceeds the 50MB limit.")
        elif rfp_word_template and not rfp_word_template.getvalue().startswith(b"PK\x03\x04"):
            st.error("❌ Security violation: The uploaded Word template is not a valid DOCX document.")
        elif collection is None:
            st.error("Database connection failed. Please refresh the page.")
        elif total_chunks == 0:
            st.error("Your knowledge base is empty. Please upload historical materials in the **Knowledge Base** tab first.")
        else:
            _allowed_batch, _wait_batch = check_rate_limit("batch")
            if not _allowed_batch:
                st.error(f"⏱️ **Rate limit reached** — You've submitted {RATE_LIMIT_MAX} batch jobs in the last {RATE_LIMIT_WINDOW}s. Please wait **{_wait_batch} second(s)**.") 
                st.stop()
            temp_pdf_path = os.path.join(base_dir, f"temp_rfp_{uuid.uuid4().hex}.pdf")
            with open(temp_pdf_path, "wb") as f:
                f.write(rfp_pdf_file.getbuffer())
            success = False
            try:
                progress_bar = st.progress(0)
                status_text  = st.empty()
                
                def extraction_progress(current, total, phase):
                    pct = current / total
                    progress_bar.progress(pct)
                    if phase == "extract_text":
                        status_text.markdown(f'<div class="engine-pill"><span class="engine-dot"></span>Reading PDF page {current} of {total}…</div>', unsafe_allow_html=True)
                    else:
                        status_text.markdown(f'<div class="engine-pill"><span class="engine-dot"></span>Extracting questions from page {current} of {total}…</div>', unsafe_allow_html=True)
                
                # Build multi-provider fallback pool from all available keys
                _provider_pool = build_provider_pool(
                    primary_api_key=api_key,
                    primary_provider=provider_key,
                    primary_model=selected_model
                )
                questions = extract_questions_from_pdf(
                    temp_pdf_path, api_key,
                    provider=provider_key, model=selected_model,
                    progress_callback=extraction_progress,
                    provider_pool=_provider_pool
                )
                
                status_text.empty()
                progress_bar.empty()
                
                if not questions:
                    st.warning("No questions could be extracted. Please verify the PDF content.")
                else:
                    st.success(f"Extracted **{len(questions)}** questions/requirements from the RFP.")
                    progress_bar_batch = st.progress(0)
                    status_text_batch  = st.empty()
                    def update_progress(current, total):
                        progress_bar_batch.progress(current / total)
                        status_text_batch.markdown(f'<div class="engine-pill"><span class="engine-dot"></span>Generating answer {current} of {total}…</div>', unsafe_allow_html=True)
                    t0 = time.time()
                    qa_results = batch_process_rfp_questions(
                        questions, collection, api_key,
                        progress_callback=update_progress,
                        provider=provider_key, model=selected_model,
                        win_themes=win_themes_input,
                        tenant_id=tenant_id,
                        provider_pool=_provider_pool
                    )
                    t1 = time.time()
                    if qa_results:
                        log_ai_performance(t0, t1, "question", quantity=len(qa_results))
                    status_text_batch.empty()
                    progress_bar_batch.empty()
                    st.session_state.batch_results = qa_results
                    st.session_state.batch_template_bytes = rfp_word_template.getvalue() if rfp_word_template else None
                    st.session_state.batch_template_name  = rfp_word_template.name if rfp_word_template else None
                    success = True
            except Exception as e:
                if 'progress_bar' in locals(): progress_bar.empty()
                if 'status_text' in locals(): status_text.empty()
                if 'progress_bar_batch' in locals(): progress_bar_batch.empty()
                if 'status_text_batch' in locals(): status_text_batch.empty()
                
                err_msg = str(e)
                if "scanned_pdf" in err_msg:
                    st.error("This is a scanned PDF. OCR is required.")
                else:
                    st.error(f"Error processing RFP: {err_msg}")
                    if any(term in err_msg.lower() for term in ["restricted", "unauthorized", "400", "401"]):
                        st.warning("💡 **Troubleshooting Tip**: If your active API key has been restricted, suspended, or is invalid, please open the **⚙️ Engine & API Settings** expander at the top of the page to switch providers/keys, or **Enable Demo Mode (No API Key Required)** to run the app using local simulation.")
            finally:
                if os.path.exists(temp_pdf_path):
                    try: os.remove(temp_pdf_path)
                    except Exception: pass
            if success:
                st.rerun()

    if "batch_results" in st.session_state:
        gradient_divider()
        col_preview, col_actions = st.columns([7, 5])
        with col_preview:
            glass_card_open()
            st.markdown(f'<div class="section-title" style="margin-bottom:1rem;">📋 Draft Answers ({len(st.session_state.batch_results)})</div>', unsafe_allow_html=True)
            for idx, item in enumerate(st.session_state.batch_results):
                q_label = item['question'][:80] + ("…" if len(item['question']) > 80 else "")
                with st.expander(f"Q{idx+1}: {q_label}"):
                    # Calculate max similarity for this batch question
                    max_sim_item = max([src['similarity'] for src in item['sources']]) if item.get("sources") else 0.0
                    if max_sim_item >= 0.85:
                        conf_badge_item = f'<span class="badge badge-green">High Confidence ({int(max_sim_item*100)}% match)</span>'
                    elif max_sim_item >= 0.70:
                        conf_badge_item = f'<span class="badge badge-yellow">Medium Confidence ({int(max_sim_item*100)}% match - Review recommended)</span>'
                    else:
                        conf_badge_item = '<span class="badge badge-red">Low Confidence (No historical data found - Manual input required)</span>'
                    
                    st.markdown(f'<div style="margin-bottom:0.75rem; display:flex; align-items:center; gap:0.5rem;"><strong>Confidence:</strong> {conf_badge_item}</div>', unsafe_allow_html=True)
                    st.markdown("**RFP Question:**")
                    st.write(item["question"])
                    st.markdown("**Drafted Response:**")
                    st.markdown('<div class="rfp-output">', unsafe_allow_html=True)
                    st.markdown(item["answer"])
                    st.markdown('</div>', unsafe_allow_html=True)
                    if item.get("sources"):
                        st.markdown("**Cited Sources:**")
                        for s_idx, src in enumerate(item["sources"]):
                            st.write(f"- *[{s_idx+1}] {src['source']} ({int(src['similarity']*100)}% match)*")
            glass_card_close()
        with col_actions:
            glass_card_open()
            section_header("📥 Export Completed RFP", "Download your drafted answers as Microsoft Word documents.")
            try:
                batch_docx_bytes = generate_batch_docx_stream(st.session_state.batch_results)
                import base64
                b64_batch = base64.b64encode(batch_docx_bytes).decode()
                st.markdown(f'<a href="data:application/octet-stream;base64,{b64_batch}" download="Completed_RFP_Drafts.docx" class="custom-dl-btn">📥 Standard Word Doc (.docx)</a>', unsafe_allow_html=True)
            except Exception as ex:
                st.error(f"Export error: {str(ex)}")
            gradient_divider()
            # Check if template is uploaded in the file uploader or in session state
            template_file = rfp_word_template if rfp_word_template else None
            template_bytes = template_file.getvalue() if template_file else st.session_state.get("batch_template_bytes")
            template_name = template_file.name if template_file else st.session_state.get("batch_template_name")

            if template_bytes:
                st.markdown(f'<span class="badge badge-blue">Template: {template_name}</span>', unsafe_allow_html=True)
                st.write("")
                try:
                    import io
                    filled_docx_bytes = fill_rfp_docx_template(
                        io.BytesIO(template_bytes),
                        st.session_state.batch_results
                    )
                    import base64
                    b64_filled = base64.b64encode(filled_docx_bytes).decode()
                    st.markdown(f'<a href="data:application/octet-stream;base64,{b64_filled}" download="Completed_RFP.docx" class="custom-dl-btn-primary">🔒 Format-Lock Export (.docx)</a>', unsafe_allow_html=True)
                except Exception as ex:
                    st.error(f"Template fill error: {str(ex)}")
            else:
                st.markdown('<div class="empty-state-text" style="font-size:0.8rem;">💡 Upload a Word template above to enable Format-Lock Export.</div>', unsafe_allow_html=True)
            
            # Advanced Proposal Docx Export
            extracted_data_list = []
            for qa in st.session_state.batch_results:
                src_text = "Knowledge Base Vector Index"
                if qa.get("sources") and isinstance(qa["sources"], list):
                    src_names = list(set([s["source"] for s in qa["sources"]]))
                    if src_names:
                        src_text = ", ".join(src_names)
                manual_flag = (
                    "MANUAL REVIEW" in qa.get("answer", "").upper() or 
                    "NO HISTORICAL" in qa.get("answer", "").upper() or
                    not qa.get("sources")
                )
                extracted_data_list.append({
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                    "source": src_text,
                    "manual_review": manual_flag
                })
            render_export_button(extracted_data_list)

            gradient_divider()
            if st.button("🗑 Clear Results", use_container_width=True):
                for k in ["batch_results", "batch_template_bytes", "batch_template_name"]:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
            glass_card_close()
    else:
        st.markdown("""
        <div class="empty-state" style="padding: 4rem 2rem;">
            <div class="empty-state-icon">⚡</div>
            <div class="section-title" style="text-align:center; margin-bottom:0.5rem;">No RFP Processed Yet</div>
            <div class="empty-state-text">Upload an RFP PDF above and click Extract & Auto-Respond.</div>
        </div>
        """, unsafe_allow_html=True)



# ================= TAB 3: BOQ / Excel Auto-Fill Engine =================
with tab_boq:
    glass_card_open()
    section_header(
        "Automated BOQ & Technical Compliance Builder",
        "Upload government tender Excel spreadsheets (Bill of Quantities / Technical Compliance Matrices). FlashRFP AI auto-detects rows, matches specs from your knowledge base, and writes compliance responses directly into your Excel template."
    )
    boq_excel_file = st.file_uploader(
        "TENDER EXCEL BOQ / COMPLIANCE MATRIX (.XLSX)",
        type=["xlsx", "xls"],
        key="boq_excel_uploader"
    )
    
    boq_win_themes = st.text_input(
        "Key Win Themes / Value Proposition (Optional)",
        value="",
        placeholder="e.g. ISO 27001 Certified, Tier-4 Datacenter SLA, OEM Direct Partner",
        key="boq_win_themes_input"
    )

    col_boq_run, _ = st.columns([4.2, 5.8])
    with col_boq_run:
        process_boq_btn = st.button("📊 Populate Excel BOQ", type="primary", use_container_width=True)
    glass_card_close()

    if process_boq_btn:
        if not boq_excel_file:
            st.warning("Please upload an Excel BOQ file first.")
        elif boq_excel_file.size > 50000000:
            st.error("❌ File too large: The Excel file exceeds the 50MB limit.")
        elif collection is None:
            st.error("Database connection failed. Please refresh the page.")
        elif total_chunks == 0 and not is_demo_mode:
            st.error("Your knowledge base is empty. Please upload historical materials in the **Knowledge Base** tab first.")
        else:
            _allowed_boq, _wait_boq = check_rate_limit("boq")
            if not _allowed_boq:
                st.error(f"⏱️ **Rate limit reached** — Please wait **{_wait_boq} second(s)** before running another BOQ processing job.")
                st.stop()
            
            with st.spinner("Analyzing Excel rows, searching knowledge base, & generating compliance matrix..."):
                try:
                    from exporter import process_boq_excel
                    
                    boq_progress_bar = st.progress(0)
                    boq_status_text = st.empty()
                    
                    def boq_progress(current, total, item_text):
                        pct = current / total
                        boq_progress_bar.progress(pct)
                        short_item = item_text[:60] + ("..." if len(item_text) > 60 else "")
                        boq_status_text.markdown(f'<div class="engine-pill"><span class="engine-dot"></span>Processing row {current} of {total}: <em>{short_item}</em></div>', unsafe_allow_html=True)
                    
                    t0 = time.time()
                    out_bytes, rows_data = process_boq_excel(
                        boq_excel_file.getvalue(),
                        collection,
                        api_key,
                        tenant_id=tenant_id,
                        provider=provider_key,
                        model=selected_model,
                        win_themes=boq_win_themes,
                        demo_mode=is_demo_mode,
                        progress_callback=boq_progress
                    )
                    t1 = time.time()
                    if rows_data:
                        log_ai_performance(t0, t1, "boq", quantity=len(rows_data))
                    
                    boq_status_text.empty()
                    boq_progress_bar.empty()
                    
                    st.session_state.boq_bytes = out_bytes
                    st.session_state.boq_rows = rows_data
                    st.session_state.boq_filename = f"Populated_{boq_excel_file.name}"
                    st.success(f"✓ Populated **{len(rows_data)}** BOQ items with AI Compliance & Technical Specifications!")
                    st.rerun()
                except Exception as ex:
                    if 'boq_progress_bar' in locals(): boq_progress_bar.empty()
                    if 'boq_status_text' in locals(): boq_status_text.empty()
                    st.error(f"Error processing BOQ Excel file: {str(ex)}")

    if "boq_bytes" in st.session_state and "boq_rows" in st.session_state:
        gradient_divider()
        col_boq_preview, col_boq_dl = st.columns([7, 5])
        
        with col_boq_preview:
            glass_card_open()
            st.markdown(f'<div class="section-title" style="margin-bottom:1rem;">📊 Generated Compliance Matrix ({len(st.session_state.boq_rows)} Items)</div>', unsafe_allow_html=True)
            
            for row in st.session_state.boq_rows:
                status_c = row['compliance']
                if "NON" in status_c:
                    badge_html = '<span class="badge badge-red">NON-COMPLIED</span>'
                elif "DEV" in status_c:
                    badge_html = '<span class="badge badge-yellow">COMPLIED WITH DEVIATIONS</span>'
                else:
                    badge_html = '<span class="badge badge-green">COMPLIED</span>'
                    
                with st.expander(f"Row {row['row_num']}: {row['item'][:70]}..."):
                    st.markdown(f'<div style="margin-bottom:0.75rem;"><strong>Status:</strong> {badge_html}</div>', unsafe_allow_html=True)
                    st.markdown("**BOQ Requirement:**")
                    st.write(row['item'])
                    st.markdown("**AI Proposed Specification:**")
                    st.info(row['response'])
                    if row.get("remarks"):
                        st.markdown("**AI Remarks:**")
                        st.caption(row['remarks'])
            glass_card_close()
            
        with col_boq_dl:
            glass_card_open()
            section_header("📥 Export Completed BOQ", "Download your populated Excel BOQ template with formulas and original styles preserved.")
            import base64
            b64_boq = base64.b64encode(st.session_state.boq_bytes).decode()
            filename = st.session_state.get("boq_filename", "FlashRFP_Populated_BOQ.xlsx")
            
            st.download_button(
                label="⬇️ Download Populated Excel BOQ (.xlsx)",
                data=st.session_state.boq_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
            
            st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_boq}" download="{filename}" class="custom-dl-btn-primary" style="margin-top:0.75rem;">📊 Download Direct Link (.xlsx)</a>', unsafe_allow_html=True)
            gradient_divider()
            if st.button("🗑 Clear BOQ Session", use_container_width=True, key="clear_boq_btn"):
                for k in ["boq_bytes", "boq_rows", "boq_filename"]:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
            glass_card_close()
    else:
        st.markdown("""
        <div class="empty-state" style="padding: 4rem 2rem;">
            <div class="empty-state-icon">📊</div>
            <div class="section-title" style="text-align:center; margin-bottom:0.5rem;">No BOQ Excel Uploaded Yet</div>
            <div class="empty-state-text">Upload a government tender Excel sheet above and click Populate Excel BOQ.</div>
        </div>
        """, unsafe_allow_html=True)


# ================= TAB 4: FlashRFP Copilot =================
with tab_copilot:
    glass_card_open()
    import importlib
    import copilot
    importlib.reload(copilot)
    copilot.render_copilot_tab(
        collection,
        api_key,
        tenant_id=tenant_id,
        provider=provider_key,
        model=selected_model,
        demo_mode=is_demo_mode
    )
    glass_card_close()


# ================= TAB 5: Knowledge Base Manager =================
with tab_kb:
    # Restored Tab 3 Metrics row for data density in both views
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        metric_card("Indexed Documents", str(total_docs))
    with col_m2:
        metric_card("Chunked Segments", str(total_chunks))
    with col_m3:
        status_val = '<span style="color:#34d399">●</span> Active' if total_chunks > 0 else '<span style="color:#f87171">●</span> Empty'
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Engine Status</div>
            <div class="metric-value" style="font-size:1.2rem; -webkit-text-fill-color: unset; background: none;">{status_val}</div>
        </div>
        """, unsafe_allow_html=True)
    gradient_divider()

    # Upload status banner
    if st.session_state.get("upload_finished"):
        if st.session_state.upload_success_count > 0:
            st.success(f"✓ Successfully indexed {st.session_state.upload_success_count} document(s)!")
        for err in st.session_state.get("upload_errors", []):
            st.error(err)
        st.session_state.upload_finished      = False
        st.session_state.upload_success_count = 0
        st.session_state.upload_errors        = []

    # Upload form
    glass_card_open()
    section_header(
        "Upload Knowledge Base Documents",
        "Upload past RFP answers, proposals, case studies, or manuals in PDF or DOCX format to train FlashRFP AI."
    )
    uploaded_files = st.file_uploader(
        "DROP FILES HERE (PDF, DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="file_uploader_kb"
    )
    st.markdown(f"""
    <div style="
        background: {green_bg};
        border: 1px dashed {green}4d;
        border-radius: 12px;
        padding: 1.1rem 1.75rem;
        margin: 0.75rem auto 1.5rem auto;
        text-align: center;
        max-width: 650px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    ">
        <span style="font-size: 1.12rem; font-weight: 800; color: {green}; display: inline-block; margin-bottom: 0.3rem; letter-spacing: 0.04em;">
            🔒 SECURE DATA ISOLATION GUARANTEED
        </span>
        <div style="font-size: 0.98rem; color: {text}; font-weight: 600; opacity: 0.9; line-height: 1.45;">
            Your uploaded documents are strictly partitioned per tenant and never utilized to train public models.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if uploaded_files:
        # Validate all uploaded files before processing
        valid_uploads = True
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 50000000:
                st.error(f"❌ File too large: {uploaded_file.name} exceeds the 50MB limit.")
                valid_uploads = False
                break
            
            file_bytes = uploaded_file.getvalue()
            name_lower = uploaded_file.name.lower()
            is_valid = False
            if name_lower.endswith(".pdf"):
                is_valid = file_bytes.startswith(b"%PDF")
            elif name_lower.endswith((".docx", ".doc")):
                is_valid = file_bytes.startswith(b"PK\x03\x04")
                
            if not is_valid:
                st.error(f"❌ Security violation: {uploaded_file.name} is not a valid PDF or DOCX file (mime type signature mismatch).")
                valid_uploads = False
                break

        if valid_uploads:
            col_sub, _ = st.columns([2, 8])
            with col_sub:
                ingest_btn = st.button("📂 Index Documents", type="primary", use_container_width=True)
            if ingest_btn:
                status_placeholder = st.empty()
                temp_dir = os.path.join(base_dir, "temp_uploads")
                os.makedirs(temp_dir, exist_ok=True)
                temp_file_paths = []
                for uploaded_file in uploaded_files:
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_file_paths.append(temp_file_path)
                status_placeholder.markdown('<div class="engine-pill"><span class="engine-dot"></span>Extracting and indexing documents…</div>', unsafe_allow_html=True)
                success_count  = 0
                upload_errors  = []
                try:
                    chunks_added = ingest_documents_batch(
                        temp_file_paths, 
                        collection, 
                        tenant_id=tenant_id,
                        enable_pii_masking=st.session_state.get("pii_masking_enabled", True)
                    )
                    if chunks_added > 0:
                        success_count = len(uploaded_files)
                        # Refresh stats cache
                        refresh_db_stats()
                    else:
                        upload_errors.append("No text content could be extracted from the uploaded files.")
                except Exception as ex:
                    upload_errors.append(f"Error during indexing: {str(ex)}")
                finally:
                    for path in temp_file_paths:
                        if os.path.exists(path):
                            try: os.remove(path)
                            except Exception: pass
                    if os.path.exists(temp_dir):
                        try: os.rmdir(temp_dir)
                        except Exception: pass
                status_placeholder.empty()
                st.session_state.upload_finished      = True
                st.session_state.upload_success_count = success_count
                st.session_state.upload_errors        = upload_errors
                st.rerun()
    glass_card_close()

    # Data Security & Retention Settings
    glass_card_open()
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-space-between:space-between; margin-bottom:1.25rem; flex-wrap:wrap; gap:0.5rem;">
        <div style="display:flex; align-items:center; gap:0.6rem;">
            <span style="font-size:1.4rem;">🛡️</span>
            <div>
                <div class="section-title" style="margin:0; font-size:1.15rem;">Enterprise Security & Data Retention</div>
                <div style="font-size:0.8rem; color:{text_muted};">GDPR Compliant Data Purging & Automated PII Masking</div>
            </div>
        </div>
        <span class="badge badge-green" style="padding:4px 12px; font-size:0.75rem;">🔒 SOC 2 / GDPR Compliant</span>
    </div>
    """, unsafe_allow_html=True)

    col_ret1, col_ret2 = st.columns([1, 1], vertical_alignment="center")
    with col_ret1:
        retention_period = st.selectbox(
            "Auto-Delete Vector Data After:",
            ["7 Days (Free Trial)", "30 Days", "1 Year", "Never (Default)"],
            index=3,
            help="In compliance with GDPR/Data Privacy, your uploaded vectors will be permanently purged from our database after this period.",
            key="retention_period_select"
        )
    with col_ret2:
        pii_masking_enabled = st.checkbox(
            "Enable PII Data Masking (Hide Names, Emails, PAN & Aadhaar from AI)", 
            value=st.session_state.get("pii_masking_enabled", True),
            key="pii_masking_checkbox"
        )
        st.session_state.pii_masking_enabled = pii_masking_enabled

    st.write("")
    if st.button("🔒 Save Security Settings", use_container_width=True, key="save_sec_settings_btn"):
        st.session_state.retention_period = retention_period
        st.success("🔒 Security protocols updated. Settings applied to all future uploads & vector indexes.")
        
    glass_card_close()

    # Indexed documents table
    glass_card_open()
    section_header("Indexed Assets", "Documents currently stored in your vector knowledge base.")
    if sources_list:
        # Table Header
        col_idx, col_name, col_type, col_enc, col_status, col_action = st.columns(
            [0.6, 4.8, 1.5, 2.2, 1.5, 2.2], 
            vertical_alignment="center"
        )
        with col_idx:
            st.markdown("**#**")
        with col_name:
            st.markdown("**Filename**")
        with col_type:
            st.markdown("**Type**")
        with col_enc:
            st.markdown("**Encryption**")
        with col_status:
            st.markdown("**Status**")
        with col_action:
            st.markdown("**Action**")
        
        st.markdown("<hr style='margin:0.25rem 0 0.5rem 0 !important;'>", unsafe_allow_html=True)
        
        # Table Body Rows
        for idx, src in enumerate(sources_list):
            col_idx, col_name, col_type, col_enc, col_status, col_action = st.columns(
                [0.6, 4.8, 1.5, 2.2, 1.5, 2.2], 
                vertical_alignment="center"
            )
            with col_idx:
                st.write(f"{idx+1}")
            with col_name:
                st.write(src)
            with col_type:
                _, ext = os.path.splitext(src)
                st.markdown(f'<span class="badge badge-blue">{ext.upper().lstrip(".")}</span>', unsafe_allow_html=True)
            with col_enc:
                st.markdown('<span class="badge badge-blue" style="border-color:#10b981; color:#059669; background:rgba(16,185,129,0.08);">🔒 AES-256</span>', unsafe_allow_html=True)
            with col_status:
                st.markdown('<span class="badge badge-green">Ready</span>', unsafe_allow_html=True)
            with col_action:
                if st.button("🗑️ Delete", key=f"del_{src}", use_container_width=True):
                    try:
                        delete_document_from_kb(src, collection, tenant_id=tenant_id)
                        st.success(f"Deleted {src}!")
                        # Refresh stats cache
                        refresh_db_stats()
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Delete error: {str(ex)}")
            st.markdown("<hr style='margin:0.25rem 0 !important;'>", unsafe_allow_html=True)
        st.caption("ℹ️ All files are encrypted at rest using AES-256 and isolated by Tenant ID.")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🗂</div>
            <div class="section-title" style="text-align:center; margin-bottom:0.5rem;">No Documents Indexed</div>
            <div class="empty-state-text">Upload past proposals above to populate your knowledge base.</div>
        </div>
        """, unsafe_allow_html=True)
    glass_card_close()

    # Administration
    glass_card_open()
    section_header("⚙️ Index Administration", "Permanently delete all documents from your local vector database.")
    col_purge, _ = st.columns([3, 7])
    with col_purge:
        purge_btn = st.button("🚨 Reset Knowledge Base", use_container_width=True)
    if purge_btn:
        purged = False
        try:
            collection.delete(where={"tenant_id": tenant_id or ""})
            st.success("Your knowledge base index has been reset.")
            refresh_db_stats()
            if "current_response" in st.session_state:
                del st.session_state.current_response
            purged = True
        except Exception as ex:
            st.error(f"Reset error: {str(ex)}")
        if purged:
            import time
            time.sleep(0.5)
            st.rerun()
    glass_card_close()


# ================= TAB 6: ROI & Time Saved Dashboard =================
with tab_roi:
    glass_card_open()
    render_roi_dashboard_main()
    glass_card_close()



