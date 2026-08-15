"""Backend schemas package."""

from app.backend.schemas.ai import (
    AiAssistantQueryRequest,
    AiAssistantQueryResponse,
    AiExpenseInsightsResponse,
    AiRoastRequest,
    ChatMessage,
    RecoveryRecommendation,
)
from app.backend.schemas.analytics import (
    DailyAggregate,
    DiscretionaryEstimate,
    ExpenseAnalysisRequest,
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
from app.backend.schemas.common import BaseSchema, ErrorDetail, ErrorResponse
from app.backend.schemas.expense import (
    DateRange,
    ExpenseIngestionResponse,
    NormalizedExpense,
    RowValidationError,
)
from app.backend.schemas.health import HealthResponse

__all__ = [
    "AiAssistantQueryRequest",
    "AiAssistantQueryResponse",
    "AiExpenseInsightsResponse",
    "AiRoastRequest",
    "BaseSchema",
    "ChatMessage",
    "DailyAggregate",
    "DateRange",
    "DiscretionaryEstimate",
    "ErrorDetail",
    "ErrorResponse",
    "ExpenseAnalysisRequest",
    "ExpenseAnalyticsReport",
    "ExpenseIngestionResponse",
    "FactualMetrics",
    "HealthResponse",
    "HeuristicInsights",
    "MonthlyAggregate",
    "NormalizedExpense",
    "RecoveryRecommendation",
    "RecurringExpenseCandidate",
    "RowValidationError",
    "SavingsOpportunity",
    "SpendingConcentration",
    "UnusualExpenseObservation",
    "WeeklyAggregate",
]
