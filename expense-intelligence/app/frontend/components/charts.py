"""
Plotly chart components for the AI Expense Intelligence dashboard.

Styled with a crisp light theme, soft pastel palettes, and strict INR (₹) formatting.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.frontend.utils.currency import format_inr

# Modern, accessible curated pastel-accent palette
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


def _apply_light_theme(fig: go.Figure, title_text: str, height: int = 340) -> None:
    """Apply consistent light-theme styling to Plotly figures."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(size=14, color="#0F172A", family="sans-serif"),
            x=0.02,
            y=0.95,
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#64748B", size=12, family="sans-serif"),
        margin=dict(t=45, b=25, l=20, r=20),
        height=height,
    )


def render_category_chart(
    spending_by_category: dict[str, float],
    category_percentages: dict[str, float],
) -> None:
    """Render an interactive Donut chart showing spending breakdown by category in INR."""
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
                hole=0.6,
                marker=dict(
                    colors=PALETTE[: len(labels)],
                    line=dict(color="#FFFFFF", width=2),
                ),
                textinfo="percent",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )

    _apply_light_theme(fig, "Spending by Category")
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#64748B"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_trend_chart(
    daily_spending: list[dict[str, Any]],
    monthly_spending: list[dict[str, Any]],
) -> None:
    """Render a time series trend chart of spending over time in INR."""
    if not daily_spending:
        st.info("No timeline data available.")
        return

    df_daily = pd.DataFrame(daily_spending)
    df_daily["date"] = pd.to_datetime(df_daily["date"])
    df_daily = df_daily.sort_values("date")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_daily["date"],
            y=df_daily["amount"],
            mode="lines+markers",
            name="Daily Spend",
            line=dict(color="#6366F1", width=2.5, shape="spline"),
            marker=dict(size=6, color="#6366F1", line=dict(color="#FFFFFF", width=1.5)),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.08)",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Spend: ₹%{y:,.2f}<extra></extra>",
        )
    )

    _apply_light_theme(fig, "Spending Timeline")
    fig.update_layout(
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Amount (₹)",
            showgrid=True,
            gridcolor="#F1F5F9",
            tickprefix="₹",
            zeroline=False,
            tickfont=dict(size=10),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_discretionary_chart(
    total_spending: float,
    discretionary_amount: float,
) -> None:
    """Render a comparative Donut chart for Discretionary vs. Essential spending in INR."""
    if total_spending <= 0:
        st.info("No spending data available.")
        return

    essential_amount = max(0.0, total_spending - discretionary_amount)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Essential", "Discretionary"],
                values=[essential_amount, discretionary_amount],
                hole=0.65,
                marker=dict(
                    colors=["#10B981", "#F43F5E"],
                    line=dict(color="#FFFFFF", width=2),
                ),
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )

    _apply_light_theme(fig, "Essential vs. Discretionary")
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#64748B"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_expenses_chart(largest_expenses: list[dict[str, Any]]) -> None:
    """Render a horizontal bar chart ranking top individual transactions in INR."""
    if not largest_expenses:
        st.info("No transaction data available.")
        return

    # Take top 5 for visual clarity
    top_5 = largest_expenses[:5][::-1]  # reverse so highest is on top
    descriptions = [
        f"{e.get('description', 'Expense')}" for e in top_5
    ]
    amounts = [e.get("amount", 0.0) for e in top_5]

    fig = go.Figure(
        data=[
            go.Bar(
                x=amounts,
                y=descriptions,
                orientation="h",
                marker=dict(color="#3B82F6", opacity=0.85, cornerradius=4),
                text=[format_inr(amt) for amt in amounts],
                textposition="auto",
                textfont=dict(color="#FFFFFF", size=10),
                hovertemplate="<b>%{y}</b><br>Amount: ₹%{x:,.2f}<extra></extra>",
            )
        ]
    )

    _apply_light_theme(fig, "Top Largest Expenses")
    fig.update_layout(
        xaxis=dict(
            title="",
            tickprefix="₹",
            showgrid=True,
            gridcolor="#F1F5F9",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            autorange=True,
            tickfont=dict(size=11, color="#0F172A"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
