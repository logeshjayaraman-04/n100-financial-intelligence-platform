"""
Sprint 2 - CAGR Engine

Day 10:
Revenue, PAT and EPS CAGR calculations
with all required edge-case flags.
"""

from typing import Optional


CAGR_OK = "OK"
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
TURNAROUND = "TURNAROUND"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


def calculate_cagr(
    start_value: float | int | None,
    end_value: float | int | None,
    years: int | None,
) -> tuple[Optional[float], str]:
    """
    Calculate CAGR.

    Formula:
        ((end / start) ** (1 / years) - 1) * 100

    Returns:
        (cagr_value, flag)
    """

    if (
        start_value is None
        or end_value is None
        or years is None
    ):
        return None, INSUFFICIENT

    if years <= 0:
        return None, INSUFFICIENT

    start = float(start_value)
    end = float(end_value)

    # Zero starting value.
    if start == 0:
        return None, ZERO_BASE

    # Positive -> negative.
    if start > 0 and end < 0:
        return None, DECLINE_TO_LOSS

    # Negative -> positive.
    if start < 0 and end > 0:
        return None, TURNAROUND

    # Negative -> negative.
    if start < 0 and end < 0:
        return None, BOTH_NEGATIVE

    # Positive -> positive.
    if start > 0 and end > 0:
        result = ((end / start) ** (1 / years) - 1) * 100

        return result, CAGR_OK

    # End value of zero after a positive starting value.
    if start > 0 and end == 0:
        return None, DECLINE_TO_LOSS

    return None, INSUFFICIENT


def revenue_cagr(
    start_revenue: float | int | None,
    end_revenue: float | int | None,
    years: int | None,
) -> tuple[Optional[float], str]:
    """
    Calculate Revenue CAGR.
    """

    return calculate_cagr(
        start_revenue,
        end_revenue,
        years,
    )


def pat_cagr(
    start_pat: float | int | None,
    end_pat: float | int | None,
    years: int | None,
) -> tuple[Optional[float], str]:
    """
    Calculate PAT / Net Profit CAGR.
    """

    return calculate_cagr(
        start_pat,
        end_pat,
        years,
    )


def eps_cagr(
    start_eps: float | int | None,
    end_eps: float | int | None,
    years: int | None,
) -> tuple[Optional[float], str]:
    """
    Calculate EPS CAGR.
    """

    return calculate_cagr(
        start_eps,
        end_eps,
        years,
    )