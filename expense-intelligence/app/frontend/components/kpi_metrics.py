"""
KPI metric card components for the AI Expense Intelligence dashboard.

Styled with modern light financial card styling, soft pastel accents, and INR currency formatting.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.frontend.utils.currency import format_inr


def render_kpi_cards(factual: dict[str, Any], heuristics: dict[str, Any]) -> None:
    """
    Render 5 horizontally aligned modern light KPI cards based strictly on backend calculations.
    """
    total_spending = factual.get("total_spending", 0.0)
    avg_txn = factual.get("average_transaction", 0.0)
    txn_count = factual.get("transaction_count", 0)
    median_txn = factual.get("median_transaction", 0.0)
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

    kpi_cards_data = [
        {
            "label": "Total Spending",
            "value": format_inr(total_spending),
            "subtext": f"{txn_count} transactions",
            "icon": "💳",
            "accent_bg": "#EEF2FF",
            "accent_border": "#C7D2FE",
            "accent_color": "#4F46E5",
        },
        {
            "label": "Avg. Transaction",
            "value": format_inr(avg_txn),
            "subtext": f"Median {format_inr(median_txn)}",
            "icon": "📊",
            "accent_bg": "#F0F9FF",
            "accent_border": "#BAE6FD",
            "accent_color": "#0284C7",
        },
        {
            "label": "Top Category",
            "value": top_cat_name,
            "subtext": f"{top_cat_pct:.1f}% ({format_inr(top_cat_amount)})",
            "icon": "🏷️",
            "accent_bg": "#FEF3C7",
            "accent_border": "#FDE68A",
            "accent_color": "#D97706",
        },
        {
            "label": "Discretionary Spend",
            "value": format_inr(disc_amount),
            "subtext": f"{disc_pct:.1f}% of total outflow",
            "icon": "🛍️",
            "accent_bg": "#FDF2F8",
            "accent_border": "#FBCFE8",
            "accent_color": "#DB2777",
        },
        {
            "label": "Potential Savings",
            "value": format_inr(total_potential_savings),
            "subtext": f"{len(savings_list)} opportunities flagged",
            "icon": "💡",
            "accent_bg": "#ECFDF5",
            "accent_border": "#A7F3D0",
            "accent_color": "#059669",
        },
    ]

    cols = st.columns(5)
    for idx, card in enumerate(kpi_cards_data):
        with cols[idx]:
            card_html = f"""
            <div style="
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-top: 3px solid {card['accent_color']};
                border-radius: 12px;
                padding: 16px 14px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: #64748B;">
                        {card['label']}
                    </span>
                    <span style="font-size: 1rem; background-color: {card['accent_bg']}; padding: 4px 6px; border-radius: 6px;">
                        {card['icon']}
                    </span>
                </div>
                <div style="font-size: 1.35rem; font-weight: 700; color: #0F172A; margin-bottom: 4px; word-break: break-word;">
                    {card['value']}
                </div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 500;">
                    {card['subtext']}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
