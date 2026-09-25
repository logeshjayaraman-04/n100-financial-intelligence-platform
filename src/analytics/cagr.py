"""
Sprint 2 - CAGR Engine

Day 10:
Revenue, PAT and EPS CAGR calculations
with all required edge-case flags.
"""

CAGR_OK = "OK"
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
TURNAROUND = "TURNAROUND"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


def calculate_cagr(
    start_value: float | None,
    end_value: float | None,
    years: int | None,
) -> tuple[float | None, str]:
    """
    Calculate CAGR.

    Formula:
        ((end / start) ** (1 / years) - 1) * 100

    Returns:
        (cagr_value, flag)
    """

    if start_value is None or end_value is None or years is None:
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
    start_revenue: float | None,
    end_revenue: float | None,
    years: int | None,
) -> tuple[float | None, str]:
    """
    Calculate Revenue CAGR.
    """

    return calculate_cagr(
        start_revenue,
        end_revenue,
        years,
    )


def pat_cagr(
    start_pat: float | None,
    end_pat: float | None,
    years: int | None,
) -> tuple[float | None, str]:
    """
    Calculate PAT / Net Profit CAGR.
    """

    return calculate_cagr(
        start_pat,
        end_pat,
        years,
    )


def eps_cagr(
    start_eps: float | None,
    end_eps: float | None,
    years: int | None,
) -> tuple[float | None, str]:
    """
    Calculate EPS CAGR.
    """

    return calculate_cagr(
        start_eps,
        end_eps,
        years,
    )
