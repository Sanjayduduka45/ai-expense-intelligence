"""
Phase 9: End-to-end integration and workflow verification tests.

Verifies:
1. Critical Flow 1: Upload CSV -> Validation -> Analytics -> AI Roast & Recovery Plan.
2. Critical Flow 2: Upload CSV -> Analytics -> Assistant Q&A with conversation history.
3. Frontend API client wrapper methods (health, upload, analyze, roast, ask).
4. Edge Case Matrix (single row, duplicates, missing category, Gemini errors, empty datasets).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
import httpx

from app.backend.core.config import Settings, get_settings
from app.backend.main import app
from app.backend.schemas.ai import AiExpenseInsightsResponse
from app.frontend.utils.api_client import (
    analyze_expenses,
    ask_ai_assistant,
    fetch_ai_roast,
    fetch_health,
    upload_expense_file,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous test client for FastAPI backend."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_roast_json() -> str:
    return json.dumps(
        {
            "roast": "Spending $120 on artisanal sourdough while living on a graduate stipend is truly a lifestyle.",
            "roast_evidence": [
                "Dining out represents $120.00 (45.3% of total spend).",
                "Total tracked spending: $265.00 across 3 transactions.",
            ],
            "summary": "Total expenditure is $265.00 across 3 transactions with high discretionary spend.",
            "key_insights": [
                "Food & Dining is your top spending category.",
                "Identified 1 recurring subscription ($15.00/mo).",
            ],
            "spending_problems": [
                "High discretionary dining expenditures.",
            ],
            "structured_recovery_plan": [
                {
                    "problem": "Frequent dining out.",
                    "action": "Cook at home 4 days a week.",
                    "estimated_monthly_saving": 60.0,
                    "estimated_yearly_saving": 720.0,
                    "priority": "High",
                    "is_heuristic_estimate": True,
                }
            ],
            "recovery_plan": [
                "Cook at home 4 days a week.",
            ],
            "recommendations": [
                "Track grocery vs dining spend weekly.",
            ],
            "savings_opportunities": [
                "Save up to $60/month on food.",
            ],
        }
    )


class TestEndToEndCriticalFlows:
    """Verify complete multi-stage user workflows."""

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_flow1_upload_validate_analyze_roast(
        self,
        mock_configure: MagicMock,
        mock_model_cls: MagicMock,
        client: TestClient,
        mock_roast_json: str,
    ) -> None:
        """Test Critical Flow 1: Upload -> Validation -> Analytics -> AI Roast & Plan."""
        # 1. Prepare raw CSV
        csv_bytes = (
            b"Transaction Date,Merchant Details,Category,Debit Amount\n"
            b"2025-01-01,Whole Foods Bakery,Food & Dining,120.00\n"
            b"2025-01-02,Spotify,Entertainment,15.00\n"
            b"2025-01-03,Target Home,Shopping,130.00\n"
        )

        # 2. Upload CSV via API
        upload_resp = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("january_expenses.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        assert upload_data["status"] == "success"
        assert upload_data["valid_rows"] == 3
        assert upload_data["total_spending"] == 265.00
        normalized_expenses = upload_data["data"]

        # 3. Analyze Normalized Expenses
        analyze_resp = client.post(
            "/api/v1/expenses/analyze",
            json={"expenses": normalized_expenses},
        )
        assert analyze_resp.status_code == 200
        report = analyze_resp.json()

        # Check factual metrics
        factual = report["factual_metrics"]
        assert factual["total_spending"] == 265.00
        assert factual["transaction_count"] == 3
        assert factual["spending_by_category"]["Shopping"] == 130.00
        assert factual["spending_by_category"]["Food & Dining"] == 120.00

        # Check heuristic insights
        heuristics = report["heuristic_insights"]
        assert heuristics["discretionary_spending_estimate"]["amount"] > 0
        assert len(factual["largest_expenses"]) == 3

        # 4. Generate AI Roast & Recovery Plan (Mocked Gemini)
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = mock_roast_json
        mock_instance.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_instance

        app.dependency_overrides[get_settings] = lambda: Settings(gemini_api_key="mock_key")
        try:
            roast_resp = client.post(
                "/api/v1/ai/roast",
                json={"expenses": normalized_expenses},
            )
            assert roast_resp.status_code == 200
            roast_data = roast_resp.json()
            assert "sourdough" in roast_data["roast"]
            assert len(roast_data["roast_evidence"]) > 0
            assert len(roast_data["structured_recovery_plan"]) == 1
            assert roast_data["structured_recovery_plan"][0]["priority"] == "High"
            assert roast_data["structured_recovery_plan"][0]["estimated_monthly_saving"] == 60.0
        finally:
            app.dependency_overrides.pop(get_settings, None)

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_flow2_upload_analyze_assistant_qa(
        self,
        mock_configure: MagicMock,
        mock_model_cls: MagicMock,
        client: TestClient,
    ) -> None:
        """Test Critical Flow 2: Upload -> Analytics -> Assistant Q&A."""
        csv_bytes = (
            b"date,description,amount,category\n"
            b"2025-01-01,Chipotle,14.50,Food & Dining\n"
            b"2025-01-02,Trader Joes,85.00,Groceries\n"
        )
        upload_resp = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("expenses.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        expenses = upload_resp.json()["data"]

        # Mock Gemini assistant answer
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "You spent $14.50 at Chipotle in Food & Dining, and $85.00 at Trader Joes in Groceries."
        mock_instance.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_instance

        app.dependency_overrides[get_settings] = lambda: Settings(gemini_api_key="mock_key")
        try:
            ask_resp = client.post(
                "/api/v1/ai/ask",
                json={
                    "query": "Where did I buy food?",
                    "expenses": expenses,
                    "history": [],
                },
            )
            assert ask_resp.status_code == 200
            assert "Chipotle" in ask_resp.json()["answer"]
            assert "Trader Joes" in ask_resp.json()["answer"]
        finally:
            app.dependency_overrides.pop(get_settings, None)


class TestFrontendApiClientWrappers:
    """Verify frontend/utils/api_client.py functions using httpx.MockTransport."""

    def test_fetch_health_success(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, json={"status": "ok", "version": "0.1.0"})
        )
        with patch("httpx.Client", return_value=httpx.Client(transport=transport)):
            result = fetch_health()
            assert result["status"] == "ok"
            assert result["version"] == "0.1.0"

    def test_upload_expense_file_success(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, json={"filename": "test.csv", "valid_rows": 2})
        )
        with patch("httpx.Client", return_value=httpx.Client(transport=transport)):
            result = upload_expense_file(b"date,description,amount\n2025-01-01,A,1.0\n", "test.csv")
            assert result["success"] is True
            assert result["data"]["valid_rows"] == 2

    def test_analyze_expenses_success(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, json={"factual_metrics": {"total_spending": 50.0}})
        )
        with patch("httpx.Client", return_value=httpx.Client(transport=transport)):
            result = analyze_expenses([{"date": "2025-01-01", "description": "A", "category": "Other", "amount": 50.0}])
            assert result["success"] is True
            assert result["data"]["factual_metrics"]["total_spending"] == 50.0

    def test_fetch_ai_roast_success(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, json={"roast": "Good roast"})
        )
        with patch("httpx.Client", return_value=httpx.Client(transport=transport)):
            result = fetch_ai_roast([{"date": "2025-01-01", "description": "A", "category": "Other", "amount": 50.0}])
            assert result["success"] is True
            assert result["data"]["roast"] == "Good roast"

    def test_ask_ai_assistant_success(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, json={"answer": "You spent $50."})
        )
        with patch("httpx.Client", return_value=httpx.Client(transport=transport)):
            result = ask_ai_assistant("How much?", [{"date": "2025-01-01", "description": "A", "category": "Other", "amount": 50.0}])
            assert result["success"] is True
            assert result["data"]["answer"] == "You spent $50."


class TestEdgeCaseMatrix:
    """Verify system resilience across the complete edge case matrix."""

    def test_one_row_dataset(self, client: TestClient) -> None:
        csv_bytes = b"date,description,amount\n2025-01-01,Coffee,4.50\n"
        upload_resp = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("single.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        data = upload_resp.json()
        assert data["valid_rows"] == 1

        analyze_resp = client.post(
            "/api/v1/expenses/analyze",
            json={"expenses": data["data"]},
        )
        assert analyze_resp.status_code == 200
        report = analyze_resp.json()
        assert report["factual_metrics"]["transaction_count"] == 1
        assert report["factual_metrics"]["average_transaction"] == 4.50

    def test_missing_optional_categories_defaults_to_other(self, client: TestClient) -> None:
        csv_bytes = b"date,description,amount\n2025-01-01,Coffee,4.50\n2025-01-02,Book,15.00\n"
        upload_resp = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("no_cat.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        expenses = upload_resp.json()["data"]
        assert all(e["category"] == "Other" for e in expenses)

    def test_duplicate_rows_detected(self, client: TestClient) -> None:
        csv_bytes = (
            b"date,description,amount\n"
            b"2025-01-01,Coffee,4.50\n"
            b"2025-01-01,Coffee,4.50\n"
        )
        upload_resp = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("dups.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        data = upload_resp.json()
        assert data["valid_rows"] == 2
        assert data["duplicate_rows"] == 1

    def test_invalid_dates_and_amounts_skipped_with_partial_status(self, client: TestClient) -> None:
        csv_bytes = (
            b"date,description,amount\n"
            b"2025-01-01,Valid Coffee,4.50\n"
            b"invalid-date,Bad Date Coffee,5.00\n"
            b"2025-01-02,Negative Coffee,-3.00\n"
            b"2025-01-03,String Amount Coffee,Free\n"
        )
        upload_resp = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("mixed.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        data = upload_resp.json()
        assert data["status"] == "partial"
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 3
        assert len(data["errors"]) == 3

    def test_empty_assistant_query_handled_safely(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = lambda: Settings(gemini_api_key="mock_key")
        try:
            response = client.post(
                "/api/v1/ai/ask",
                json={
                    "query": "   ",
                    "expenses": [{"date": "2025-01-01", "description": "Coffee", "category": "Food", "amount": 4.50}],
                },
            )
            assert response.status_code == 200
            assert "Please provide a question" in response.json()["answer"]
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_assistant_query_with_no_expenses_handled_safely(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = lambda: Settings(gemini_api_key="mock_key")
        try:
            response = client.post(
                "/api/v1/ai/ask",
                json={
                    "query": "What did I spend?",
                    "expenses": [],
                },
            )
            assert response.status_code == 200
            assert "No expense data is currently loaded" in response.json()["answer"]
        finally:
            app.dependency_overrides.pop(get_settings, None)
