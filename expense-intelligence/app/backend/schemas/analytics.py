"""
Pydantic schemas for deterministic expense analytics.

Strictly delineates FACTUAL METRICS from HEURISTIC INSIGHTS.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.backend.schemas.common import BaseSchema
from app.backend.schemas.expense import NormalizedExpense


# ── Factual Metrics Schemas ───────────────────────────────────────────────────


class DailyAggregate(BaseSchema):
    """Aggregate spending for a single calendar day."""

    date: str = Field(description="ISO date (YYYY-MM-DD)")
    amount: float = Field(description="Total spending on this day")
    transaction_count: int = Field(description="Number of transactions on this day")


class WeeklyAggregate(BaseSchema):
    """Aggregate spending for a 7-day period starting on week_start."""

    week_start: str = Field(description="Start date of the week (YYYY-MM-DD)")
    amount: float = Field(description="Total spending in this week")
    transaction_count: int = Field(description="Number of transactions in this week")


class MonthlyAggregate(BaseSchema):
    """Aggregate spending for a calendar month."""

    month: str = Field(description="Calendar month identifier (YYYY-MM)")
    amount: float = Field(description="Total spending in this month")
    transaction_count: int = Field(description="Number of transactions in this month")


class SpendingConcentration(BaseSchema):
    """Factual concentration measurements of total spending."""

    top_3_categories_percentage: float = Field(
        description="Percentage of total spending consumed by the top 3 categories"
    )
    top_20_percent_transactions_percentage: float = Field(
        description="Percentage of total spending accounted for by the largest 20% of transactions (Pareto ratio)"
    )


class FactualMetrics(BaseSchema):
    """Strictly factual, mathematical calculations derived directly from the data."""

    total_spending: float = Field(description="Total sum of all transaction amounts")
    transaction_count: int = Field(description="Total number of valid transactions")
    average_transaction: float = Field(description="Mean transaction amount")
    median_transaction: float = Field(description="Median transaction amount")
    min_transaction: float = Field(description="Smallest transaction amount")
    max_transaction: float = Field(description="Largest transaction amount")
    spending_by_category: dict[str, float] = Field(
        description="Total spending aggregated by category"
    )
    category_percentages: dict[str, float] = Field(
        description="Percentage breakdown of total spending by category"
    )
    daily_spending: list[DailyAggregate] = Field(
        description="Time series of daily spending aggregates"
    )
    weekly_spending: list[WeeklyAggregate] = Field(
        description="Time series of weekly spending aggregates"
    )
    monthly_spending: list[MonthlyAggregate] = Field(
        description="Time series of monthly spending aggregates"
    )
    largest_expenses: list[NormalizedExpense] = Field(
        description="Top N largest individual transactions"
    )
    spending_concentration: SpendingConcentration = Field(
        description="Concentration and distribution metrics"
    )


# ── Heuristic Insights Schemas ────────────────────────────────────────────────


class RecurringExpenseCandidate(BaseSchema):
    """A recurring expense pattern identified via deterministic rule matching."""

    description: str = Field(description="Normalized merchant or charge description")
    amount: float = Field(description="Characteristic recurring transaction amount")
    occurrences: int = Field(description="Total number of matching occurrences")
    estimated_frequency: str = Field(
        description="Estimated cadence (e.g., 'Monthly', 'Weekly', 'Periodic')"
    )
    confidence_note: str = Field(
        description="Neutral explanatory note detailing how the pattern was identified"
    )


class DiscretionaryEstimate(BaseSchema):
    """Heuristic estimate of discretionary vs. essential spending."""

    amount: float = Field(description="Estimated total discretionary expenditure")
    percentage_of_total: float = Field(
        description="Discretionary spending as a percentage of total spend"
    )
    discretionary_categories: list[str] = Field(
        description="Categories classified as discretionary under standard budgeting heuristics"
    )
    heuristic_explanation: str = Field(
        description="Neutral disclosure explaining the rule-based classification methodology"
    )


class UnusualExpenseObservation(BaseSchema):
    """A statistical outlier or disproportionate transaction flagged for user review."""

    date: str = Field(description="Date of the transaction")
    description: str = Field(description="Transaction description")
    amount: float = Field(description="Transaction amount")
    category: str = Field(description="Transaction category")
    reason: str = Field(description="Statistical or rule-based reason for flagging")


class SavingsOpportunity(BaseSchema):
    """Rule-based observation identifying potential areas for spending reduction."""

    title: str = Field(description="Short title of the observation")
    category: str | None = Field(
        default=None, description="Relevant category if applicable"
    )
    potential_monthly_impact: float | None = Field(
        default=None, description="Estimated monthly dollar amount involved"
    )
    observation: str = Field(
        description="Objective, non-judgmental observation based purely on data patterns"
    )


class HeuristicInsights(BaseSchema):
    """Rule-based, heuristic insights clearly distinguished from factual metrics."""

    recurring_expenses: list[RecurringExpenseCandidate] = Field(
        description="Identified recurring payment candidates"
    )
    discretionary_spending_estimate: DiscretionaryEstimate = Field(
        description="Rule-based discretionary spending estimate"
    )
    top_discretionary_categories: list[str] = Field(
        description="Top discretionary categories ranked by total expenditure"
    )
    unusual_spending_observations: list[UnusualExpenseObservation] = Field(
        description="Statistically unusual transactions or category spikes"
    )
    potential_savings_opportunities: list[SavingsOpportunity] = Field(
        description="Rule-based spending reduction observations"
    )


# ── Top-Level Analysis Request & Report ───────────────────────────────────────


class ExpenseAnalysisRequest(BaseModel):
    """Payload sent to the analytics endpoint."""

    expenses: list[NormalizedExpense] = Field(
        description="List of normalized expense items to analyze"
    )


class ExpenseAnalyticsReport(BaseModel):
    """Complete structured analytics report."""

    factual_metrics: FactualMetrics = Field(
        description="Deterministic, factual mathematical calculations"
    )
    heuristic_insights: HeuristicInsights = Field(
        description="Rule-based heuristic insights and observations"
    )
