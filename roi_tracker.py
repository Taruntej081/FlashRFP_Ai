import time
import streamlit as st

# ==========================================
# ⏱️ ROI & TIME TRACKING ENGINE
# ==========================================
def init_roi_tracker():
    """Initialize the ROI tracking session state"""
    if "roi_stats" not in st.session_state:
        st.session_state.roi_stats = {
            "total_questions_answered": 0,
            "total_ai_processing_time": 0.0,  # In seconds
            "total_boq_rows_processed": 0
        }

def log_ai_performance(start_time, end_time, task_type, quantity=1):
    """Logs AI execution duration and quantities for ROI metrics"""
    init_roi_tracker()
    duration = max(0.0, end_time - start_time)
    
    if task_type == "question":
        st.session_state.roi_stats["total_questions_answered"] += quantity
        st.session_state.roi_stats["total_ai_processing_time"] += duration
    elif task_type == "boq":
        st.session_state.roi_stats["total_boq_rows_processed"] += quantity
        st.session_state.roi_stats["total_ai_processing_time"] += duration

def calculate_roi(hourly_rate: float = 500.0):
    """Calculates human time saved and financial ROI metrics with exact time formatting"""
    init_roi_tracker()
    stats = st.session_state.roi_stats
    
    # Industry benchmark: 1 human takes ~30 minutes to research & draft 1 RFP question,
    # and ~2 minutes to analyze & fill 1 BOQ Excel line item.
    human_minutes_saved = (stats["total_questions_answered"] * 30) + (stats["total_boq_rows_processed"] * 2)
    ai_seconds = float(stats["total_ai_processing_time"])
    ai_minutes = ai_seconds / 60.0
    
    hours_saved = human_minutes_saved / 60.0
    cost_saved = hours_saved * hourly_rate
    
    # Exact Hours & Minutes formatting for human time
    human_hrs_int = int(human_minutes_saved // 60)
    human_mins_rem = int(human_minutes_saved % 60)
    if human_hrs_int > 0 and human_mins_rem > 0:
        human_formatted = f"{human_hrs_int}h {human_mins_rem}m"
    elif human_hrs_int > 0:
        human_formatted = f"{human_hrs_int} hrs"
    else:
        human_formatted = f"{human_minutes_saved} mins"

    # Exact Minutes & Seconds formatting for AI time
    ai_mins_int = int(ai_seconds // 60)
    ai_secs_rem = round(ai_seconds % 60, 1)
    if ai_mins_int > 0:
        ai_formatted = f"{ai_mins_int}m {ai_secs_rem}s"
    else:
        ai_formatted = f"{ai_seconds:.1f}s"

    # Speedup ratio math
    manual_secs = human_minutes_saved * 60.0
    speedup = (manual_secs / max(0.1, ai_seconds)) if human_minutes_saved > 0 else 1.0
    
    return {
        "questions": stats["total_questions_answered"],
        "boq_rows": stats["total_boq_rows_processed"],
        "ai_seconds": round(ai_seconds, 1),
        "ai_minutes": round(ai_minutes, 2),
        "ai_formatted": ai_formatted,
        "human_minutes_saved": human_minutes_saved,
        "human_hours_saved": hours_saved,
        "human_formatted": human_formatted,
        "cost_saved": cost_saved,
        "hourly_rate": hourly_rate,
        "speedup": round(speedup, 1)
    }

def render_elevated_metric_card(title: str, value: str, badge_text: str = "", badge_type: str = "green", subtitle: str = ""):
    """
    Renders an elevated HeroUI SaaS Metric Card matching the site's design system:
    - Integrated top accent line (merged seamlessly with site theme)
    - Uppercase letter-spaced header title
    - Top-right rounded pill badge
    - Bold prominent value typography
    - Bottom sub-caption text
    - Zero indented lines to prevent Streamlit codeblock auto-formatting
    """
    badge_bg = "rgba(16, 185, 129, 0.12)" if badge_type == "green" else ("rgba(239, 68, 68, 0.12)" if badge_type == "red" else "rgba(59, 130, 246, 0.12)")
    badge_color = "#10B981" if badge_type == "green" else ("#EF4444" if badge_type == "red" else "#3B82F6")
    badge_border = "rgba(16, 185, 129, 0.25)" if badge_type == "green" else ("rgba(239, 68, 68, 0.25)" if badge_type == "red" else "rgba(59, 130, 246, 0.25)")
    
    badge_html = ""
    if badge_text:
        badge_html = f'<div style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; border-radius: 9999px; padding: 2px 8px; font-size: 0.72rem; font-weight: 700; display: inline-flex; align-items: center; white-space: nowrap;">{badge_text}</div>'

    html = f'''<div style="background: #ffffff; border: 1px solid rgba(226, 232, 240, 0.95); border-top: 4px solid #10B981; border-radius: 14px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03); padding: 18px 20px; margin-bottom: 1rem; transition: all 0.2s ease;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
<div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B;">{title}</div>
{badge_html}
</div>
<div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; line-height: 1.25; margin: 4px 0 6px 0;">{value}</div>
<div style="font-size: 0.78rem; font-weight: 500; color: #94A3B8;">{subtitle}</div>
</div>'''

    st.markdown(html, unsafe_allow_html=True)

def render_roi_dashboard():
    """Renders HeroUI ROI & Time Saved dashboard in the sidebar"""
    init_roi_tracker()
    rate = st.session_state.get("hourly_rate_input", 500.0)
    roi = calculate_roi(hourly_rate=rate)
    
    st.sidebar.markdown("<hr style='margin:1.5rem 0 1rem 0 !important;'>", unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; color: #10B981; margin-bottom: 0.75rem;">
            📊 ROI & Time Saved Dashboard
        </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        render_elevated_metric_card(
            title="Labor Saved",
            value=f"₹{roi['cost_saved']:,.0f}",
            badge_text=f"⚡ {int(roi['speedup'])}x Faster",
            badge_type="green",
            subtitle=f"{roi['human_formatted']} saved @ ₹{int(rate)}/h"
        )
        render_elevated_metric_card(
            title="Drafts Generated",
            value=f"{roi['questions']}",
            badge_text=f"▲ +{roi['boq_rows']} BOQ",
            badge_type="blue",
            subtitle=f"AI Time: {roi['ai_formatted']}"
        )
        
        st.markdown("<hr style='margin:0.75rem 0 !important;'>", unsafe_allow_html=True)
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            if st.button("🎲 Demo", use_container_width=True, key="sb_demo_roi_btn", help="Populates dashboard with sample analytics for demonstrations."):
                st.session_state.roi_stats = {
                    "total_questions_answered": 142,
                    "total_ai_processing_time": 384.5,
                    "total_boq_rows_processed": 85
                }
                st.rerun()
        with col_sb2:
            if st.button("🔄 Reset", use_container_width=True, key="sb_reset_roi_btn", help="Resets ROI metrics to 0."):
                st.session_state.roi_stats = {
                    "total_questions_answered": 0,
                    "total_ai_processing_time": 0.0,
                    "total_boq_rows_processed": 0
                }
                st.rerun()

def render_roi_dashboard_main():
    """Renders full-width HeroUI Enterprise ROI & Time Saved Dashboard in main tab"""
    init_roi_tracker()
    
    st.markdown('<div class="section-title" style="margin-bottom:0.25rem;">📈 Enterprise ROI & Time Saved Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub" style="margin-bottom:1.5rem;">'
        'Real-time measure of human productivity gains, labor cost reduction, and AI execution efficiency.'
        '</div>',
        unsafe_allow_html=True
    )

    # Custom Hourly Labor Rate Calculator Input
    st.markdown("### ⚙️ Financial Value Calculator")
    col_calc1, col_calc2 = st.columns([1, 1])
    with col_calc1:
        hourly_rate = st.number_input(
            "Average Hourly Human Labor Value (₹/hr):",
            min_value=100,
            max_value=10000,
            value=st.session_state.get("hourly_rate_input", 500),
            step=50,
            key="hourly_rate_input",
            help="Customize the hourly rate for your bid management team to calculate exact cost savings."
        )

    # Now calculate ROI using the active user-configured hourly_rate
    roi = calculate_roi(hourly_rate=float(hourly_rate))

    with col_calc2:
        calc_html = f'''<div style="background: rgba(16, 185, 129, 0.08); border: 1px solid #10B981; border-radius: 14px; padding: 16px; margin-top: 0.5rem;">
<div style="font-size: 0.75rem; color: #059669; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Total Financial Value Realized</div>
<div style="font-size: 1.85rem; font-weight: 800; color: #10B981; margin-top: 4px;">₹{roi['cost_saved']:,.0f}</div>
</div>'''
        st.markdown(calc_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Top Metric Banner Cards dynamically responding to hourly rate
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_elevated_metric_card(
            title="EST. LABOR COST SAVED",
            value=f"₹{roi['cost_saved']:,.0f}",
            badge_text="▲ +18.5%",
            badge_type="green",
            subtitle=f"Labor rate: ₹{int(hourly_rate):,}/hr"
        )
    with col2:
        render_elevated_metric_card(
            title="RFP DRAFTS GENERATED",
            value=f"{roi['questions']}",
            badge_text=f"▲ +{roi['questions']} new",
            badge_type="green",
            subtitle="Synthesized responses"
        )
    with col3:
        speedup_badge = f"⚡ {int(roi['speedup'])}x Faster" if roi['speedup'] > 1 else "▲ High Speed"
        render_elevated_metric_card(
            title="HUMAN HOURS SAVED",
            value=f"{roi['human_formatted']}",
            badge_text=speedup_badge,
            badge_type="green",
            subtitle=f"{roi['human_minutes_saved']:,} mins manual work"
        )
    with col4:
        render_elevated_metric_card(
            title="BOQ LINE ITEMS FILLED",
            value=f"{roi['boq_rows']}",
            badge_text=f"▲ {roi['boq_rows']} rows",
            badge_type="blue",
            subtitle="Excel specs filled"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Benchmark Efficiency Comparison Breakdown
    st.markdown("### ⚡ Execution Speed Breakdown")
    col_spd1, col_spd2 = st.columns(2)
    with col_spd1:
        st.info(f"⏱️ **Manual Team Execution Time**: ~{roi['human_formatted']} ({roi['human_minutes_saved']:,} total mins)")
    with col_spd2:
        st.success(f"⚡ **FlashRFP AI Processing Time**: {roi['ai_formatted']} ({roi['ai_seconds']} total secs) — **{int(roi['speedup'])}x Speedup**")

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("### 🛠️ Analytics Controls")
    col_ctrl1, col_ctrl2 = st.columns(2)
    with col_ctrl1:
        if st.button("🎲 Load Demo Analytics", use_container_width=True, key="main_demo_roi_btn", help="Populates the dashboard with sample data for demonstrations."):
            st.session_state.roi_stats = {
                "total_questions_answered": 142,
                "total_ai_processing_time": 384.5,
                "total_boq_rows_processed": 85
            }
            st.rerun()
    with col_ctrl2:
        if st.button("🔄 Reset Analytics", use_container_width=True, key="main_reset_roi_btn", help="Clears stats for a new project."):
            st.session_state.roi_stats = {
                "total_questions_answered": 0,
                "total_ai_processing_time": 0.0,
                "total_boq_rows_processed": 0
            }
            st.rerun()
