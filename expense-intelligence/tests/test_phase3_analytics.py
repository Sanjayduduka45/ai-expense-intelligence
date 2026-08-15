"""
Phase 3: Deterministic expense intelligence tests.

Tests:
1. Empty dataset handling.
2. Single transaction dataset.
3. Zero amounts / boundary numbers.
4. Duplicate records calculation.
5. Very large values (overflow & precision safety).
6. Missing categories handling (defaulting to 'Other').
7. Multiple months across daily/weekly/monthly time series aggregations.
8. Separation of FACTUAL METRICS vs HEURISTIC INSIGHTS.
9. Recurring expenses detection heuristic.
10. Discretionary spending estimate heuristic.
11. Statistical outlier & unusual spending detection heuristic.
12. API endpoint POST /api/v1/expenses/analyze.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.schemas.analytics import ExpenseAnalyticsReport
from app.backend.schemas.expense import NormalizedExpense
from app.backend.services.analytics_service import ExpenseAnalyticsService


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous test client for the FastAPI backend."""
    return TestClient(app)


@pytest.fixture
def analytics_service() -> ExpenseAnalyticsService:
    return ExpenseAnalyticsService()


class TestEdgeCases:
    """Edge cases: empty, single item, zero amounts, large numbers, missing categories."""

    def test_empty_dataset(self, analytics_service: ExpenseAnalyticsService) -> None:
        report = analytics_service.analyze([])
        assert isinstance(report, ExpenseAnalyticsReport)
        
        # Factual metrics must be zeroed safely without division by zero errors
        assert report.factual_metrics.total_spending == 0.0
        assert report.factual_metrics.transaction_count == 0
        assert report.factual_metrics.average_transaction == 0.0
        assert report.factual_metrics.median_transaction == 0.0
        assert report.factual_metrics.spending_by_category == {}
        assert report.factual_metrics.daily_spending == []
        assert report.factual_metrics.weekly_spending == []
        assert report.factual_metrics.monthly_spending == []
        assert report.factual_metrics.largest_expenses == []

        # Heuristic insights must be empty and safe
        assert report.heuristic_insights.recurring_expenses == []
        assert report.heuristic_insights.discretionary_spending_estimate.amount == 0.0
        assert report.heuristic_insights.unusual_spending_observations == []

    def test_single_transaction_dataset(
        self, analytics_service: ExpenseAnalyticsService
    ) -> None:
        expenses = [
            NormalizedExpense(
                date="2025-03-10",
                description="Groceries",
                category="Food & Dining",
                amount=54.20,
            )
        ]
        report = analytics_service.analyze(expenses)
        f = report.factual_metrics

        assert f.total_spending == 54.20
        assert f.transaction_count == 1
        assert f.average_transaction == 54.20
        assert f.median_transaction == 54.20
        assert f.min_transaction == 54.20
        assert f.max_transaction == 54.20
        assert f.spending_by_category == {"Food & Dining": 54.20}
        assert f.category_percentages == {"Food & Dining": 100.0}
        assert len(f.daily_spending) == 1
        assert len(f.monthly_spending) == 1
        assert f.monthly_spending[0].month == "2025-03"

    def test_zero_and_boundary_amounts(
        self, analytics_service: ExpenseAnalyticsService
    ) -> None:
        expenses = [
            NormalizedExpense(date="2025-01-01", description="A", category="Other", amount=0.01),
            NormalizedExpense(date="2025-01-02", description="B", category="Other", amount=0.02),
        ]
        report = analytics_service.analyze(expenses)
        assert report.factual_metrics.total_spending == 0.03
        assert report.factual_metrics.average_transaction in (0.01, 0.02)

    def test_duplicate_records(self, analytics_service: ExpenseAnalyticsService) -> None:
        """Duplicate records must be preserved and included in total financial calculations."""
        expenses = [
            NormalizedExpense(date="2025-01-15", description="Coffee", category="Dining", amount=5.00),
            NormalizedExpense(date="2025-01-15", description="Coffee", category="Dining", amount=5.00),
        ]
        report = analytics_service.analyze(expenses)
        assert report.factual_metrics.transaction_count == 2
        assert report.factual_metrics.total_spending == 10.00
        assert report.factual_metrics.spending_by_category == {"Dining": 10.00}

    def test_very_large_values(self, analytics_service: ExpenseAnalyticsService) -> None:
        """Precision and overflow safety for multi-million amounts."""
        expenses = [
            NormalizedExpense(
                date="2025-01-01",
                description="Commercial Property Purchase",
                category="Housing",
                amount=5_000_000.55,
            ),
            NormalizedExpense(
                date="2025-01-02",
                description="Equipment Investment",
                category="Business",
                amount=2_500_000.45,
            ),
        ]
        report = analytics_service.analyze(expenses)
        assert report.factual_metrics.total_spending == 7_500_001.00
        assert report.factual_metrics.average_transaction == 3_750_000.50

    def test_missing_and_blank_categories(
        self, analytics_service: ExpenseAnalyticsService
    ) -> None:
        expenses = [
            NormalizedExpense(date="2025-01-01", description="Misc Item", category="", amount=20.00),
        ]
        report = analytics_service.analyze(expenses)
        assert "Other" in report.factual_metrics.spending_by_category
        assert report.factual_metrics.spending_by_category["Other"] == 20.00


