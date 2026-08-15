"""
AI Expense Intelligence — Streamlit Application.

Roast • Analyze • Recover
Light Theme Financial Intelligence Dashboard matching Image 2 reference UI:
- Full 3-Column Layout (Left Navigation Sidebar, Center Dashboard, Dedicated Right-Side AI Assistant Panel)
- Strict INR (₹) Currency Representation
- Clean Card Structure & Soft Pastel Accents
- 5-Step Collapsible Workflow Accordion
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── Ensure the project root is on sys.path when running via:
#    streamlit run app/frontend/streamlit_app.py
# ─────────────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

from app.frontend.components import (
    render_5stage_experience,
    render_assistant_chat,
    render_category_chart,
    render_discretionary_chart,
    render_kpi_cards,
    render_top_expenses_chart,
    render_trend_chart,
)
from app.frontend.utils.api_client import (
    analyze_expenses,
    fetch_ai_roast,
    fetch_health,
    upload_expense_file,
)
from app.frontend.utils.currency import format_inr
from app.shared.constants import APP_NAME, APP_TAGLINE, APP_VERSION

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_custom_css() -> None:
    """Inject CSS to enforce modern light financial dashboard styling."""
    st.markdown(
        """
        <style>
        /* ── Base Light Theme ── */
        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* ── Header adjustments ── */
        header[data-testid="stHeader"] {
            background-color: rgba(248, 250, 252, 0.8) !important;
            backdrop-filter: blur(8px);
        }

        /* ── Card Containers ── */
        div[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
            margin-bottom: 14px !important;
        }

        div[data-testid="stExpander"] details summary {
            font-weight: 600 !important;
            color: #0F172A !important;
        }

        /* ── Primary Buttons ── */
        div.stButton > button[kind="primary"] {
            background-color: #6366F1 !important;
            border-color: #6366F1 !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(99, 102, 241, 0.2) !important;
            transition: all 0.15s ease-in-out;
        }

        div.stButton > button[kind="primary"]:hover {
            background-color: #4F46E5 !important;
            border-color: #4F46E5 !important;
            transform: translateY(-1px);
        }

        /* ── Secondary / Outline Buttons ── */
        div.stButton > button[kind="secondary"] {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            color: #334155 !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
        }

        div.stButton > button[kind="secondary"]:hover {
            background-color: #F1F5F9 !important;
            border-color: #94A3B8 !important;
        }

        /* ── Sidebar Navigation Styling ── */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }

        /* ── DataFrames ── */
        div[data-testid="stDataFrame"] {
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            background-color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    """Initialize session state keys safely."""
    st.session_state.setdefault("expenses_data", None)
    st.session_state.setdefault("ingestion_summary", None)
    st.session_state.setdefault("analytics_report", None)
    st.session_state.setdefault("ai_roast", None)
    st.session_state.setdefault("chat_messages", [])


def render_sidebar_nav() -> None:
    """Render the left navigation sidebar matching Image 2 structure."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <span style="font-size: 1.5rem;">💸</span>
                <div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; line-height: 1.2;">{APP_NAME}</div>
                    <div style="font-size: 0.72rem; color: #6366F1; font-weight: 600;">{APP_TAGLINE}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='margin: 8px 0 14px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        st.markdown("<span style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em;'>OVERVIEW</span>", unsafe_allow_html=True)
        st.markdown("🔹 **Financial Dashboard**")

        st.markdown("<br><span style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em;'>WORKFLOW</span>", unsafe_allow_html=True)
        st.markdown("1. 🔥 **The Roast**")
        st.markdown("2. 📊 **What Is Happening**")
        st.markdown("3. 📊 **Where Money Goes**")
        st.markdown("4. 💰 **What You Can Recover**")
        st.markdown("5. 🛡️ **Recovery Plan**")

        st.markdown("<br><span style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em;'>DATA</span>", unsafe_allow_html=True)
        st.markdown("📁 **Upload & Manage**")

        st.markdown("<br><span style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em;'>AI ASSISTANT</span>", unsafe_allow_html=True)
        st.markdown("🤖 **Ask Assistant** &nbsp;<span style='background-color: #EEF2FF; color: #4F46E5; font-size: 0.65rem; font-weight: 600; padding: 2px 6px; border-radius: 9999px;'>Online</span>", unsafe_allow_html=True)

        st.markdown("<hr style='margin: 20px 0 12px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        # Reset button
        if st.session_state.get("expenses_data"):
            if st.button("🔄 Reset / Clear Data", use_container_width=True):
                st.session_state["expenses_data"] = None
                st.session_state["ingestion_summary"] = None
                st.session_state["analytics_report"] = None
                st.session_state["ai_roast"] = None
                st.session_state["chat_messages"] = []
                st.rerun()

        st.caption(f"v{APP_VERSION} • Light Mode")


def render_header() -> None:
    """Render top clean horizontal header card."""
    health = fetch_health()
    status_text = "Online" if health.get("status") == "ok" else "Offline"
    status_bg = "#ECFDF5" if status_text == "Online" else "#FEF2F2"
    status_color = "#059669" if status_text == "Online" else "#DC2626"

    header_html = f"""
    <div style="
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background-color: #EEF2FF; padding: 8px 10px; border-radius: 8px; font-size: 1.3rem;">💸</div>
            <div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #0F172A;">{APP_NAME}</div>
                <div style="font-size: 0.78rem; color: #64748B; font-weight: 500;">{APP_TAGLINE}</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="background-color: {status_bg}; color: {status_color}; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 9999px;">
                ● Backend {status_text}
            </div>
            <div style="background-color: #F1F5F9; color: #475569; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 8px;">
                v{APP_VERSION}
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def _process_and_store_csv_data(file_bytes: bytes, filename: str) -> None:
    """Helper to upload, parse, and analyze CSV data into session state."""
    with st.spinner("Validating and normalizing CSV transactions..."):
        upload_res = upload_expense_file(file_bytes, filename)

    if upload_res.get("success"):
        summary_data = upload_res["data"]
        parsed_expenses = summary_data.get("data", [])

        st.session_state["ingestion_summary"] = summary_data
        st.session_state["expenses_data"] = parsed_expenses
        st.session_state["ai_roast"] = None
        st.session_state["chat_messages"] = []

        with st.spinner("Computing deterministic analytics engine..."):
            analytics_res = analyze_expenses(parsed_expenses)
            if analytics_res.get("success"):
                st.session_state["analytics_report"] = analytics_res["data"]

        st.toast(f"Loaded {len(parsed_expenses)} transactions from {filename}", icon="✅")
    else:
        st.error(f"Validation error: {upload_res.get('detail')}")


def render_upload_section() -> None:
    """Render the upload section with side-by-side Quick Start card."""
    with st.expander("📤 **Upload & Manage Expense Data**", expanded=st.session_state["expenses_data"] is None):
        st.caption("Upload your transaction CSV export. We'll automatically normalize columns and run deterministic financial analysis.")

        col_up, col_demo = st.columns([3, 1])

        with col_up:
            with st.form("upload_form", clear_on_submit=False):
                uploaded_file = st.file_uploader(
                    "Select Expense CSV File",
                    type=["csv"],
                    help="CSV containing date, description, amount (INR ₹), and optional category columns.",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("Upload & Process", type="primary", use_container_width=True)

                if submitted:
                    if uploaded_file is None:
                        st.error("Please choose a CSV file first.")
                    else:
                        _process_and_store_csv_data(uploaded_file.getvalue(), uploaded_file.name)
                        st.rerun()

        with col_demo:
            st.markdown(
                """
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; height: 100%;">
                    <div style="font-size: 0.82rem; font-weight: 600; color: #0F172A; margin-bottom: 2px;">⚡ Quick Start</div>
                    <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 8px;">Try demo data with pre-populated INR transactions.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🧪 Load Sample Data", key="btn_load_sample_top", use_container_width=True):
                sample_path = _PROJECT_ROOT / "data" / "sample" / "sample_expenses.csv"
                if sample_path.exists():
                    _process_and_store_csv_data(sample_path.read_bytes(), "sample_expenses.csv")
                    st.rerun()
                else:
                    st.error("Sample dataset file not found.")

    # ── Validation Status Banner & Preview ─────────────────────────────────────
    expenses = st.session_state.get("expenses_data")
    summary = st.session_state.get("ingestion_summary")
    if expenses and summary:
        dates = [e.get("date") for e in expenses if e.get("date")]
        date_range_str = f"{min(dates)} to {max(dates)}" if dates else "N/A"

        st.markdown(
            f"""
            <div style="
                background-color: #ECFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 10px;
                padding: 10px 16px;
                margin-bottom: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: #059669; font-weight: 700; font-size: 1rem;">✓</span>
                    <span style="font-weight: 600; color: #065F46; font-size: 0.88rem;">Successfully loaded and validated</span>
                    <span style="color: #64748B; font-size: 0.8rem;">• {len(expenses)} transactions • {date_range_str}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Preview Data Table
        with st.expander("👁️ **Preview Normalized Transaction Records (INR ₹)**", expanded=False):
            df = pd.DataFrame(expenses)
            df_display = df.copy()
            if "amount" in df_display.columns:
                df_display["amount"] = df_display["amount"].apply(format_inr)
            st.dataframe(df_display, use_container_width=True, hide_index=True)


def trigger_ai_generation() -> None:
    """Callback to trigger AI Roast & Recovery Plan generation."""
    expenses = st.session_state.get("expenses_data")
    if not expenses:
        return
    with st.spinner("Generating AI Roast and Actionable Recovery Plan..."):
        roast_res = fetch_ai_roast(expenses)
        if roast_res.get("success"):
            st.session_state["ai_roast"] = roast_res["data"]
            st.toast("AI Roast and Recovery Plan generated!", icon="🔥")
            st.rerun()
        else:
            st.error(f"AI Service Error: {roast_res.get('detail')}")


def render_main_dashboard() -> None:
    """Render the central dashboard (KPI cards, 2x2 Plotly grid, and 5-Step Workflow)."""
    report = st.session_state.get("analytics_report")
    expenses = st.session_state.get("expenses_data")
    if not report or not expenses:
        return

    factual = report.get("factual_metrics", {})
    heuristics = report.get("heuristic_insights", {})
    ai_data = st.session_state.get("ai_roast")

    # ── 1. 5 KPI Cards ────────────────────────────────────────────────────────
    render_kpi_cards(factual, heuristics)
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # ── 2. Analytics Visualizations (2x2 Grid) ────────────────────────────────
    st.markdown("### 📊 Spending Analytics")
    st.caption("Visual breakdown of category allocations, daily run rates, essential ratios, and top outflows.")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        with st.container():
            render_category_chart(
                factual.get("spending_by_category", {}),
                factual.get("category_percentages", {}),
            )
    with col_g2:
        with st.container():
            render_trend_chart(
                factual.get("daily_spending", []),
                factual.get("monthly_spending", []),
            )

    col_g3, col_g4 = st.columns(2)
    with col_g3:
        with st.container():
            render_discretionary_chart(
                factual.get("total_spending", 0.0),
                heuristics.get("discretionary_spending_estimate", {}).get("amount", 0.0),
            )
    with col_g4:
        with st.container():
            render_top_expenses_chart(factual.get("largest_expenses", []))

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # ── 3. 5-Step Analysis Workflow ───────────────────────────────────────────
    render_5stage_experience(
        factual=factual,
        heuristics=heuristics,
        ai_data=ai_data,
        on_generate_click=trigger_ai_generation,
    )


def main() -> None:
    """Application main entry point."""
    inject_custom_css()
    init_session_state()
    render_sidebar_nav()
    render_header()

    # ── 3-Column Split: Center Main Dashboard (70%) + Right AI Assistant Panel (30%) ──
    col_main, col_assistant = st.columns([2.3, 1.0], gap="medium")

    with col_main:
        render_upload_section()
        render_main_dashboard()

    with col_assistant:
        render_assistant_chat(st.session_state.get("expenses_data"))


if __name__ == "__main__":
    main()
