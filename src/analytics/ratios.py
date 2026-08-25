"""
Sprint 2 - Financial Ratio Engine

Day 08:
Profitability ratios
"""

from typing import Optional


def net_profit_margin(
    net_profit: float | int | None,
    sales: float | int | None,
) -> Optional[float]:
    """
    Net Profit Margin = Net Profit / Sales * 100

    Returns None when sales is zero or unavailable.
    """

    if net_profit is None or sales is None:
        return None

    if sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(
    operating_profit: float | int | None,
    sales: float | int | None,
) -> Optional[float]:
    """
    Operating Profit Margin = Operating Profit / Sales * 100

    Returns None when sales is zero or unavailable.
    """

    if operating_profit is None or sales is None:
        return None

    if sales == 0:
        return None

    return (operating_profit / sales) * 100


def check_opm_cross_check(
    calculated_opm: float | None,
    source_opm: float | int | None,
    tolerance: float = 1.0,
) -> bool:
    """
    Compare calculated OPM with the source OPM.

    Returns True when the absolute difference is greater
    than the allowed tolerance.
    """

    if calculated_opm is None or source_opm is None:
        return False

    return abs(calculated_opm - float(source_opm)) > tolerance


def return_on_equity(
    net_profit: float | int | None,
    equity_capital: float | int | None,
    reserves: float | int | None,
) -> Optional[float]:
    """
    ROE = Net Profit / (Equity Capital + Reserves) * 100

    If equity + reserves <= 0, return None.
    """

    if (
        net_profit is None
        or equity_capital is None
        or reserves is None
    ):
        return None

    equity = float(equity_capital) + float(reserves)

    if equity <= 0:
        return None

    return (float(net_profit) / equity) * 100


def return_on_capital_employed(
    ebit: float | int | None,
    equity_capital: float | int | None,
    reserves: float | int | None,
    borrowings: float | int | None,
) -> Optional[float]:
    """
    ROCE = EBIT /
           (Equity Capital + Reserves + Borrowings) * 100

    Returns None when the denominator is zero or negative.
    """

    if (
        ebit is None
        or equity_capital is None
        or reserves is None
        or borrowings is None
    ):
        return None

    capital_employed = (
        float(equity_capital)
        + float(reserves)
        + float(borrowings)
    )

    if capital_employed <= 0:
        return None

    return (float(ebit) / capital_employed) * 100


def return_on_assets(
    net_profit: float | int | None,
    total_assets: float | int | None,
) -> Optional[float]:
    """
    ROA = Net Profit / Total Assets * 100

    Returns None when total assets is zero or unavailable.
    """

    if net_profit is None or total_assets is None:
        return None

    if total_assets == 0:
        return None

    return (float(net_profit) / float(total_assets)) * 100

def debt_to_equity(
    borrowings: float | int | None,
    equity_capital: float | int | None,
    reserves: float | int | None,
) -> Optional[float]:
    """
    Debt-to-Equity = Borrowings / (Equity Capital + Reserves)

    Debt-free companies return 0.
    """

    if borrowings is None or equity_capital is None or reserves is None:
        return None

    borrowings = float(borrowings)
    equity = float(equity_capital) + float(reserves)

    if borrowings == 0:
        return 0.0

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(
    debt_to_equity_value: float | None,
    broad_sector: str | None,
) -> bool:
    """
    Flag D/E > 5 for non-Financials companies.

    Financials are excluded because high leverage is structurally normal.
    """

    if debt_to_equity_value is None:
        return False

    if broad_sector is not None:
        if broad_sector.strip().lower() == "financials":
            return False

    return debt_to_equity_value > 5


def interest_coverage_ratio(
    operating_profit: float | int | None,
    other_income: float | int | None,
    interest: float | int | None,
) -> Optional[float]:
    """
    ICR = (Operating Profit + Other Income) / Interest

    Returns None when interest is zero.
    """

    if (
        operating_profit is None
        or other_income is None
        or interest is None
    ):
        return None

    if interest == 0:
        return None

    return (
        (float(operating_profit) + float(other_income))
        / float(interest)
    )


def interest_coverage_label(
    icr: float | None,
) -> Optional[str]:
    """
    Return 'Debt Free' when ICR is None.
    """

    if icr is None:
        return "Debt Free"

    return None


def interest_coverage_warning(
    icr: float | None,
) -> bool:
    """
    Flag companies with ICR below 1.5.
    """

    if icr is None:
        return False

    return icr < 1.5


def net_debt(
    borrowings: float | int | None,
    investments: float | int | None,
) -> Optional[float]:
    """
    Net Debt = Borrowings - Investments
    """

    if borrowings is None or investments is None:
        return None

    return float(borrowings) - float(investments)


def asset_turnover(
    sales: float | int | None,
    total_assets: float | int | None,
) -> Optional[float]:
    """
    Asset Turnover = Sales / Total Assets

    Returns None when total assets are zero.
    """

    if sales is None or total_assets is None:
        return None

    if total_assets == 0:
        return None

    return float(sales) / float(total_assets)