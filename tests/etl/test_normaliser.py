"""Unit tests for N100 Excel normalisation utilities."""

from pathlib import Path

import pandas as pd
import pytest

from src.etl.normaliser import (
    normalize_columns,
    normalize_ticker,
    normalize_year,
    read_excel_normalized,
)


# ---------------------------------------------------------------------------
# normalize_year() — 20 tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Dec 2012", 2012),
        ("Mar 2014", 2014),
        ("Mar 2015", 2015),
        ("Mar-15", 2015),
        ("Mar-16", 2016),
        ("2020", 2020),
        ("2021", 2021),
        ("2022", 2022),
        ("2023", 2023),
        ("2024", 2024),
        (2024, 2024),
        (2024.0, 2024),
        ("FY 2020", 2020),
        ("FY2021", 2021),
        ("Year 2022", 2022),
        ("Apr/2019", 2019),
        ("31-03-2023", 2023),
        ("Jun 2018", 2018),
        ("Sep-19", 2019),
        ("Dec/2024", 2024),
    ],
)
def test_normalize_year_valid(value, expected):
    """Valid year/date formats should produce the expected year."""
    assert normalize_year(value) == expected


def test_normalize_year_none():
    """None should return None."""
    assert normalize_year(None) is None


def test_normalize_year_nan():
    """NaN should return None."""
    assert normalize_year(float("nan")) is None


def test_normalize_year_invalid_text():
    """Text without a year should return None."""
    assert normalize_year("not available") is None


# ---------------------------------------------------------------------------
# normalize_ticker() — 15 tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ABB", "ABB"),
        ("abb", "ABB"),
        (" Abb ", "ABB"),
        ("HDFCBANK", "HDFCBANK"),
        ("hdfcbank", "HDFCBANK"),
        (" TCS ", "TCS"),
        ("SBIN", "SBIN"),
        ("reliance", "RELIANCE"),
        ("INFY", "INFY"),
        ("  INFY  ", "INFY"),
        ("ADANIENT", "ADANIENT"),
        ("adaniensol", "ADANIENSOL"),
        (12345, "12345"),
        ("12345", "12345"),
        ("ABC-XYZ", "ABC-XYZ"),
    ],
)
def test_normalize_ticker_valid(value, expected):
    """Ticker values should be stripped and converted to uppercase."""
    assert normalize_ticker(value) == expected


def test_normalize_ticker_none():
    """None should return None."""
    assert normalize_ticker(None) is None


def test_normalize_ticker_nan():
    """NaN should return None."""
    assert normalize_ticker(float("nan")) is None


def test_normalize_ticker_blank():
    """Blank strings should return None."""
    assert normalize_ticker("   ") is None


# ---------------------------------------------------------------------------
# normalize_columns() tests
# ---------------------------------------------------------------------------


def test_normalize_columns():
    """Column names should become clean snake_case names."""
    columns = [
        "Company ID",
        "Profit & Loss",
        "ROE %",
        "Total Assets",
    ]

    result = normalize_columns(columns)

    assert result == [
        "company_id",
        "profit_loss",
        "roe",
        "total_assets",
    ]


def test_normalize_columns_strips_spaces():
    """Leading and trailing spaces should be removed."""
    assert normalize_columns(["  Company Name  "]) == ["company_name"]


# ---------------------------------------------------------------------------
# read_excel_normalized() tests
# ---------------------------------------------------------------------------


def test_read_excel_normalized_companies():
    """Companies workbook should load using its title-row structure."""
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root / "data" / "raw" / "companies.xlsx"

    df = read_excel_normalized(file_path)

    assert len(df) == 100
    assert "id" in df.columns
    assert "company_name" in df.columns
    assert df["id"].notna().all()


def test_read_excel_normalized_profit_loss():
    """Profit & Loss workbook should load with 1,276 records."""
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root / "data" / "raw" / "profitandloss.xlsx"

    df = read_excel_normalized(file_path)

    assert len(df) == 1276
    assert "company_id" in df.columns
    assert "year" in df.columns
    assert "sales" in df.columns


def test_read_excel_normalized_stock_prices():
    """Stock price workbook should load with 5,520 records."""
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root / "data" / "raw" / "stock_prices.xlsx"

    df = read_excel_normalized(file_path)

    assert len(df) == 5520
    assert "company_id" in df.columns
    assert "date" in df.columns
    assert "close_price" in df.columns


def test_read_excel_normalized_empty_rows_removed(tmp_path):
    """Completely empty rows should be removed."""
    file_path = tmp_path / "test.xlsx"

    source = pd.DataFrame(
        {
            "Company ID": ["ABC", None],
            "Year": ["2024", None],
        }
    )

    source.to_excel(file_path, index=False)

    df = read_excel_normalized(file_path)

    assert len(df) == 1
    assert df.iloc[0]["company_id"] == "ABC"


def test_read_excel_normalized_columns_cleaned(tmp_path):
    """Loaded columns should be normalized to snake_case."""
    file_path = tmp_path / "test.xlsx"

    source = pd.DataFrame(
        {
            "Company ID": ["ABC"],
            "Total Assets": [100],
        }
    )

    source.to_excel(file_path, index=False)

    df = read_excel_normalized(file_path)

    assert "company_id" in df.columns
    assert "total_assets" in df.columns