"""
AI generation API routes for v1.

Uses asyncio.to_thread to run synchronous Gemini SDK calls in a worker threadpool,
ensuring the main FastAPI asyncio event loop never blocks and /api/v1/health remains
fully responsive during AI operations.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from app.backend.core.config import Settings, get_settings
from app.backend.schemas.ai import (
    AiAssistantQueryRequest,
    AiAssistantQueryResponse,
    AiExpenseInsightsResponse,
    AiRoastRequest,
)
from app.backend.services.analytics_service import (
    ExpenseAnalyticsService,
    analytics_service,
)
from app.backend.services.gemini_service import (
    GeminiExpenseService,
)

router = APIRouter(prefix="/ai", tags=["AI Insights"])


def get_analytics_service() -> ExpenseAnalyticsService:
    """Dependency provider for ExpenseAnalyticsService."""
    return analytics_service


def get_gemini_service(settings: Settings = Depends(get_settings)) -> GeminiExpenseService:
    """Dependency provider for GeminiExpenseService initialized with current settings."""
    return GeminiExpenseService(settings=settings)


@router.post(
    "/roast",
    response_model=AiExpenseInsightsResponse,
    summary="Generate AI Roast and Recovery Plan",
    description="Generate a humorous financial roast, key insights, and actionable recovery plan based on normalized expenses.",
)
async def generate_roast_and_recovery(
    request: AiRoastRequest,
    analytics: ExpenseAnalyticsService = Depends(get_analytics_service),
    gemini: GeminiExpenseService = Depends(get_gemini_service),
) -> AiExpenseInsightsResponse:
    """
    Produce a structured AI roast and recovery plan.

    1. Computes deterministic analytics summary.
    2. Packages compact analytical data safely inside prompt-injection defense tags.
    3. Requests structured JSON from Gemini via non-blocking worker thread.
    4. Validates output with Pydantic.
    """
    analytics_report = analytics.analyze(request.expenses)
    # Offload blocking Gemini SDK network call to worker thread
    return await asyncio.to_thread(gemini.generate_insights, analytics_report)


@router.post(
    "/ask",
    response_model=AiAssistantQueryResponse,
    summary="Ask AI Expense Assistant",
    description="Ask natural language questions about analyzed expense records.",
)
async def ask_assistant(
    request: AiAssistantQueryRequest,
    analytics: ExpenseAnalyticsService = Depends(get_analytics_service),
    gemini: GeminiExpenseService = Depends(get_gemini_service),
) -> AiAssistantQueryResponse:
    """
    Answer user query grounded strictly in the analyzed financial metrics.
    Offloads blocking Gemini SDK call to a worker thread so the event loop is never blocked.
    """
    analytics_report = analytics.analyze(request.expenses)
    # Offload blocking Gemini SDK network call to worker thread
    answer = await asyncio.to_thread(
        gemini.answer_query,
        query=request.query,
        report=analytics_report,
        history=request.history,
    )
    return AiAssistantQueryResponse(answer=answer)
