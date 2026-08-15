"""
KPI metric card components for the AI Expense Intelligence dashboard.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_kpi_cards(factual: dict[str, Any], heuristics: dict[str, Any]) -> None:
    """
    Render 5 clean, consistent KPI metric cards based strictly on backend calculations.
    """
    total_spending = factual.get("total_spending", 0.0)
    avg_txn = factual.get("average_transaction", 0.0)
    spending_by_cat = factual.get("spending_by_category", {})
    cat_pcts = factual.get("category_percentages", {})

    # Top category
    if spending_by_cat:
        top_cat_name = next(iter(spending_by_cat.keys()))
        top_cat_amount = spending_by_cat[top_cat_name]
        top_cat_pct = cat_pcts.get(top_cat_name, 0.0)
    else:
        top_cat_name = "N/A"
        top_cat_amount = 0.0
        top_cat_pct = 0.0

    # Discretionary spend
    disc = heuristics.get("discretionary_spending_estimate", {})
    disc_amount = disc.get("amount", 0.0)
    disc_pct = disc.get("percentage_of_total", 0.0)

    # Potential savings
    savings_list = heuristics.get("potential_savings_opportunities", [])
    total_potential_savings = sum(
        s.get("potential_monthly_impact") or 0.0 for s in savings_list
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Spending",
            value=f"${total_spending:,.2f}",
            help="Total sum of all valid transactions parsed.",
        )
        st.caption(f"{factual.get('transaction_count', 0)} transactions")

    with col2:
        st.metric(
            label="Avg. Transaction",
            value=f"${avg_txn:,.2f}",
            help="Mean expenditure per transaction.",
        )
        st.caption(f"Median: ${factual.get('median_transaction', 0.0):,.2f}")

    with col3:
        st.metric(
            label="Top Category",
            value=top_cat_name,
            delta=f"{top_cat_pct:.1f}% share",
            delta_color="off",
            help="Category with the highest aggregate expenditure.",
        )
        st.caption(f"${top_cat_amount:,.2f}")

    with col4:
        st.metric(
            label="Discretionary Spend",
            value=f"${disc_amount:,.2f}",
            delta=f"{disc_pct:.1f}% of total",
            delta_color="inverse",
            help="Estimated non-essential expenditure (dining, shopping, leisure).",
        )
        st.caption("Rule-based classification")

    with col5:
        st.metric(
            label="Potential Savings",
            value=f"${total_potential_savings:,.2f}",
            delta=f"{len(savings_list)} opportunities" if savings_list else "0 opportunities",
            delta_color="normal",
            help="Calculated potential savings across recurring and discretionary items.",
        )
        st.caption("Identified targets")
