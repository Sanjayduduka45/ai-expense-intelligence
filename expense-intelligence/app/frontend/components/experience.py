"""
Cohesive 5-Stage Financial Narrative Experience Component.

Structures analytical insights and AI generation into:
1. ROAST
2. WHAT IS ACTUALLY HAPPENING
3. WHERE YOUR MONEY IS GOING
4. WHAT YOU CAN RECOVER
5. RECOVERY PLAN
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from app.frontend.components.charts import (
    render_category_chart,
    render_discretionary_chart,
    render_top_expenses_chart,
    render_trend_chart,
)


def render_5stage_experience(
    factual: dict[str, Any],
    heuristics: dict[str, Any],
    ai_data: dict[str, Any] | None,
) -> None:
    """
    Render the complete structured 5-stage product experience.
    """
    # ── Stage 1: THE ROAST ───────────────────────────────────────────────────
    st.header("🔥 1. The Roast")
    if ai_data and ai_data.get("roast"):
        st.error(f"### *\"{ai_data['roast']}\"*")

        evidence_items = ai_data.get("roast_evidence", [])
        if evidence_items:
            with st.expander("🔍 **Why You Got Roasted (Supporting Evidence)**", expanded=True):
                for item in evidence_items:
                    st.markdown(f"- {item}")
        else:
            # Fallback factual evidence from calculations
            top_cat = next(iter(factual.get("spending_by_category", {}).keys()), "Top Category")
            top_pct = factual.get("category_percentages", {}).get(top_cat, 0.0)
            disc_pct = heuristics.get("discretionary_spending_estimate", {}).get("percentage_of_total", 0.0)
            with st.expander("🔍 **Why You Got Roasted (Supporting Evidence)**", expanded=True):
                st.markdown(f"- **Top Spending Area**: `{top_cat}` represents **{top_pct:.1f}%** of your total expenses.")
                st.markdown(f"- **Discretionary Spending**: Estimated at **{disc_pct:.1f}%** of total outflows.")
    else:
        st.info("Click **Generate AI Roast & Plan** above to reveal your personalized financial roast.")

    st.markdown("---")

    # ── Stage 2: WHAT IS ACTUALLY HAPPENING ───────────────────────────────────
    st.header("🚨 2. What Is Actually Happening")
    st.caption("Root-cause diagnostic analysis of your spending behavior and anomalies.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ⚠️ Identified Spending Problems")
        problems = ai_data.get("spending_problems", []) if ai_data else []
        if problems:
            for prob in problems:
                st.warning(f"**Issue:** {prob}")
        else:
            # Factual spending observations if AI not yet run
            top_3_pct = factual.get("spending_concentration", {}).get("top_3_categories_percentage", 0.0)
            st.markdown(f"- **Category Dominance**: Top 3 categories consume **{top_3_pct:.1f}%** of total budget.")
            disc_amt = heuristics.get("discretionary_spending_estimate", {}).get("amount", 0.0)
            if disc_amt > 0:
                st.markdown(f"- **Discretionary Volume**: ${disc_amt:,.2f} spent across non-essential categories.")

    with col2:
        st.markdown("#### ⚡ Unusual Spending Observations")
        anomalies = heuristics.get("unusual_spending_observations", [])
        if anomalies:
            for a in anomalies[:4]:
                st.info(
                    f"**${a.get('amount', 0):,.2f}** at `{a.get('description', '')}` ({a.get('category', '')})  \n"
                    f"*{a.get('reason', '')}*"
                )
        else:
            st.caption("No statistical anomalies or unusual single-transaction spikes detected.")

    st.markdown("---")

    # ── Stage 3: WHERE YOUR MONEY IS GOING ────────────────────────────────────
    st.header("📊 3. Where Your Money Is Going")
    st.caption("Detailed breakdown, concentration, and category flow.")

    # 2x2 Plotly Grid
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        render_category_chart(
            spending_by_category=factual.get("spending_by_category", {}),
            category_percentages=factual.get("category_percentages", {}),
        )
    with row1_c2:
        render_trend_chart(
            daily_spending=factual.get("daily_spending", []),
            monthly_spending=factual.get("monthly_spending", []),
        )

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        render_discretionary_chart(
            total_spending=factual.get("total_spending", 0.0),
            discretionary_amount=heuristics.get("discretionary_spending_estimate", {}).get("amount", 0.0),
        )
    with row2_c2:
        render_top_expenses_chart(
            largest_expenses=factual.get("largest_expenses", [])
        )

    st.markdown("---")

    # ── Stage 4: WHAT YOU CAN RECOVER ─────────────────────────────────────────
    st.header("💰 4. What You Can Recover")
    st.caption("Quantified savings opportunities and subscription commitments.")

    savings_list = heuristics.get("potential_savings_opportunities", [])
    total_potential_savings = sum(
        s.get("potential_monthly_impact") or 0.0 for s in savings_list
    )
    yearly_potential_savings = total_potential_savings * 12

    rec_col1, rec_col2 = st.columns([1, 2])
    with rec_col1:
        st.metric(
            label="Estimated Monthly Recovery",
            value=f"${total_potential_savings:,.2f}/mo",
            delta=f"${yearly_potential_savings:,.2f}/yr potential",
            delta_color="normal",
            help="Estimated monthly cash flow that can be preserved.",
        )
        st.caption("*Based on deterministic heuristics and detected commitments.*")

    with rec_col2:
        # Recurring commitments audit
        recurring = heuristics.get("recurring_expenses", [])
        if recurring:
            st.markdown("##### 🔁 Recurring Commitments Audit")
            rec_df = pd.DataFrame(
                [
                    {
                        "Service / Merchant": r.get("description"),
                        "Amount": f"${r.get('amount', 0):,.2f}",
                        "Frequency": r.get("estimated_frequency"),
                        "Occurrences": r.get("occurrences"),
                        "Est. Annual Cost": f"${r.get('amount', 0) * (12 if r.get('estimated_frequency') == 'Monthly' else r.get('occurrences', 1)):,.2f}",
                    }
                    for r in recurring
                ]
            )
            st.dataframe(rec_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No recurring subscription patterns detected.")

    st.markdown("---")

    # ── Stage 5: THE RECOVERY PLAN ────────────────────────────────────────────
    st.header("🛡️ 5. The Recovery Plan")
    st.caption("Actionable, prioritized recommendations with estimated financial impact.")

    structured_plan = ai_data.get("structured_recovery_plan", []) if ai_data else []

    if structured_plan:
        for idx, item in enumerate(structured_plan, start=1):
            priority = item.get("priority", "Medium").capitalize()
            p_badge = "🔴 High Priority" if priority == "High" else ("🟡 Medium Priority" if priority == "Medium" else "🟢 Low Priority")

            m_saving = item.get("estimated_monthly_saving")
            y_saving = item.get("estimated_yearly_saving")
            if m_saving and not y_saving:
                y_saving = m_saving * 12

            with st.container():
                col_h, col_s = st.columns([3, 1])
                with col_h:
                    st.markdown(f"**Step {idx}: {item.get('action', '')}**  \n`{p_badge}`")
                    st.markdown(f"*Root Problem:* {item.get('problem', '')}")
                with col_s:
                    if m_saving:
                        st.metric(
                            label="Est. Monthly Saving",
                            value=f"+${m_saving:,.2f}",
                            delta=f"+${y_saving:,.2f}/yr" if y_saving else None,
                        )
                        st.caption("*(Heuristic estimate)*")
                    else:
                        st.caption("Qualitative efficiency")
                st.markdown("---")
    elif ai_data and ai_data.get("recovery_plan"):
        # Fallback to text list if structured items were not generated
        for idx, step in enumerate(ai_data["recovery_plan"], 1):
            st.markdown(f"**{idx}.** {step}")
    else:
        st.info("Click **Generate AI Roast & Plan** to produce your custom, prioritized recovery roadmap.")
