"""
Plotly chart components for the AI Expense Intelligence dashboard.

Generates clean, informative visualizations with responsive layouts and curated palettes.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Modern, accessible curated color palette
PALETTE = [
    "#6366F1",  # Indigo
    "#EC4899",  # Pink
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#3B82F6",  # Blue
    "#8B5CF6",  # Violet
    "#14B8A6",  # Teal
    "#F97316",  # Orange
    "#64748B",  # Slate
]


def render_category_chart(
    spending_by_category: dict[str, float],
    category_percentages: dict[str, float],
) -> None:
    """Render an interactive Donut chart showing spending breakdown by category."""
    if not spending_by_category:
        st.info("No category data available.")
        return

    labels = list(spending_by_category.keys())
    values = list(spending_by_category.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=PALETTE[: len(labels)]),
                textinfo="label+percent",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>Total: $%{value:,.2f}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=dict(text="<b>Spending by Category</b>", font=dict(size=16)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=40, b=40, l=20, r=20),
        height=380,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_trend_chart(
    daily_spending: list[dict[str, Any]],
    monthly_spending: list[dict[str, Any]],
) -> None:
    """Render a time series trend chart of spending over time."""
    if not daily_spending:
        st.info("No timeline data available.")
        return

    df_daily = pd.DataFrame(daily_spending)
    df_daily["date"] = pd.to_datetime(df_daily["date"])
    df_daily = df_daily.sort_values("date")

    fig = go.Figure()

    # Daily Area Curve
    fig.add_trace(
        go.Scatter(
            x=df_daily["date"],
            y=df_daily["amount"],
            mode="lines+markers",
            name="Daily Spend",
            line=dict(color="#6366F1", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.12)",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Spend: $%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="<b>Spending Timeline</b>", font=dict(size=16)),
        xaxis=dict(title="Date", showgrid=True, gridcolor="rgba(150, 150, 150, 0.15)"),
        yaxis=dict(
            title="Amount ($)",
            showgrid=True,
            gridcolor="rgba(150, 150, 150, 0.15)",
            tickprefix="$",
        ),
        margin=dict(t=40, b=20, l=20, r=20),
        height=380,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_discretionary_chart(
    total_spending: float,
    discretionary_amount: float,
) -> None:
    """Render a comparative Donut chart for Discretionary vs. Essential spending."""
    if total_spending <= 0:
        st.info("No spending data available.")
        return

    essential_amount = max(0.0, total_spending - discretionary_amount)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Essential", "Discretionary"],
                values=[essential_amount, discretionary_amount],
                hole=0.6,
                marker=dict(colors=["#10B981", "#EC4899"]),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=dict(text="<b>Discretionary vs. Essential</b>", font=dict(size=16)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=40, b=40, l=20, r=20),
        height=380,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_expenses_chart(largest_expenses: list[dict[str, Any]]) -> None:
    """Render a horizontal bar chart ranking the top 5 largest individual transactions."""
    if not largest_expenses:
        st.info("No transaction data available.")
        return

    # Take top 5 for visual clarity
    top_5 = largest_expenses[:5][::-1]  # reverse so highest is on top
    descriptions = [
        f"{e.get('description', 'Expense')} ({e.get('category', 'Other')})" for e in top_5
    ]
    amounts = [e.get("amount", 0.0) for e in top_5]

    fig = go.Figure(
        data=[
            go.Bar(
                x=amounts,
                y=descriptions,
                orientation="h",
                marker=dict(color="#3B82F6", opacity=0.85),
                text=[f"${amt:,.2f}" for amt in amounts],
                textposition="auto",
                hovertemplate="<b>%{y}</b><br>Amount: $%{x:,.2f}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=dict(text="<b>Top Largest Expenses</b>", font=dict(size=16)),
        xaxis=dict(title="Amount ($)", tickprefix="$", showgrid=True),
        yaxis=dict(autorange=True),
        margin=dict(t=40, b=20, l=20, r=20),
        height=380,
    )

    st.plotly_chart(fig, use_container_width=True)
