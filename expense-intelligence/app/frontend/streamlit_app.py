"""
AI Expense Intelligence — Streamlit application shell.

Phase 0: project identity shell only.
No expense logic, no AI calls, no data processing yet.
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

import streamlit as st

from app.frontend.utils.api_client import fetch_health
from app.shared.constants import APP_NAME, APP_TAGLINE, APP_VERSION

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="💸",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def render_header() -> None:
    """Render the application identity header."""
    st.title(f"💸 {APP_NAME}")
    st.markdown(f"### *{APP_TAGLINE}*")
    st.caption(f"Version {APP_VERSION} · Phase 0 — Foundation")
    st.divider()


def render_backend_status() -> None:
    """Display live backend health status."""
    st.subheader("🔌 Backend Status")
    with st.spinner("Checking backend health…"):
        health = fetch_health()

    if health.get("status") == "ok":
        st.success(
            f"Backend is **online** · env: `{health.get('environment', 'unknown')}` "
            f"· version: `{health.get('version', '?')}`"
        )
    else:
        detail = health.get("detail", "Unknown error")
        st.warning(
            f"Backend is **{health.get('status', 'unreachable')}**. "
            f"Start the backend with `uvicorn app.backend.main:app --reload`.  \n"
            f"`{detail}`"
        )


def render_coming_soon() -> None:
    """Placeholder for features planned in later phases."""
    st.divider()
    st.subheader("🚧 Coming in later phases")
    features = [
        "📤 Upload monthly expense CSV / Excel files",
        "📊 Spending pattern analysis with interactive charts",
        "🔥 AI-powered expense roast (via Gemini)",
        "📋 Personalised recovery plan",
        "🤖 AI assistant — ask questions about your expenses",
    ]
    for feature in features:
        st.markdown(f"- {feature}")


def main() -> None:
    """Application entry point called by Streamlit."""
    render_header()
    render_backend_status()
    render_coming_soon()


if __name__ == "__main__":
    main()
