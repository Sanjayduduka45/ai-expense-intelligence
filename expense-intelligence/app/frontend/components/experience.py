"""
Cohesive 5-Stage Financial Narrative Experience Component.

Structures analytical insights and AI generation into a clean, light-themed 5-step accordion workflow:
1. The Roast
2. What Is Actually Happening
3. Where Your Money Is Going
4. What You Can Recover
5. The Recovery Plan
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from app.frontend.utils.currency import format_inr


def render_5stage_experience(
    factual: dict[str, Any],
    heuristics: dict[str, Any],
    ai_data: dict[str, Any] | None,
    on_generate_click: Any = None,
) -> None:
    """
    Render the structured 5-step accordion workflow.
    """
    st.markdown("### 📋 5-Step Analysis Workflow")
    st.caption("Review your spending diagnosis, root-cause patterns, and actionable recovery roadmap.")

    # ── Step 1: THE ROAST ───────────────────────────────────────────────────
    with st.expander("🔥 **Step 1 — The Roast**", expanded=True):
        st.caption("AI-powered financial roast based on your actual spending.")

        col_text, col_btn = st.columns([3, 1])
        with col_text:
            if ai_data and ai_data.get("roast"):
                roast_text = ai_data.get("roast", "")
                st.markdown(
                    f"""
                    <div style="
                        background-color: #FEF2F2;
                        border-left: 4px solid #EF4444;
                        border-radius: 8px;
                        padding: 14px 18px;
                        margin-bottom: 12px;
                        color: #991B1B;
                        font-size: 1rem;
                        font-style: italic;
                        font-weight: 500;
                    ">
                        "{roast_text}"
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                evidence_items = ai_data.get("roast_evidence", [])
                if evidence_items:
                    st.markdown("**Why You Got Roasted (Supporting Evidence):**")
                    for item in evidence_items:
                        # Clean any dollar signs in item if present
                        item_clean = item.replace("$", "₹")
                        st.markdown(f"- {item_clean}")
                else:
                    top_cat = next(iter(factual.get("spending_by_category", {}).keys()), "Top Category")
                    top_pct = factual.get("category_percentages", {}).get(top_cat, 0.0)
                    disc_pct = heuristics.get("discretionary_spending_estimate", {}).get("percentage_of_total", 0.0)
                    st.markdown(f"- **Top Spending Area**: `{top_cat}` represents **{top_pct:.1f}%** of your total outflows.")
                    st.markdown(f"- **Discretionary Spending**: Estimated at **{disc_pct:.1f}%** of total budget.")
            else:
                st.info("Click **Generate Roast & Plan** to unlock your customized financial roast.")

        with col_btn:
            if st.button("🔥 Generate Roast & Plan", type="primary", use_container_width=True, key="btn_roast_step1"):
                if on_generate_click:
                    on_generate_click()

    # ── Step 2: WHAT IS ACTUALLY HAPPENING ───────────────────────────────────
    with st.expander("📊 **Step 2 — What Is Actually Happening**", expanded=False):
        st.caption("Root-cause diagnostic analysis of your spending patterns and anomalies.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ⚠️ Identified Spending Problems")
            problems = ai_data.get("spending_problems", []) if ai_data else []
            if problems:
                for prob in problems:
                    prob_clean = prob.replace("$", "₹")
                    st.markdown(
                        f"""
                        <div style="background-color: #FFFBEB; border-left: 3px solid #F59E0B; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; color: #92400E; font-size: 0.9rem;">
                            <b>Issue:</b> {prob_clean}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                top_3_pct = factual.get("spending_concentration", {}).get("top_3_categories_percentage", 0.0)
                disc_amt = heuristics.get("discretionary_spending_estimate", {}).get("amount", 0.0)
                st.markdown(f"- **Category Dominance**: Top 3 categories consume **{top_3_pct:.1f}%** of total budget.")
                if disc_amt > 0:
                    st.markdown(f"- **Discretionary Outflows**: **{format_inr(disc_amt)}** spent across non-essential categories.")

        with col2:
            st.markdown("#### ⚡ Unusual Spending Observations")
            anomalies = heuristics.get("unusual_spending_observations", [])
            if anomalies:
                for a in anomalies[:4]:
                    amt_str = format_inr(a.get("amount", 0))
                    reason_clean = a.get("reason", "").replace("$", "₹")
                    st.markdown(
                        f"""
                        <div style="background-color: #EFF6FF; border-left: 3px solid #3B82F6; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; color: #1E40AF; font-size: 0.9rem;">
                            <b>{amt_str}</b> at <code>{a.get('description', '')}</code> ({a.get('category', '')})<br>
                            <span style="font-size: 0.8rem; color: #3B82F6;">{reason_clean}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No statistical anomalies or unusual spikes detected.")

    # ── Step 3: WHERE YOUR MONEY IS GOING ────────────────────────────────────
    with st.expander("📊 **Step 3 — Where Your Money Is Going**", expanded=False):
        st.caption("Detailed breakdown, concentration, and category flow.")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("##### 🏷️ Category Share Breakdown")
            spending_by_cat = factual.get("spending_by_category", {})
            cat_pcts = factual.get("category_percentages", {})
            cat_df = pd.DataFrame(
                [
                    {
                        "Category": cat,
                        "Amount": format_inr(amt),
                        "Share": f"{cat_pcts.get(cat, 0.0):.1f}%",
                    }
                    for cat, amt in spending_by_cat.items()
                ]
            )
            st.dataframe(cat_df, use_container_width=True, hide_index=True)

        with col_c2:
            st.markdown("##### 🎯 Spending Concentration")
            conc = factual.get("spending_concentration", {})
            top3_pct = conc.get("top_3_categories_percentage", 0.0)
            pareto_pct = conc.get("top_20_percent_transactions_percentage", 0.0)

            st.markdown(f"- **Top 3 Categories**: **{top3_pct:.1f}%** of total expenditures.")
            st.markdown(f"- **Pareto Rule (Top 20% Txns)**: Accounts for **{pareto_pct:.1f}%** of total spend.")

            largest = factual.get("largest_expenses", [])
            if largest:
                st.markdown(f"- **Single Largest Outflow**: **{format_inr(largest[0].get('amount', 0))}** (`{largest[0].get('description', '')}`)")

    # ── Step 4: WHAT YOU CAN RECOVER ─────────────────────────────────────────
    with st.expander("💰 **Step 4 — What You Can Recover**", expanded=False):
        st.caption("Quantified savings opportunities and detected commitments.")

        savings_list = heuristics.get("potential_savings_opportunities", [])
        total_potential_savings = sum(
            s.get("potential_monthly_impact") or 0.0 for s in savings_list
        )
        yearly_potential_savings = total_potential_savings * 12

        rec_col1, rec_col2 = st.columns([1, 2])
        with rec_col1:
            st.markdown(
                f"""
                <div style="background-color: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 10px; padding: 16px; text-align: center;">
                    <div style="font-size: 0.8rem; font-weight: 600; color: #065F46; text-transform: uppercase;">Estimated Monthly Recovery</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #059669; margin: 6px 0;">{format_inr(total_potential_savings)}/mo</div>
                    <div style="font-size: 0.8rem; color: #047857; font-weight: 500;">+{format_inr(yearly_potential_savings)}/yr potential</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("*Based on deterministic heuristics and detected commitments.*")

        with rec_col2:
            recurring = heuristics.get("recurring_expenses", [])
            if recurring:
                st.markdown("##### 🔁 Recurring Commitments Audit")
                rec_df = pd.DataFrame(
                    [
                        {
                            "Service / Merchant": r.get("description"),
                            "Amount": format_inr(r.get("amount", 0)),
                            "Frequency": r.get("estimated_frequency"),
                            "Occurrences": r.get("occurrences"),
                            "Est. Annual Cost": format_inr(r.get("amount", 0) * (12 if r.get("estimated_frequency") == "Monthly" else r.get("occurrences", 1))),
                        }
                        for r in recurring
                    ]
                )
                st.dataframe(rec_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No recurring subscription patterns detected.")

    # ── Step 5: THE RECOVERY PLAN ────────────────────────────────────────────
    with st.expander("🛡️ **Step 5 — The Recovery Plan**", expanded=False):
        st.caption("Actionable, prioritized recommendations with estimated financial impact.")

        structured_plan = ai_data.get("structured_recovery_plan", []) if ai_data else []

        if structured_plan:
            for idx, item in enumerate(structured_plan, start=1):
                priority = item.get("priority", "Medium").capitalize()
                if priority == "High":
                    p_badge = '<span style="background-color: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">🔴 High Priority</span>'
                elif priority == "Medium":
                    p_badge = '<span style="background-color: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">🟡 Medium Priority</span>'
                else:
                    p_badge = '<span style="background-color: #D1FAE5; color: #065F46; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">🟢 Low Priority</span>'

                m_saving = item.get("estimated_monthly_saving")
                y_saving = item.get("estimated_yearly_saving")
                if m_saving and not y_saving:
                    y_saving = m_saving * 12

                action_clean = item.get("action", "").replace("$", "₹")
                problem_clean = item.get("problem", "").replace("$", "₹")

                col_h, col_s = st.columns([3, 1])
                with col_h:
                    st.markdown(f"**Step {idx}: {action_clean}** &nbsp; {p_badge}", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #64748B; font-size: 0.85rem;'>*Root Problem:* {problem_clean}</span>", unsafe_allow_html=True)
                with col_s:
                    if m_saving:
                        st.markdown(
                            f"""
                            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px; text-align: right;">
                                <div style="font-size: 0.7rem; color: #64748B;">Est. Monthly Saving</div>
                                <div style="font-size: 1rem; font-weight: 700; color: #059669;">+{format_inr(m_saving)}</div>
                                <div style="font-size: 0.68rem; color: #94A3B8;">+{format_inr(y_saving)}/yr *(est)*</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("Qualitative efficiency")
                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        elif ai_data and ai_data.get("recovery_plan"):
            for idx, step in enumerate(ai_data["recovery_plan"], 1):
                step_clean = step.replace("$", "₹")
                st.markdown(f"**{idx}.** {step_clean}")
        else:
            st.info("Click **Generate Roast & Plan** to produce your custom, prioritized recovery roadmap.")
