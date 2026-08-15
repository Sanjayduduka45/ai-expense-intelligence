"""
Pydantic schemas for Gemini AI responses, roast requests, and assistant Q&A.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.backend.schemas.common import BaseSchema
from app.backend.schemas.expense import NormalizedExpense


class ChatMessage(BaseSchema):
    """A single chat message in the assistant conversation."""

    role: str = Field(description="Message sender role: 'user' or 'assistant'")
    content: str = Field(description="Text content of the message")


class RecoveryRecommendation(BaseSchema):
    """An actionable, prioritized recovery action item with financial estimates."""

    problem: str = Field(description="The underlying spending problem or inefficiency")
    action: str = Field(description="Concrete, practical action recommended to resolve the issue")
    estimated_monthly_saving: float | None = Field(
        default=None, description="Estimated dollar amount saved per month"
    )
    estimated_yearly_saving: float | None = Field(
        default=None, description="Estimated dollar amount saved per year (12x monthly)"
    )
    priority: str = Field(
        default="Medium", description="Urgency/impact level: 'High', 'Medium', or 'Low'"
    )
    is_heuristic_estimate: bool = Field(
        default=True, description="Flag indicating the savings figure is a heuristic estimate"
    )


class AiExpenseInsightsResponse(BaseSchema):
    """Structured, validated AI output for financial roasts, analysis, and recovery roadmaps."""

    roast: str = Field(
        description="Humorous, sharp, concise roast focused strictly on spending behavior"
    )
    roast_evidence: list[str] = Field(
        default_factory=list,
        description="Factual, numerical evidence backing up the roast",
    )
    summary: str = Field(
        description="Executive financial summary grounded in actual calculated numbers"
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="Key analytical takeaways identified in the expense dataset",
    )
    spending_problems: list[str] = Field(
        default_factory=list,
        description="Specific financial pain points and leakage areas identified",
    )
    structured_recovery_plan: list[RecoveryRecommendation] = Field(
        default_factory=list,
        description="Prioritized, actionable recovery action items with monthly/yearly savings",
    )
    recovery_plan: list[str] = Field(
        default_factory=list,
        description="Text list of recovery steps for backward compatibility",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Practical, achievable spending and budgeting recommendations",
    )
    savings_opportunities: list[str] = Field(
        default_factory=list,
        description="Concrete estimated areas where spending could be optimized",
    )


class AiRoastRequest(BaseModel):
    """Request payload to generate AI insights from normalized expense records."""

    expenses: list[NormalizedExpense] = Field(
        description="List of normalized expense items to analyze and roast"
    )


class AiAssistantQueryRequest(BaseModel):
    """Request payload for asking natural language questions about expenses."""

    query: str = Field(description="User question regarding their expense data")
    expenses: list[NormalizedExpense] = Field(
        default_factory=list,
        description="List of normalized expense items to consult",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Optional recent conversation history for contextual follow-ups",
    )


class AiAssistantQueryResponse(BaseSchema):
    """Response payload containing the AI assistant's grounded answer."""

    answer: str = Field(description="Objective, grounded response to the user query")
