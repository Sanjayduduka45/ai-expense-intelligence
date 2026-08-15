"""
Deterministic expense analytics engine using Pandas and NumPy.

Calculates reliable financial insights with strict separation between
FACTUAL METRICS and HEURISTIC INSIGHTS.
"""

from __future__ import annotations

import math
import re
from typing import Any

import numpy as np
import pandas as pd

from app.backend.schemas.analytics import (
    DailyAggregate,
    DiscretionaryEstimate,
    ExpenseAnalyticsReport,
    FactualMetrics,
    HeuristicInsights,
    MonthlyAggregate,
    RecurringExpenseCandidate,
    SavingsOpportunity,
    SpendingConcentration,
    UnusualExpenseObservation,
    WeeklyAggregate,
)
from app.backend.schemas.expense import NormalizedExpense

# Heuristic category classification for discretionary spend estimates
DISCRETIONARY_CATEGORIES: frozenset[str] = frozenset(
    {
        "entertainment",
        "shopping",
        "food & dining",
        "food and dining",
        "dining",
        "restaurants",
        "coffee",
        "travel",
        "leisure",
        "subscriptions",
        "hobbies",
        "personal care",
        "electronics",
        "bars",
        "clothing",
    }
)


class ExpenseAnalyticsService:
    """Service performing deterministic mathematical and heuristic financial analysis."""

    def analyze(self, expenses: list[NormalizedExpense]) -> ExpenseAnalyticsReport:
        """
        Analyze a list of normalized expense records.
        
        Guarantees deterministic, reproducible results with neutral phrasing.
        """
        if not expenses:
            return self._build_empty_report()

        df = self._to_dataframe(expenses)

        # 1. Compute Factual Metrics
        factual = self._compute_factual_metrics(df, expenses)

        # 2. Compute Heuristic Insights
        heuristics = self._compute_heuristic_insights(df, factual)

        return ExpenseAnalyticsReport(
            factual_metrics=factual,
            heuristic_insights=heuristics,
        )

    def _to_dataframe(self, expenses: list[NormalizedExpense]) -> pd.DataFrame:
        """Convert expense models to an optimized Pandas DataFrame."""
        records = [
            {
                "date": pd.to_datetime(e.date),
                "date_str": e.date,
                "description": e.description,
                "category": e.category or "Other",
                "amount": float(e.amount),
            }
            for e in expenses
        ]
        df = pd.DataFrame(records)
        df = df.sort_values(by=["date", "amount"], ascending=[True, False]).reset_index(
            drop=True
        )
        return df

    def _compute_factual_metrics(
        self, df: pd.DataFrame, original_expenses: list[NormalizedExpense]
    ) -> FactualMetrics:
        """Calculate strictly factual mathematical aggregations."""
        amounts = df["amount"].to_numpy()
        total_spending = round(float(np.sum(amounts)), 2)
        transaction_count = len(amounts)
        avg_transaction = round(float(np.mean(amounts)), 2)
        median_transaction = round(float(np.median(amounts)), 2)
        min_transaction = round(float(np.min(amounts)), 2)
        max_transaction = round(float(np.max(amounts)), 2)

        # Category spending & percentages
        cat_grouped = (
            df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )
        spending_by_category = {k: round(float(v), 2) for k, v in cat_grouped.items()}

        if total_spending > 0:
            category_percentages = {
                k: round((v / total_spending) * 100, 2)
                for k, v in spending_by_category.items()
            }
        else:
            category_percentages = {k: 0.0 for k in spending_by_category}

        # Daily spending
        daily_df = (
            df.groupby("date_str")
            .agg(amount=("amount", "sum"), count=("amount", "count"))
            .reset_index()
            .sort_values("date_str")
        )
        daily_spending = [
            DailyAggregate(
                date=row["date_str"],
                amount=round(float(row["amount"]), 2),
                transaction_count=int(row["count"]),
            )
            for _, row in daily_df.iterrows()
        ]

        # Weekly spending (grouped by start of week Monday)
        df["week_start"] = (
            df["date"].dt.to_period("W-SUN").apply(lambda r: r.start_time.strftime("%Y-%m-%d"))
        )
        weekly_df = (
            df.groupby("week_start")
            .agg(amount=("amount", "sum"), count=("amount", "count"))
            .reset_index()
            .sort_values("week_start")
        )
        weekly_spending = [
            WeeklyAggregate(
                week_start=row["week_start"],
                amount=round(float(row["amount"]), 2),
                transaction_count=int(row["count"]),
            )
            for _, row in weekly_df.iterrows()
        ]

        # Monthly spending
        df["month"] = df["date"].dt.strftime("%Y-%m")
        monthly_df = (
            df.groupby("month")
            .agg(amount=("amount", "sum"), count=("amount", "count"))
            .reset_index()
            .sort_values("month")
        )
        monthly_spending = [
            MonthlyAggregate(
                month=row["month"],
                amount=round(float(row["amount"]), 2),
                transaction_count=int(row["count"]),
            )
            for _, row in monthly_df.iterrows()
        ]

        # Largest expenses (Top 10)
        sorted_expenses = sorted(
            original_expenses, key=lambda e: (e.amount, e.date), reverse=True
        )
        largest_expenses = sorted_expenses[:10]

        # Spending concentration
        top_3_sum = sum(list(spending_by_category.values())[:3])
        top_3_pct = (
            round((top_3_sum / total_spending) * 100, 2) if total_spending > 0 else 0.0
        )

        # Pareto 20% transactions concentration
        top_20_count = max(1, math.ceil(0.2 * transaction_count))
        sorted_amounts = np.sort(amounts)[::-1]
        top_20_sum = float(np.sum(sorted_amounts[:top_20_count]))
        top_20_pct = (
            round((top_20_sum / total_spending) * 100, 2) if total_spending > 0 else 0.0
        )

        spending_concentration = SpendingConcentration(
            top_3_categories_percentage=top_3_pct,
            top_20_percent_transactions_percentage=top_20_pct,
        )

        return FactualMetrics(
            total_spending=total_spending,
            transaction_count=transaction_count,
            average_transaction=avg_transaction,
            median_transaction=median_transaction,
            min_transaction=min_transaction,
            max_transaction=max_transaction,
            spending_by_category=spending_by_category,
            category_percentages=category_percentages,
            daily_spending=daily_spending,
            weekly_spending=weekly_spending,
            monthly_spending=monthly_spending,
            largest_expenses=largest_expenses,
            spending_concentration=spending_concentration,
        )

    def _compute_heuristic_insights(
        self, df: pd.DataFrame, factual: FactualMetrics
    ) -> HeuristicInsights:
        """Compute rule-based heuristic insights with neutral framing."""
        # 1. Identify recurring candidates
        recurring = self._detect_recurring_expenses(df)

        # 2. Estimate discretionary spending
        discretionary, top_disc_cats = self._estimate_discretionary(df, factual.total_spending)

        # 3. Detect unusual spending observations (outliers)
        unusual = self._detect_unusual_expenses(df)

        # 4. Identify potential savings opportunities (rule-based)
        savings = self._identify_savings_opportunities(
            factual, recurring, discretionary, top_disc_cats
        )

        return HeuristicInsights(
            recurring_expenses=recurring,
            discretionary_spending_estimate=discretionary,
            top_discretionary_categories=top_disc_cats,
            unusual_spending_observations=unusual,
            potential_savings_opportunities=savings,
        )

    def _detect_recurring_expenses(
        self, df: pd.DataFrame
    ) -> list[RecurringExpenseCandidate]:
        """Heuristic detection of repetitive merchant and amount occurrences."""
        candidates: list[RecurringExpenseCandidate] = []

        # Normalize descriptions for grouping
        df["norm_desc"] = (
            df["description"]
            .str.lower()
            .apply(lambda s: re.sub(r"[^a-z0-9]", " ", s).strip())
        )

        grouped = df.groupby(["norm_desc", "amount"])

        for (desc_key, amount), group in grouped:
            count = len(group)
            if count >= 2:
                sorted_dates = group["date"].sort_values().tolist()
                intervals = [
                    (sorted_dates[i] - sorted_dates[i - 1]).days
                    for i in range(1, len(sorted_dates))
                ]
                avg_interval = np.mean(intervals) if intervals else 0

                if 25 <= avg_interval <= 35:
                    freq = "Monthly"
                elif 6 <= avg_interval <= 8:
                    freq = "Weekly"
                else:
                    freq = "Periodic"

                orig_desc = group["description"].iloc[0]
                candidates.append(
                    RecurringExpenseCandidate(
                        description=orig_desc,
                        amount=round(float(amount), 2),
                        occurrences=count,
                        estimated_frequency=freq,
                        confidence_note=(
                            f"Observed {count} occurrences of '{orig_desc}' with matching amount (${amount:.2f}) "
                            f"(average interval of {avg_interval:.0f} days)."
                        ),
                    )
                )

        # Sort by total recurring impact (amount * occurrences)
        candidates.sort(key=lambda c: c.amount * c.occurrences, reverse=True)
        return candidates

    def _estimate_discretionary(
        self, df: pd.DataFrame, total_spending: float
    ) -> tuple[DiscretionaryEstimate, list[str]]:
        """Classify spending categories into discretionary vs essential based on standard rules."""
        # Find matching discretionary rows
        df["is_discretionary"] = df["category"].str.lower().isin(DISCRETIONARY_CATEGORIES)
        disc_df = df[df["is_discretionary"]]

        disc_total = round(float(disc_df["amount"].sum()), 2)
        disc_pct = (
            round((disc_total / total_spending) * 100, 2) if total_spending > 0 else 0.0
        )

        disc_by_cat = (
            disc_df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )
        top_disc_cats = list(disc_by_cat.index)

        estimate = DiscretionaryEstimate(
            amount=disc_total,
            percentage_of_total=disc_pct,
            discretionary_categories=top_disc_cats,
            heuristic_explanation=(
                "Estimated based on standard budgetary taxonomy where categories such as "
                "Dining, Entertainment, Shopping, Travel, and Subscriptions are classified as non-essential."
            ),
        )
        return estimate, top_disc_cats

    def _detect_unusual_expenses(
        self, df: pd.DataFrame
    ) -> list[UnusualExpenseObservation]:
        """Detect statistically unusual transactions using IQR and category proportions."""
        observations: list[UnusualExpenseObservation] = []
        n = len(df)
        if n < 4:
            return observations

        # 1. Global IQR Outliers
        q25, q75 = np.percentile(df["amount"], [25, 75])
        iqr = q75 - q25
        upper_threshold = q75 + 1.5 * iqr

        outliers = df[df["amount"] > upper_threshold]
        for _, row in outliers.iterrows():
            observations.append(
                UnusualExpenseObservation(
                    date=row["date_str"],
                    description=row["description"],
                    amount=round(float(row["amount"]), 2),
                    category=row["category"],
                    reason=(
                        f"Amount (${row['amount']:.2f}) exceeds dataset statistical upper fence "
                        f"(Q3 + 1.5*IQR = ${upper_threshold:.2f})."
                    ),
                )
            )

        # 2. Category Dominance (single transaction >= 50% of category total with >=3 txns in category)
        for cat, cat_group in df.groupby("category"):
            if len(cat_group) >= 3:
                cat_sum = cat_group["amount"].sum()
                for _, row in cat_group.iterrows():
                    share = row["amount"] / cat_sum
                    if share >= 0.50 and row["amount"] not in [o.amount for o in observations]:
                        observations.append(
                            UnusualExpenseObservation(
                                date=row["date_str"],
                                description=row["description"],
                                amount=round(float(row["amount"]), 2),
                                category=cat,
                                reason=(
                                    f"Single transaction constitutes {share * 100:.1f}% of total "
                                    f"'{cat}' category expenditure (${cat_sum:.2f})."
                                ),
                            )
                        )

        # Sort observations by amount descending
        observations.sort(key=lambda o: o.amount, reverse=True)
        return observations

    def _identify_savings_opportunities(
        self,
        factual: FactualMetrics,
        recurring: list[RecurringExpenseCandidate],
        discretionary: DiscretionaryEstimate,
        top_disc_cats: list[str],
    ) -> list[SavingsOpportunity]:
        """Rule-based observations for potential spending optimization."""
        opportunities: list[SavingsOpportunity] = []

        # 1. Recurring Subscriptions
        if recurring:
            recurring_sum = sum(c.amount for c in recurring)
            opportunities.append(
                SavingsOpportunity(
                    title="Identified Recurring Commitments",
                    category="Subscriptions / Recurring",
                    potential_monthly_impact=round(recurring_sum, 2),
                    observation=(
                        f"Detected {len(recurring)} recurring items totaling ${recurring_sum:.2f} "
                        f"per cycle. Reviewing active subscriptions may reveal unused services."
                    ),
                )
            )

        # 2. Discretionary Spending Volume
        if discretionary.percentage_of_total > 25.0:
            opportunities.append(
                SavingsOpportunity(
                    title="Discretionary Expense Volume",
                    category=top_disc_cats[0] if top_disc_cats else "Discretionary",
                    potential_monthly_impact=round(discretionary.amount * 0.15, 2),
                    observation=(
                        f"Discretionary spending represents {discretionary.percentage_of_total:.1f}% "
                        f"(${discretionary.amount:.2f}) of total expenditures. A modest 15% adjustment "
                        f"could preserve approximately ${discretionary.amount * 0.15:.2f}."
                    ),
                )
            )

        # 3. Concentration in Single Top Category
        if factual.spending_by_category:
            top_cat, top_spend = next(iter(factual.spending_by_category.items()))
            top_pct = factual.category_percentages.get(top_cat, 0.0)
            if top_pct > 40.0:
                opportunities.append(
                    SavingsOpportunity(
                        title=f"High Spending Concentration in '{top_cat}'",
                        category=top_cat,
                        potential_monthly_impact=round(top_spend * 0.10, 2),
                        observation=(
                            f"The '{top_cat}' category accounts for {top_pct:.1f}% (${top_spend:.2f}) "
                            f"of all tracked expenses. Focused budgeting in this area provides the largest leverage."
                        ),
                    )
                )

        return opportunities

    def _build_empty_report(self) -> ExpenseAnalyticsReport:
        """Return a neutral empty report when no data is provided."""
        factual = FactualMetrics(
            total_spending=0.0,
            transaction_count=0,
            average_transaction=0.0,
            median_transaction=0.0,
            min_transaction=0.0,
            max_transaction=0.0,
            spending_by_category={},
            category_percentages={},
            daily_spending=[],
            weekly_spending=[],
            monthly_spending=[],
            largest_expenses=[],
            spending_concentration=SpendingConcentration(
                top_3_categories_percentage=0.0,
                top_20_percent_transactions_percentage=0.0,
            ),
        )
        heuristics = HeuristicInsights(
            recurring_expenses=[],
            discretionary_spending_estimate=DiscretionaryEstimate(
                amount=0.0,
                percentage_of_total=0.0,
                discretionary_categories=[],
                heuristic_explanation="No transactions available to evaluate.",
            ),
            top_discretionary_categories=[],
            unusual_spending_observations=[],
            potential_savings_opportunities=[],
        )
        return ExpenseAnalyticsReport(
            factual_metrics=factual,
            heuristic_insights=heuristics,
        )


# Default singleton instance
analytics_service = ExpenseAnalyticsService()