class TestFactualCalculationsAndMultiMonthTimeSeries:
    """Tests multi-month aggregations, category breakdowns, and concentration metrics."""

    @pytest.fixture
    def multi_month_dataset(self) -> list[NormalizedExpense]:
        return [
            # January 2025
            NormalizedExpense(date="2025-01-05", description="Rent", category="Housing", amount=1500.00),
            NormalizedExpense(date="2025-01-10", description="Supermarket", category="Groceries", amount=200.00),
            NormalizedExpense(date="2025-01-15", description="Electricity", category="Utilities", amount=120.00),
            NormalizedExpense(date="2025-01-20", description="Restaurant", category="Food & Dining", amount=80.00),
            NormalizedExpense(date="2025-01-28", description="Streaming", category="Entertainment", amount=15.00),
            # February 2025
            NormalizedExpense(date="2025-02-05", description="Rent", category="Housing", amount=1500.00),
            NormalizedExpense(date="2025-02-12", description="Supermarket", category="Groceries", amount=250.00),
            NormalizedExpense(date="2025-02-18", description="Gas Bill", category="Utilities", amount=90.00),
            NormalizedExpense(date="2025-02-22", description="Concert", category="Entertainment", amount=120.00),
            NormalizedExpense(date="2025-02-28", description="Streaming", category="Entertainment", amount=15.00),
            # March 2025
            NormalizedExpense(date="2025-03-05", description="Rent", category="Housing", amount=1500.00),
            NormalizedExpense(date="2025-03-14", description="Supermarket", category="Groceries", amount=180.00),
            NormalizedExpense(date="2025-03-28", description="Streaming", category="Entertainment", amount=15.00),
        ]

    def test_multi_month_monthly_aggregation(
        self, analytics_service: ExpenseAnalyticsService, multi_month_dataset: list[NormalizedExpense]
    ) -> None:
        report = analytics_service.analyze(multi_month_dataset)
        monthly = report.factual_metrics.monthly_spending

        assert len(monthly) == 3
        assert monthly[0].month == "2025-01"
        assert monthly[0].amount == 1915.00
        assert monthly[0].transaction_count == 5

        assert monthly[1].month == "2025-02"
        assert monthly[1].amount == 1975.00
        assert monthly[1].transaction_count == 5

        assert monthly[2].month == "2025-03"
        assert monthly[2].amount == 1695.00
        assert monthly[2].transaction_count == 3

    def test_category_distribution_and_percentages(
        self, analytics_service: ExpenseAnalyticsService, multi_month_dataset: list[NormalizedExpense]
    ) -> None:
        report = analytics_service.analyze(multi_month_dataset)
        cat_spend = report.factual_metrics.spending_by_category
        cat_pcts = report.factual_metrics.category_percentages

        assert cat_spend["Housing"] == 4500.00
        assert cat_spend["Groceries"] == 630.00
        assert cat_spend["Utilities"] == 210.00
        assert cat_spend["Entertainment"] == 165.00
        assert cat_spend["Food & Dining"] == 80.00

        # Percentages must sum to ~100%
        total_pct = sum(cat_pcts.values())
        assert pytest.approx(total_pct, abs=0.1) == 100.0

    def test_spending_concentration(
        self, analytics_service: ExpenseAnalyticsService, multi_month_dataset: list[NormalizedExpense]
    ) -> None:
        report = analytics_service.analyze(multi_month_dataset)
        conc = report.factual_metrics.spending_concentration

        # Top 3 categories: Housing (4500) + Groceries (630) + Utilities (210) = 5340 / 5585 = ~95.6%
        assert conc.top_3_categories_percentage > 90.0
        # Pareto 20% transactions
        assert conc.top_20_percent_transactions_percentage > 0.0

    def test_largest_expenses(
        self, analytics_service: ExpenseAnalyticsService, multi_month_dataset: list[NormalizedExpense]
    ) -> None:
        report = analytics_service.analyze(multi_month_dataset)
        largest = report.factual_metrics.largest_expenses

        assert len(largest) <= 10
        assert largest[0].amount == 1500.00
        assert largest[1].amount == 1500.00
        assert largest[2].amount == 1500.00


