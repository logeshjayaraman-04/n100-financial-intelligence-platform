from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    check_opm_cross_check,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    interest_coverage_label,
    interest_coverage_warning,
    net_debt,
    asset_turnover,
)

def test_net_profit_margin_normal():
    result = net_profit_margin(20, 100)

    assert result == 20.0


def test_net_profit_margin_zero_sales():
    result = net_profit_margin(20, 0)

    assert result is None


def test_operating_profit_margin_normal():
    result = operating_profit_margin(30, 100)

    assert result == 30.0


def test_opm_cross_check_no_mismatch():
    result = check_opm_cross_check(
        calculated_opm=30.0,
        source_opm=30.5,
    )

    assert result is False


def test_opm_cross_check_mismatch():
    result = check_opm_cross_check(
        calculated_opm=30.0,
        source_opm=32.0,
    )

    assert result is True


def test_return_on_equity_normal():
    result = return_on_equity(
        net_profit=20,
        equity_capital=50,
        reserves=50,
    )

    assert result == 20.0


def test_return_on_equity_negative_equity():
    result = return_on_equity(
        net_profit=20,
        equity_capital=-100,
        reserves=20,
    )

    assert result is None


def test_return_on_assets_zero_assets():
    result = return_on_assets(
        net_profit=20,
        total_assets=0,
    )

    assert result is None


def test_return_on_assets_normal():
    result = return_on_assets(
        net_profit=20,
        total_assets=200,
    )

    assert result == 10.0


def test_return_on_capital_employed_normal():
    result = return_on_capital_employed(
        ebit=30,
        equity_capital=50,
        reserves=50,
        borrowings=100,
    )

    assert result == 15.0

def test_debt_to_equity_normal():
    result = debt_to_equity(
        borrowings=100,
        equity_capital=50,
        reserves=50,
    )

    assert result == 1.0


def test_debt_to_equity_debt_free():
    result = debt_to_equity(
        borrowings=0,
        equity_capital=50,
        reserves=50,
    )

    assert result == 0.0


def test_high_leverage_flag():
    result = high_leverage_flag(
        debt_to_equity_value=6.0,
        broad_sector="Industrials",
    )

    assert result is True


def test_financials_high_leverage_suppressed():
    result = high_leverage_flag(
        debt_to_equity_value=6.0,
        broad_sector="Financials",
    )

    assert result is False


def test_interest_coverage_normal():
    result = interest_coverage_ratio(
        operating_profit=100,
        other_income=20,
        interest=40,
    )

    assert result == 3.0


def test_interest_coverage_zero_interest():
    result = interest_coverage_ratio(
        operating_profit=100,
        other_income=20,
        interest=0,
    )

    assert result is None


def test_interest_coverage_debt_free_label():
    result = interest_coverage_label(None)

    assert result == "Debt Free"


def test_interest_coverage_warning():
    result = interest_coverage_warning(1.2)

    assert result is True


def test_net_debt():
    result = net_debt(
        borrowings=100,
        investments=30,
    )

    assert result == 70.0


def test_asset_turnover_normal():
    result = asset_turnover(
        sales=200,
        total_assets=100,
    )

    assert result == 2.0


def test_asset_turnover_zero_assets():
    result = asset_turnover(
        sales=200,
        total_assets=0,
    )

    assert result is None