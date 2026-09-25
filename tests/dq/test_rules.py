import numpy as np
import pandas as pd

from src.etl.validator import (
    dq01_pk_uniqueness,
    dq02_company_year_uniqueness,
    dq03_fk_integrity,
    dq04_balance_sheet_balance,
    dq05_opm_crosscheck,
    dq06_positive_sales,
    dq07_company_identifier,
    dq08_year_present,
    dq09_nonnegative_assets,
    dq10_balance_sheet_completeness,
    dq11_positive_price,
    dq12_ohlc_consistency,
    dq13_market_cap_positive,
    dq14_dividend_payout,
    dq15_sector_weight,
    dq16_eps_sanity,
)


def assert_rule(failures, rule_id, severity):
    assert len(failures) >= 1
    assert failures[0]["rule_id"] == rule_id
    assert failures[0]["severity"] == severity


def test_dq01_pk_uniqueness():
    df = pd.DataFrame(
        {
            "id": [1, 1],
            "company_id": ["C001", "C002"],
        }
    )

    failures = dq01_pk_uniqueness(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-01",
        "CRITICAL",
    )


def test_dq02_company_year_uniqueness():
    df = pd.DataFrame(
        {
            "company_id": ["C001", "C001"],
            "year": ["Mar 2024", "Mar 2024"],
        }
    )

    failures = dq02_company_year_uniqueness(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-02",
        "CRITICAL",
    )


def test_dq03_fk_integrity():
    df = pd.DataFrame(
        {
            "company_id": ["C999"],
            "year": ["Mar 2024"],
        }
    )

    companies_df = pd.DataFrame(
        {
            "id": ["C001"],
        }
    )

    failures = dq03_fk_integrity(
        df,
        companies_df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-03",
        "CRITICAL",
    )


def test_dq04_balance_sheet_balance():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "total_assets": [1000],
            "total_liabilities": [500],
            "total_equity": [100],
        }
    )

    failures = dq04_balance_sheet_balance(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-04",
        "CRITICAL",
    )


def test_dq05_opm_crosscheck():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "sales": [100],
            "operating_profit": [30],
            "opm_percentage": [35],
        }
    )

    failures = dq05_opm_crosscheck(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-05",
        "WARNING",
    )


def test_dq06_positive_sales():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "sales": [0],
        }
    )

    failures = dq06_positive_sales(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-06",
        "CRITICAL",
    )


def test_dq07_company_identifier():
    df = pd.DataFrame(
        {
            "company_id": [None],
            "year": ["Mar 2024"],
        }
    )

    failures = dq07_company_identifier(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-07",
        "CRITICAL",
    )


def test_dq08_year_present():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["not-a-year"],
        }
    )

    failures = dq08_year_present(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-08",
        "WARNING",
    )


def test_dq09_nonnegative_assets():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "total_assets": [-100],
        }
    )

    failures = dq09_nonnegative_assets(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-09",
        "WARNING",
    )


def test_dq10_balance_sheet_completeness():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "total_assets": [1000],
            "total_liabilities": [np.nan],
        }
    )

    failures = dq10_balance_sheet_completeness(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-10",
        "WARNING",
    )


def test_dq11_positive_price():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "date": ["2024-03-31"],
            "open_price": [0],
            "high_price": [10],
            "low_price": [9],
            "close_price": [9.5],
        }
    )

    failures = dq11_positive_price(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-11",
        "CRITICAL",
    )


def test_dq12_ohlc_consistency():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "date": ["2024-03-31"],
            "open_price": [20],
            "high_price": [10],
            "low_price": [15],
            "close_price": [18],
        }
    )

    failures = dq12_ohlc_consistency(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-12",
        "WARNING",
    )


def test_dq13_market_cap_positive():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "market_cap_crore": [0],
        }
    )

    failures = dq13_market_cap_positive(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-13",
        "WARNING",
    )


def test_dq14_dividend_payout():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "dividend_payout": [101],
        }
    )

    failures = dq14_dividend_payout(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-14",
        "WARNING",
    )


def test_dq15_sector_weight():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "index_weight_pct": [101],
        }
    )

    failures = dq15_sector_weight(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-15",
        "WARNING",
    )


def test_dq16_eps_sanity():
    df = pd.DataFrame(
        {
            "company_id": ["C001"],
            "year": ["Mar 2024"],
            "eps": [np.nan],
        }
    )

    failures = dq16_eps_sanity(
        df,
        "test.csv",
    )

    assert_rule(
        failures,
        "DQ-16",
        "WARNING",
    )
