from src.analytics.cagr import (
    calculate_cagr,
    revenue_cagr,
    pat_cagr,
    eps_cagr,
    CAGR_OK,
    DECLINE_TO_LOSS,
    TURNAROUND,
    BOTH_NEGATIVE,
    ZERO_BASE,
    INSUFFICIENT,
)


def test_normal_cagr():
    result, flag = calculate_cagr(
        start_value=100,
        end_value=121,
        years=2,
    )

    assert round(result, 2) == 10.0
    assert flag == CAGR_OK


def test_positive_to_negative():
    result, flag = calculate_cagr(
        start_value=100,
        end_value=-20,
        years=3,
    )

    assert result is None
    assert flag == DECLINE_TO_LOSS


def test_negative_to_positive():
    result, flag = calculate_cagr(
        start_value=-100,
        end_value=50,
        years=3,
    )

    assert result is None
    assert flag == TURNAROUND


def test_both_negative():
    result, flag = calculate_cagr(
        start_value=-100,
        end_value=-50,
        years=3,
    )

    assert result is None
    assert flag == BOTH_NEGATIVE


def test_zero_base():
    result, flag = calculate_cagr(
        start_value=0,
        end_value=100,
        years=5,
    )

    assert result is None
    assert flag == ZERO_BASE


def test_insufficient_years():
    result, flag = calculate_cagr(
        start_value=100,
        end_value=150,
        years=0,
    )

    assert result is None
    assert flag == INSUFFICIENT


def test_revenue_cagr():
    result, flag = revenue_cagr(
        start_revenue=100,
        end_revenue=121,
        years=2,
    )

    assert round(result, 2) == 10.0
    assert flag == CAGR_OK


def test_pat_cagr():
    result, flag = pat_cagr(
        start_pat=100,
        end_pat=121,
        years=2,
    )

    assert round(result, 2) == 10.0
    assert flag == CAGR_OK


def test_eps_cagr():
    result, flag = eps_cagr(
        start_eps=10,
        end_eps=12.1,
        years=2,
    )

    assert round(result, 2) == 10.0
    assert flag == CAGR_OK


def test_missing_value_is_insufficient():
    result, flag = calculate_cagr(
        start_value=None,
        end_value=100,
        years=5,
    )

    assert result is None
    assert flag == INSUFFICIENT