class TestHeuristicInsights:
    """Tests for rule-based recurring detection, discretionary estimation, and outliers."""

    def test_recurring_expense_heuristic(
        self, analytics_service: ExpenseAnalyticsService
    ) -> None:
        expenses = [
            NormalizedExpense(date="2025-01-01", description="Netflix.com", category="Entertainment", amount=19.99),
            NormalizedExpense(date="2025-02-01", description="Netflix.com", category="Entertainment", amount=19.99),
            NormalizedExpense(date="2025-03-01", description="Netflix.com", category="Entertainment", amount=19.99),
            NormalizedExpense(date="2025-01-15", description="One Time Dinner", category="Food & Dining", amount=65.00),
        ]
        report = analytics_service.analyze(expenses)
        recurring = report.heuristic_insights.recurring_expenses

        assert len(recurring) == 1
        assert recurring[0].description == "Netflix.com"
        assert recurring[0].amount == 19.99
        assert recurring[0].occurrences == 3
        assert recurring[0].estimated_frequency == "Monthly"
        assert "Netflix" in recurring[0].confidence_note

    def test_discretionary_spending_estimate(
        self, analytics_service: ExpenseAnalyticsService
    ) -> None:
        expenses = [
            NormalizedExpense(date="2025-01-01", description="Mortgage", category="Housing", amount=1000.00),
            NormalizedExpense(date="2025-01-02", description="Sushi House", category="Food & Dining", amount=100.00),
            NormalizedExpense(date="2025-01-03", description="Zara Clothes", category="Shopping", amount=150.00),
        ]
        report = analytics_service.analyze(expenses)
        disc = report.heuristic_insights.discretionary_spending_estimate

        # Discretionary = Dining (100) + Shopping (150) = 250 / 1250 = 20%
        assert disc.amount == 250.00
        assert disc.percentage_of_total == 20.00
        assert "Shopping" in disc.discretionary_categories
        assert "Food & Dining" in disc.discretionary_categories

    def test_unusual_expense_outlier_detection(
        self, analytics_service: ExpenseAnalyticsService
    ) -> None:
        expenses = [
            NormalizedExpense(date="2025-01-01", description="Coffee", category="Food & Dining", amount=4.50),
            NormalizedExpense(date="2025-01-02", description="Lunch", category="Food & Dining", amount=12.00),
            NormalizedExpense(date="2025-01-03", description="Dinner", category="Food & Dining", amount=15.00),
            NormalizedExpense(date="2025-01-04", description="Snack", category="Food & Dining", amount=5.00),
            NormalizedExpense(date="2025-01-05", description="Fancy Gala Dinner", category="Food & Dining", amount=350.00),
        ]
        report = analytics_service.analyze(expenses)
        unusual = report.heuristic_insights.unusual_spending_observations

        assert len(unusual) >= 1
        assert any(o.amount == 350.00 for o in unusual)
        assert any("exceeds" in o.reason.lower() or "constitutes" in o.reason.lower() for o in unusual)


class TestAnalyticsApiEndpoint:
    """API endpoint POST /api/v1/expenses/analyze integration test."""

    def test_analyze_endpoint_returns_report(self, client: TestClient) -> None:
        payload = {
            "expenses": [
                {"date": "2025-01-01", "description": "Coffee", "category": "Food & Dining", "amount": 4.50},
                {"date": "2025-01-02", "description": "Book", "category": "Education", "amount": 25.00},
            ]
        }
        response = client.post("/api/v1/expenses/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        report = ExpenseAnalyticsReport(**data)

        assert report.factual_metrics.total_spending == 29.50
        assert report.factual_metrics.transaction_count == 2
        assert report.factual_metrics.spending_by_category == {
            "Education": 25.00,
            "Food & Dining": 4.50,
        }
        assert isinstance(report.heuristic_insights.discretionary_spending_estimate.amount, float)
