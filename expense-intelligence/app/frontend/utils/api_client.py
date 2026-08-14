"""
Frontend HTTP utility for calling the FastAPI backend.

Streamlit must never call Gemini directly — all AI calls go through
the backend service layer.
"""

from __future__ import annotations

import os

import httpx

# Resolve backend URL from environment (falls back to local dev default).
_BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")


def get_backend_url() -> str:
    """Return the configured backend base URL."""
    return _BACKEND_URL.rstrip("/")


def fetch_health() -> dict:
    """
    Call GET /health on the backend and return the parsed JSON body.

    Returns an error dict on connection failure so the UI can display
    a graceful message instead of raising an unhandled exception.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{get_backend_url()}/health")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        return {"status": "unreachable", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "detail": str(exc)}
