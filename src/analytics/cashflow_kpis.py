"""
Sprint 2 - Day 11
Cash Flow KPIs & Capital Allocation
"""

from typing import Optional


def free_cash_flow(
    operating_activity: float | int | None,
    investing_activity: float | int | None,
) -> Optional[float]:
    """Free Cash Flow = Operating Activity + Investing Activity."""

    if operating_activity is None or investing_activity is None:
        return None

    return float(operating_activity) + float(investing_activity)


def cfo_quality_score(
    cfo: float | int | None,
    pat: float | int | None,
) -> Optional[float]:
    """CFO / PAT. Returns None when PAT is zero."""

    if cfo is None or pat is None:
        return None

    pat = float(pat)

    if pat == 0:
        return None

    return float(cfo) / pat


def cfo_quality_label(
    score: float | int | None,
) -> Optional[str]:
    """Classify CFO quality."""

    if score is None:
        return None

    score = float(score)

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def capex_intensity(
    investing_activity: float | int | None,
    sales: float | int | None,
) -> Optional[float]:
    """CapEx Intensity = abs(investing activity) / sales * 100."""

    if investing_activity is None or sales is None:
        return None

    sales = float(sales)

    if sales == 0:
        return None

    return abs(float(investing_activity)) / sales * 100


def capex_intensity_label(
    intensity: float | int | None,
) -> Optional[str]:
    """Classify CapEx intensity."""

    if intensity is None:
        return None

    intensity = float(intensity)

    if intensity < 3:
        return "Asset Light"

    if intensity <= 8:
        return "Moderate"

    return "Capital Intensive"


def fcf_conversion_rate(
    fcf: float | int | None,
    operating_profit: float | int | None,
) -> Optional[float]:
    """FCF / Operating Profit * 100."""

    if fcf is None or operating_profit is None:
        return None

    operating_profit = float(operating_profit)

    if operating_profit == 0:
        return None

    return float(fcf) / operating_profit * 100


def capital_allocation_pattern(
    cfo: float | int | None,
    cfi: float | int | None,
    cff: float | int | None,
    cfo_pat_ratio: float | int | None = None,
) -> str:
    """Classify capital allocation pattern."""

    if cfo is None or cfi is None or cff is None:
        return "Unknown"

    cfo_positive = float(cfo) >= 0
    cfi_positive = float(cfi) >= 0
    cff_positive = float(cff) >= 0

    if cfo_positive and not cfi_positive and not cff_positive:
        if (
            cfo_pat_ratio is not None
            and float(cfo_pat_ratio) > 1.0
        ):
            return "Shareholder Returns"

        return "Reinvestor"

    if cfo_positive and cfi_positive and not cff_positive:
        return "Liquidating Assets"

    if not cfo_positive and cfi_positive and cff_positive:
        return "Distress Signal"

    if not cfo_positive and not cfi_positive and cff_positive:
        return "Growth Funded by Debt"

    if cfo_positive and cfi_positive and cff_positive:
        return "Cash Accumulator"

    if not cfo_positive and not cfi_positive and not cff_positive:
        return "Pre-Revenue"

    if cfo_positive and not cfi_positive and cff_positive:
        return "Mixed"

    return "Mixed"


def cash_flow_sign(
    value: float | int | None,
) -> str:
    """Convert cash flow to +, -, or 0."""

    if value is None:
        return "0"

    value = float(value)

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"