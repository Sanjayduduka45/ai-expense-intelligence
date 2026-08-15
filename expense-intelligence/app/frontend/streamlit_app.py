"""
AI Expense Intelligence — Streamlit Application.

Roast • Analyze • Recover
Complete Phase 6-10 narrative experience:
1. ROAST
2. WHAT IS ACTUALLY HAPPENING
3. WHERE YOUR MONEY IS GOING
4. WHAT YOU CAN RECOVER
5. RECOVERY PLAN
+ Interactive AI Expense Assistant
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
    render_kpi_cards,
)
from app.frontend.utils.api_client import (
    analyze_expenses,
    fetch_ai_roast,
    fetch_health,
    upload_expense_file,
)
from app.shared.constants import APP_NAME, APP_TAGLINE, APP_VERSION

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def init_session_state() -> None:
    """Initialize session state keys safely."""
    st.session_state.setdefault("expenses_data", None)
    st.session_state.setdefault("ingestion_summary", None)
    st.session_state.setdefault("analytics_report", None)
    st.session_state.setdefault("ai_roast", None)
    st.session_state.setdefault("chat_messages", [])


def render_header() -> None:
    """Render top application header and brand identity."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"💸 {APP_NAME}")
        st.markdown(f"#### *{APP_TAGLINE}*")
    with col2:
        st.caption(f"Version {APP_VERSION}")
        health = fetch_health()
        if health.get("status") == "ok":
            st.success(f"● Online ({health.get('environment', 'dev')})")
        else:
            st.warning("● Backend Offline")
    st.divider()


def _process_and_store_csv_data(file_bytes: bytes, filename: str) -> None:
    """Helper to upload, parse, and analyze CSV data into session state."""
    with st.spinner("Validating and parsing CSV..."):
        upload_res = upload_expense_file(file_bytes, filename)

    if upload_res.get("success"):
        summary_data = upload_res["data"]
        parsed_expenses = summary_data.get("data", [])

        st.session_state["ingestion_summary"] = summary_data
        st.session_state["expenses_data"] = parsed_expenses
        st.session_state["ai_roast"] = None  # reset prior roast
        st.session_state["chat_messages"] = []  # reset chat

        # Automatically compute deterministic analytics
        with st.spinner("Computing deterministic analytics engine..."):
            analytics_res = analyze_expenses(parsed_expenses)
            if analytics_res.get("success"):
                st.session_state["analytics_report"] = analytics_res["data"]

        st.success(f"Successfully loaded and validated **{filename}** ({len(parsed_expenses)} valid rows)!")
    else:
        st.error(f"Validation error: {upload_res.get('detail')}")


def render_upload_and_preview() -> None:
    """Handle Step 1 (Upload), Step 2 (Validate), and Step 3 (Preview)."""
    with st.expander("📤 **Upload & Manage Expense Data**", expanded=st.session_state["expenses_data"] is None):
        st.write(
            "Upload your transaction CSV export. The engine will automatically normalize columns "
            "(`date`, `description`, `category`, `amount`) and execute deterministic financial intelligence."
        )

        col_upload, col_sample = st.columns([3, 1])

        with col_upload:
            with st.form("upload_form", clear_on_submit=False):
                uploaded_file = st.file_uploader(
                    "Select Expense CSV File",
                    type=["csv"],
                    help="CSV containing date, description, amount, and optional category columns.",
                )
                submitted = st.form_submit_button("Upload & Process", type="primary", use_container_width=True)

                if submitted:
                    if uploaded_file is None:
                        st.error("Please choose a CSV file first.")
                    else:
                        _process_and_store_csv_data(uploaded_file.getvalue(), uploaded_file.name)

        with col_sample:
            st.markdown("**Quick Demo:**")
            st.caption("Try the platform immediately with pre-configured sample financial transactions.")
            if st.button("🧪 Load Sample Data", use_container_width=True):
                sample_path = _PROJECT_ROOT / "data" / "sample" / "sample_expenses.csv"
                if sample_path.exists():
                    _process_and_store_csv_data(sample_path.read_bytes(), "sample_expenses.csv")
                else:
                    st.error("Sample dataset file not found.")

    # Display Ingestion Summary & Rejected Rows if applicable
    summary = st.session_state.get("ingestion_summary")
    if summary:
        errors = summary.get("errors", [])
        if errors:
            with st.expander(f"⚠️ **Validation Warnings: {len(errors)} Row(s) Skipped**", expanded=False):
                st.dataframe(pd.DataFrame(errors), use_container_width=True)

        records = st.session_state.get("expenses_data", [])
        if records:
            with st.expander("👁️ **Preview Normalized Transaction Records**", expanded=False):
                df = pd.DataFrame(records)
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                        "date": "Date",
                        "description": "Description",
                        "category": "Category",
                    },
                )


def render_narrative_experience() -> None:
    """Render the structured 5-stage experience and AI trigger."""
    report = st.session_state.get("analytics_report")
    expenses = st.session_state.get("expenses_data")
    if not report or not expenses:
        return

    factual = report.get("factual_metrics", {})
    heuristics = report.get("heuristic_insights", {})

    # Top KPI Metrics Overview
    render_kpi_cards(factual, heuristics)
    st.markdown("---")

    # AI Roast & Recovery Generation CTA Bar
    col_cta_text, col_cta_btn = st.columns([3, 1])
    with col_cta_text:
        st.subheader("⚡ AI Roast & Recovery Engine")
        st.caption("Generate your evidence-based financial roast, root-cause diagnostic, and prioritized recovery roadmap.")
    with col_cta_btn:
        if st.button("🔥 Generate AI Roast & Plan", type="primary", use_container_width=True):
            with st.spinner("Calling Gemini AI financial engine..."):
                roast_res = fetch_ai_roast(expenses)
                if roast_res.get("success"):
                    st.session_state["ai_roast"] = roast_res["data"]
                    st.toast("AI Roast and Recovery Plan generated!", icon="🔥")
                else:
                    st.error(f"AI Service Error: {roast_res.get('detail')}")

    st.markdown("---")

    # Render 5-Stage Product Experience
    ai_data = st.session_state.get("ai_roast")
    render_5stage_experience(factual=factual, heuristics=heuristics, ai_data=ai_data)

    st.markdown("---")

    # Interactive Assistant Chat
    render_assistant_chat(expenses)


def main() -> None:
    """Application main entry point."""
    init_session_state()
    render_header()
    render_upload_and_preview()
    render_narrative_experience()


if __name__ == "__main__":
    main()
