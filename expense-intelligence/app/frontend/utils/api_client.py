"""
Frontend HTTP utility for calling the FastAPI backend.

Streamlit must never call Gemini directly — all AI calls, data validations,
and analytical calculations go through the backend service layer.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# Resolve backend URL from environment (falls back to local dev default).
_BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")


def get_backend_url() -> str:
    """Return the configured backend base URL."""
    return _BACKEND_URL.rstrip("/")


def fetch_health() -> dict[str, Any]:
    """
    Call GET /api/v1/health on the backend and return the parsed JSON body.

    Returns an error dict on connection failure so the UI can display
    a graceful message instead of raising an unhandled exception.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{get_backend_url()}/api/v1/health")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        return {"status": "unreachable", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "detail": str(exc)}


def upload_expense_file(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    Upload an untrusted expense CSV file to the backend for ingestion and validation.

    Returns the parsed JSON response or standardized error dictionary.
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            files = {"file": (filename, file_bytes, "text/csv")}
            response = client.post(
                f"{get_backend_url()}/api/v1/expenses/upload",
                files=files,
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_payload = response.json()
                    error_message = error_payload.get("error", {}).get(
                        "message", response.text
                    )
                except Exception:
                    error_message = response.text or f"HTTP {response.status_code}"
                return {"success": False, "detail": error_message}
    except httpx.RequestError as exc:
        return {
            "success": False,
            "detail": f"Could not connect to backend server: {exc}",
        }


def analyze_expenses(expenses: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Request deterministic financial analytics and heuristic insights from backend.

    Returns the parsed ExpenseAnalyticsReport JSON or error dictionary.
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{get_backend_url()}/api/v1/expenses/analyze",
                json={"expenses": expenses},
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_payload = response.json()
                    error_message = error_payload.get("error", {}).get(
                        "message", response.text
                    )
                except Exception:
                    error_message = response.text or f"HTTP {response.status_code}"
                return {"success": False, "detail": error_message}
    except httpx.RequestError as exc:
        return {
            "success": False,
            "detail": f"Could not connect to backend server: {exc}",
        }


def fetch_ai_roast(expenses: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Request Gemini AI financial roast and recovery plan from the backend service.

    Returns the validated AiExpenseInsightsResponse JSON or error dictionary.
    """
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{get_backend_url()}/api/v1/ai/roast",
                json={"expenses": expenses},
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_payload = response.json()
                    error_message = error_payload.get("error", {}).get(
                        "message", response.text
                    )
                except Exception:
                    error_message = response.text or f"HTTP {response.status_code}"
                return {"success": False, "detail": error_message}
    except httpx.RequestError as exc:
        return {
            "success": False,
            "detail": f"Could not connect to backend server: {exc}",
        }


def ask_ai_assistant(
    query: str,
    expenses: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Ask the AI Assistant a question regarding the user's analyzed expenses.

    Returns the assistant's answer or an error dictionary.
    """
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{get_backend_url()}/api/v1/ai/ask",
                json={
                    "query": query,
                    "expenses": expenses,
                    "history": history or [],
                },
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_payload = response.json()
                    error_message = error_payload.get("error", {}).get(
                        "message", response.text
                    )
                except Exception:
                    error_message = response.text or f"HTTP {response.status_code}"
                return {"success": False, "detail": error_message}
    except httpx.RequestError as exc:
        return {
            "success": False,
            "detail": f"Could not connect to backend server: {exc}",
        }
