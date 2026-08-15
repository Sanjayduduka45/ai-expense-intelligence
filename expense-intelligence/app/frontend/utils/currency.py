"""
INR Currency formatting utility for AI Expense Intelligence.

Formats monetary amounts using the Indian Rupee (₹) symbol and Indian numbering system
(e.g., ₹1,500.00, ₹10,000.00, ₹1,25,000.00, ₹10,00,000.00).
"""

from __future__ import annotations


def format_inr(amount: float | int | None) -> str:
    """
    Format a numeric amount as Indian Rupees (₹) using Indian numbering system.

    Examples:
        format_inr(150.0) -> '₹150.00'
        format_inr(2604.72) -> '₹2,604.72'
        format_inr(125000.0) -> '₹1,25,000.00'
        format_inr(1000000.0) -> '₹10,00,000.00'
    """
    if amount is None:
        return "₹0.00"

    try:
        val = float(amount)
    except (ValueError, TypeError):
        return "₹0.00"

    is_negative = val < 0
    val = abs(val)

    # Format to 2 decimal places
    parts = f"{val:.2f}".split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        # Last 3 digits
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        # Group remaining digits in pairs of 2 from right to left
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last_three

    sign = "-" if is_negative else ""
    return f"{sign}₹{formatted_int}.{decimal_part}"
