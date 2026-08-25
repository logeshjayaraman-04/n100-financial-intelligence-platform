from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    cfo_quality_label,
    capex_intensity,
    capex_intensity_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
    cash_flow_sign,
)


def test_free_cash_flow():
    result = free_cash_flow(
        operating_activity=100,
        investing_activity=-40,
    )
    assert result == 60.0


def test_free_cash_flow_negative_allowed():
    result = free_cash_flow(
        operating_activity=20,
        investing_activity=-50,
    )
    assert result == -30.0


def test_cfo_quality_score():
    result = cfo_quality_score(
        cfo=120,
        pat=100,
    )
    assert result == 1.2


def test_cfo_quality_zero_pat():
    result = cfo_quality_score(
        cfo=100,
        pat=0,
    )
    assert result is None


def test_cfo_quality_high():
    assert cfo_quality_label(1.2) == "High Quality"


def test_cfo_quality_moderate():
    assert cfo_quality_label(0.7) == "Moderate"


def test_cfo_quality_accrual_risk():
    assert cfo_quality_label(0.3) == "Accrual Risk"


def test_capex_intensity():
    result = capex_intensity(
        investing_activity=-20,
        sales=1000,
    )
    assert result == 2.0


def test_capex_intensity_zero_sales():
    result = capex_intensity(
        investing_activity=-20,
        sales=0,
    )
    assert result is None


def test_capex_asset_light():
    assert capex_intensity_label(2.0) == "Asset Light"


def test_capex_moderate():
    assert capex_intensity_label(5.0) == "Moderate"


def test_capex_capital_intensive():
    assert capex_intensity_label(10.0) == "Capital Intensive"


def test_fcf_conversion_rate():
    result = fcf_conversion_rate(
        fcf=50,
        operating_profit=100,
    )
    assert result == 50.0


def test_fcf_conversion_zero_operating_profit():
    result = fcf_conversion_rate(
        fcf=50,
        operating_profit=0,
    )
    assert result is None


def test_reinvestor_pattern():
    result = capital_allocation_pattern(
        cfo=100,
        cfi=-50,
        cff=-20,
    )
    assert result == "Reinvestor"


def test_shareholder_returns_pattern():
    result = capital_allocation_pattern(
        cfo=150,
        cfi=-50,
        cff=-20,
        cfo_pat_ratio=1.5,
    )
    assert result == "Shareholder Returns"


def test_liquidating_assets_pattern():
    result = capital_allocation_pattern(
        cfo=100,
        cfi=50,
        cff=-20,
    )
    assert result == "Liquidating Assets"


def test_distress_signal_pattern():
    result = capital_allocation_pattern(
        cfo=-100,
        cfi=50,
        cff=20,
    )
    assert result == "Distress Signal"


def test_growth_funded_by_debt_pattern():
    result = capital_allocation_pattern(
        cfo=-100,
        cfi=-50,
        cff=150,
    )
    assert result == "Growth Funded by Debt"


def test_cash_accumulator_pattern():
    result = capital_allocation_pattern(
        cfo=100,
        cfi=50,
        cff=20,
    )
    assert result == "Cash Accumulator"


def test_pre_revenue_pattern():
    result = capital_allocation_pattern(
        cfo=-100,
        cfi=-50,
        cff=-20,
    )
    assert result == "Pre-Revenue"


def test_mixed_pattern():
    result = capital_allocation_pattern(
        cfo=100,
        cfi=-50,
        cff=20,
    )
    assert result == "Mixed"


def test_cash_flow_sign():
    assert cash_flow_sign(100) == "+"
    assert cash_flow_sign(-100) == "-"
    assert cash_flow_sign(0) == "0"