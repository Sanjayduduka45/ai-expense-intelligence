"""
Shared constants used across the backend and (via direct import) the frontend.

Keep this file free of any runtime side-effects.
"""

from __future__ import annotations

# ── Application metadata ───────────────────────────────────────────────────────
APP_NAME: str = "AI Expense Intelligence"
APP_TAGLINE: str = "Roast • Analyze • Recover"
APP_VERSION: str = "0.1.0"

# ── HTTP status codes (re-exported for convenience) ───────────────────────────
HTTP_200_OK: int = 200
HTTP_422_UNPROCESSABLE: int = 422
HTTP_500_INTERNAL: int = 500

# ── API route prefixes ────────────────────────────────────────────────────────
API_V1_PREFIX: str = "/api/v1"

# ── Supported file types for expense upload ───────────────────────────────────
SUPPORTED_UPLOAD_EXTENSIONS: frozenset[str] = frozenset({".csv", ".xlsx", ".xls"})
MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

# ── Expense categories (will be extended in later phases) ─────────────────────
DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Housing",
    "Food & Dining",
    "Transportation",
    "Entertainment",
    "Health & Fitness",
    "Shopping",
    "Utilities",
    "Travel",
    "Education",
    "Other",
)
