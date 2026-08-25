"""
N100 Financial Intelligence Platform
Data Quality Validator.

Validates the CLEAN processed CSV files produced by the ETL pipeline.

Implements DQ-01 through DQ-16 and writes validation failures
to output/validation_failures.csv.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# IMPORTANT:
# Validator checks CLEAN processed CSV files, not the original raw Excel.
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_DIR = PROJECT_ROOT / "output"

FAILURE_COLUMNS = [
    "rule_id",
    "rule_name",
    "severity",
    "file",
    "company_id",
    "year",
    "details",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def failure(
    rule_id: str,
    rule_name: str,
    severity: str,
    file_name: str,
    details: str,
    company_id: object = None,
    year: object = None,
) -> dict:
    """Create one validation-failure record."""
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "severity": severity,
        "file": file_name,
        "company_id": company_id,
        "year": year,
        "details": details,
    }


def load_excel(file_name: str) -> pd.DataFrame:
    """
    Load the CLEAN processed CSV corresponding to a source filename.

    Example:
        profitandloss.xlsx
    becomes:
        data/processed/profitandloss.csv
    """

    csv_name = Path(file_name).with_suffix(".csv").name
    csv_path = PROCESSED_DIR / csv_name

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {csv_path}"
        )

    return pd.read_csv(csv_path)


# ---------------------------------------------------------------------------
# DQ-01 — Primary-key uniqueness
# ---------------------------------------------------------------------------


def dq01_pk_uniqueness(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that the id column contains no duplicate primary keys."""

    failures = []

    if "id" not in df.columns:
        return failures

    duplicates = df[df["id"].duplicated(keep=False)]

    for _, row in duplicates.iterrows():
        failures.append(
            failure(
                "DQ-01",
                "Primary-key uniqueness",
                "CRITICAL",
                file_name,
                f"Duplicate id value: {row['id']}",
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-02 — Company/year uniqueness
# ---------------------------------------------------------------------------


def dq02_company_year_uniqueness(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check uniqueness of company_id and actual reporting period."""

    failures = []

    if not {"company_id", "year"}.issubset(df.columns):
        return failures

    check = df.copy()

    check["company_id"] = (
        check["company_id"].apply(normalize_ticker)
    )

    # Do NOT collapse Mar 2024 and Sep 2024 into the same year.
    check["reporting_period"] = (
        check["year"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    duplicates = check[
        check.duplicated(
            subset=["company_id", "reporting_period"],
            keep=False,
        )
    ]

    for _, row in duplicates.iterrows():
        failures.append(
            failure(
                "DQ-02",
                "(company_id, year) uniqueness",
                "CRITICAL",
                file_name,
                "Duplicate company/year combination",
                row["company_id"],
                row["reporting_period"],
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-03 — Foreign-key integrity
# ---------------------------------------------------------------------------


def dq03_fk_integrity(
    child_df: pd.DataFrame,
    companies_df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that every child company_id exists in companies."""

    failures = []

    if "company_id" not in child_df.columns:
        return failures

    if "id" not in companies_df.columns:
        return failures

    valid_companies = set(
        companies_df["id"]
        .dropna()
        .apply(normalize_ticker)
    )

    child_companies = (
        child_df["company_id"]
        .dropna()
        .apply(normalize_ticker)
    )

    invalid_mask = ~child_companies.isin(valid_companies)

    for index in child_df.index[invalid_mask]:
        row = child_df.loc[index]

        failures.append(
            failure(
                "DQ-03",
                "Foreign-key integrity",
                "CRITICAL",
                file_name,
                f"Unknown company_id: {row.get('company_id')}",
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-04 — Balance-sheet balance
# ---------------------------------------------------------------------------


def dq04_balance_sheet_balance(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that assets approximately equal liabilities."""

    failures = []

    required = {
        "total_assets",
        "total_liabilities",
    }

    if not required.issubset(df.columns):
        return failures

    check = df.copy()

    check["total_assets"] = pd.to_numeric(
        check["total_assets"],
        errors="coerce",
    )

    check["total_liabilities"] = pd.to_numeric(
        check["total_liabilities"],
        errors="coerce",
    )

    valid = check[
        check["total_assets"].notna()
        & check["total_liabilities"].notna()
        & (check["total_assets"] != 0)
    ].copy()

    valid["difference_pct"] = (
        (
            valid["total_assets"]
            - valid["total_liabilities"]
        ).abs()
        / valid["total_assets"].abs()
        * 100
    )

    invalid = valid[
        valid["difference_pct"] >= 1
    ]

    for _, row in invalid.iterrows():
        failures.append(
            failure(
                "DQ-04",
                "Balance-sheet balance",
                "CRITICAL",
                file_name,
                (
                    f"Assets={row['total_assets']}, "
                    f"Liabilities={row['total_liabilities']}, "
                    f"difference={row['difference_pct']:.2f}%"
                ),
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-05 — Operating-profit-margin cross-check
# ---------------------------------------------------------------------------


def dq05_opm_crosscheck(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check OPM against operating_profit / sales * 100."""

    failures = []

    required = {
        "sales",
        "operating_profit",
        "opm_percentage",
    }

    if not required.issubset(df.columns):
        return failures

    check = df.copy()

    for column in required:
        check[column] = pd.to_numeric(
            check[column],
            errors="coerce",
        )

    valid = check[
        check["sales"].notna()
        & check["operating_profit"].notna()
        & check["opm_percentage"].notna()
        & (check["sales"] != 0)
    ].copy()

    valid["calculated_opm"] = (
        valid["operating_profit"]
        / valid["sales"]
        * 100
    )

    invalid = valid[
        (
            valid["calculated_opm"]
            - valid["opm_percentage"]
        ).abs()
        > 1
    ]

    for _, row in invalid.iterrows():
        failures.append(
            failure(
                "DQ-05",
                "Operating-profit-margin cross-check",
                "WARNING",
                file_name,
                (
                    f"Reported OPM={row['opm_percentage']}, "
                    f"calculated OPM="
                    f"{row['calculated_opm']:.2f}"
                ),
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-06 — Positive sales
# ---------------------------------------------------------------------------


def dq06_positive_sales(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that sales values are positive."""

    failures = []

    if "sales" not in df.columns:
        return failures

    sales = pd.to_numeric(
        df["sales"],
        errors="coerce",
    )

    invalid = df[sales <= 0]

    for index in invalid.index:
        row = df.loc[index]

        failures.append(
            failure(
                "DQ-06",
                "Positive sales",
                "CRITICAL",
                file_name,
                f"Sales value is {sales.loc[index]}",
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-07 — Positive company identifiers
# ---------------------------------------------------------------------------


def dq07_company_identifier(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check for missing company identifiers."""

    failures = []

    if "company_id" not in df.columns:
        return failures

    invalid = df[
        df["company_id"].isna()
        | (
            df["company_id"]
            .astype(str)
            .str.strip()
            == ""
        )
    ]

    for index in invalid.index:
        failures.append(
            failure(
                "DQ-07",
                "Company identifier present",
                "CRITICAL",
                file_name,
                "Missing company_id",
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-08 — Year present
# ---------------------------------------------------------------------------


def dq08_year_present(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that financial records contain a valid year."""

    failures = []

    if "year" not in df.columns:
        return failures

    normalized = df["year"].apply(normalize_year)

    for index in df.index[normalized.isna()]:
        failures.append(
            failure(
                "DQ-08",
                "Valid year",
                "WARNING",
                file_name,
                (
                    "Unable to normalize year value: "
                    f"{df.loc[index, 'year']}"
                ),
                df.loc[index].get("company_id"),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-09 — Non-negative balance-sheet assets
# ---------------------------------------------------------------------------


def dq09_nonnegative_assets(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that total assets are not negative."""

    failures = []

    if "total_assets" not in df.columns:
        return failures

    values = pd.to_numeric(
        df["total_assets"],
        errors="coerce",
    )

    invalid = df[values < 0]

    for index in invalid.index:
        row = df.loc[index]

        failures.append(
            failure(
                "DQ-09",
                "Non-negative assets",
                "WARNING",
                file_name,
                (
                    f"Negative total assets: "
                    f"{values.loc[index]}"
                ),
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-10 — Balance-sheet completeness
# ---------------------------------------------------------------------------


def dq10_balance_sheet_completeness(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check required balance-sheet fields are populated."""

    failures = []

    required = [
        "total_liabilities",
        "total_assets",
    ]

    available = [
        column
        for column in required
        if column in df.columns
    ]

    if not available:
        return failures

    for column in available:
        invalid = df[df[column].isna()]

        for index in invalid.index:
            row = df.loc[index]

            failures.append(
                failure(
                    "DQ-10",
                    "Balance-sheet completeness",
                    "WARNING",
                    file_name,
                    f"Missing value in {column}",
                    row.get("company_id"),
                    normalize_year(row.get("year")),
                )
            )

    return failures


# ---------------------------------------------------------------------------
# DQ-11 — Positive price
# ---------------------------------------------------------------------------


def dq11_positive_price(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that stock prices are positive."""

    failures = []

    price_columns = [
        column
        for column in [
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "adjusted_close",
        ]
        if column in df.columns
    ]

    for column in price_columns:
        values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid = df[values <= 0]

        for index in invalid.index:
            row = df.loc[index]

            failures.append(
                failure(
                    "DQ-11",
                    "Positive stock price",
                    "CRITICAL",
                    file_name,
                    f"{column}={values.loc[index]}",
                    row.get("company_id"),
                    row.get("date"),
                )
            )

    return failures


# ---------------------------------------------------------------------------
# DQ-12 — OHLC consistency
# ---------------------------------------------------------------------------


def dq12_ohlc_consistency(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check basic OHLC price relationships."""

    failures = []

    required = {
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    }

    if not required.issubset(df.columns):
        return failures

    check = df.copy()

    for column in required:
        check[column] = pd.to_numeric(
            check[column],
            errors="coerce",
        )

    invalid = check[
        (check["high_price"] < check["low_price"])
        | (check["high_price"] < check["open_price"])
        | (check["high_price"] < check["close_price"])
        | (check["low_price"] > check["open_price"])
        | (check["low_price"] > check["close_price"])
    ]

    for _, row in invalid.iterrows():
        failures.append(
            failure(
                "DQ-12",
                "OHLC consistency",
                "WARNING",
                file_name,
                "OHLC relationship is inconsistent",
                row.get("company_id"),
                row.get("date"),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-13 — Market-cap positivity
# ---------------------------------------------------------------------------


def dq13_market_cap_positive(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check that market capitalization is positive."""

    failures = []

    if "market_cap_crore" not in df.columns:
        return failures

    values = pd.to_numeric(
        df["market_cap_crore"],
        errors="coerce",
    )

    invalid = df[values <= 0]

    for index in invalid.index:
        row = df.loc[index]

        failures.append(
            failure(
                "DQ-13",
                "Positive market capitalization",
                "WARNING",
                file_name,
                (
                    f"market_cap_crore="
                    f"{values.loc[index]}"
                ),
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-14 — Dividend payout range
# ---------------------------------------------------------------------------


def dq14_dividend_payout(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check dividend payout percentage is 0-100."""

    failures = []

    if "dividend_payout" in df.columns:
        column = "dividend_payout"
    elif "dividend_payout_ratio_pct" in df.columns:
        column = "dividend_payout_ratio_pct"
    else:
        return failures

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    invalid = df[
        (values < 0)
        | (values > 100)
    ]

    for index in invalid.index:
        row = df.loc[index]

        failures.append(
            failure(
                "DQ-14",
                "Dividend payout range",
                "WARNING",
                file_name,
                f"{column}={values.loc[index]}",
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-15 — Sector/index weight range
# ---------------------------------------------------------------------------


def dq15_sector_weight(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check index weight percentage is 0-100."""

    if "index_weight_pct" not in df.columns:
        return []

    failures = []

    values = pd.to_numeric(
        df["index_weight_pct"],
        errors="coerce",
    )

    invalid = df[
        (values < 0)
        | (values > 100)
    ]

    for index in invalid.index:
        row = df.loc[index]

        failures.append(
            failure(
                "DQ-15",
                "Index weight range",
                "WARNING",
                file_name,
                f"index_weight_pct={values.loc[index]}",
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# DQ-16 — EPS sanity check
# ---------------------------------------------------------------------------


def dq16_eps_sanity(
    df: pd.DataFrame,
    file_name: str,
) -> list[dict]:
    """Check for invalid EPS values."""

    failures = []

    if "eps" in df.columns:
        column = "eps"
    elif "earnings_per_share" in df.columns:
        column = "earnings_per_share"
    else:
        return failures

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    invalid_mask = (
        values.isna()
        | values.isin(
            [float("inf"), float("-inf")]
        )
    )

    for index in df.index[invalid_mask]:
        row = df.loc[index]

        failures.append(
            failure(
                "DQ-16",
                "EPS sanity check",
                "WARNING",
                file_name,
                f"Invalid EPS value: {row.get(column)}",
                row.get("company_id"),
                normalize_year(row.get("year")),
            )
        )

    return failures


# ---------------------------------------------------------------------------
# Validation runner
# ---------------------------------------------------------------------------


def validate_all() -> pd.DataFrame:
    """Run all applicable data-quality checks."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    failures: list[dict] = []

    # -----------------------------------------------------------------------
    # Companies
    # -----------------------------------------------------------------------

    companies = load_excel("companies.xlsx")

    failures.extend(
        dq01_pk_uniqueness(
            companies,
            "companies.xlsx",
        )
    )

    failures.extend(
        dq07_company_identifier(
            companies,
            "companies.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Profit & Loss
    # -----------------------------------------------------------------------

    pnl = load_excel("profitandloss.xlsx")

    failures.extend(
        dq01_pk_uniqueness(
            pnl,
            "profitandloss.xlsx",
        )
    )

    failures.extend(
        dq02_company_year_uniqueness(
            pnl,
            "profitandloss.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            pnl,
            companies,
            "profitandloss.xlsx",
        )
    )

    failures.extend(
        dq05_opm_crosscheck(
            pnl,
            "profitandloss.xlsx",
        )
    )

    failures.extend(
        dq06_positive_sales(
            pnl,
            "profitandloss.xlsx",
        )
    )

    failures.extend(
        dq07_company_identifier(
            pnl,
            "profitandloss.xlsx",
        )
    )

    failures.extend(
        dq08_year_present(
            pnl,
            "profitandloss.xlsx",
        )
    )

    failures.extend(
        dq14_dividend_payout(
            pnl,
            "profitandloss.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Balance Sheet
    # -----------------------------------------------------------------------

    balance_sheet = load_excel(
        "balancesheet.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            balance_sheet,
            "balancesheet.xlsx",
        )
    )

    failures.extend(
        dq02_company_year_uniqueness(
            balance_sheet,
            "balancesheet.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            balance_sheet,
            companies,
            "balancesheet.xlsx",
        )
    )

    failures.extend(
        dq04_balance_sheet_balance(
            balance_sheet,
            "balancesheet.xlsx",
        )
    )

    failures.extend(
        dq07_company_identifier(
            balance_sheet,
            "balancesheet.xlsx",
        )
    )

    failures.extend(
        dq08_year_present(
            balance_sheet,
            "balancesheet.xlsx",
        )
    )

    failures.extend(
        dq09_nonnegative_assets(
            balance_sheet,
            "balancesheet.xlsx",
        )
    )

    failures.extend(
        dq10_balance_sheet_completeness(
            balance_sheet,
            "balancesheet.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Cash Flow
    # -----------------------------------------------------------------------

    cashflow = load_excel(
        "cashflow.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            cashflow,
            "cashflow.xlsx",
        )
    )

    failures.extend(
        dq02_company_year_uniqueness(
            cashflow,
            "cashflow.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            cashflow,
            companies,
            "cashflow.xlsx",
        )
    )

    failures.extend(
        dq07_company_identifier(
            cashflow,
            "cashflow.xlsx",
        )
    )

    failures.extend(
        dq08_year_present(
            cashflow,
            "cashflow.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Stock Prices
    # -----------------------------------------------------------------------

    stock_prices = load_excel(
        "stock_prices.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            stock_prices,
            "stock_prices.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            stock_prices,
            companies,
            "stock_prices.xlsx",
        )
    )

    failures.extend(
        dq07_company_identifier(
            stock_prices,
            "stock_prices.xlsx",
        )
    )

    failures.extend(
        dq11_positive_price(
            stock_prices,
            "stock_prices.xlsx",
        )
    )

    failures.extend(
        dq12_ohlc_consistency(
            stock_prices,
            "stock_prices.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Market Cap
    # -----------------------------------------------------------------------

    market_cap = load_excel(
        "market_cap.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            market_cap,
            "market_cap.xlsx",
        )
    )

    failures.extend(
        dq02_company_year_uniqueness(
            market_cap,
            "market_cap.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            market_cap,
            companies,
            "market_cap.xlsx",
        )
    )

    failures.extend(
        dq13_market_cap_positive(
            market_cap,
            "market_cap.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Financial Ratios
    # -----------------------------------------------------------------------

    ratios = load_excel(
        "financial_ratios.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            ratios,
            "financial_ratios.xlsx",
        )
    )

    failures.extend(
        dq02_company_year_uniqueness(
            ratios,
            "financial_ratios.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            ratios,
            companies,
            "financial_ratios.xlsx",
        )
    )

    failures.extend(
        dq14_dividend_payout(
            ratios,
            "financial_ratios.xlsx",
        )
    )

    failures.extend(
        dq16_eps_sanity(
            ratios,
            "financial_ratios.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Sectors
    # -----------------------------------------------------------------------

    sectors = load_excel(
        "sectors.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            sectors,
            "sectors.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            sectors,
            companies,
            "sectors.xlsx",
        )
    )

    failures.extend(
        dq15_sector_weight(
            sectors,
            "sectors.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Peer Groups
    # -----------------------------------------------------------------------

    peers = load_excel(
        "peer_groups.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            peers,
            "peer_groups.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            peers,
            companies,
            "peer_groups.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Documents
    # -----------------------------------------------------------------------

    documents = load_excel(
        "documents.xlsx"
    )

    failures.extend(
        dq01_pk_uniqueness(
            documents,
            "documents.xlsx",
        )
    )

    failures.extend(
        dq03_fk_integrity(
            documents,
            companies,
            "documents.xlsx",
        )
    )

    # -----------------------------------------------------------------------
    # Final report
    # -----------------------------------------------------------------------

    result = pd.DataFrame(
        failures,
        columns=FAILURE_COLUMNS,
    )

    output_file = (
        OUTPUT_DIR
        / "validation_failures.csv"
    )

    result.to_csv(
        output_file,
        index=False,
    )

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run validation and print summary."""

    print(
        "Running N100 data-quality validation..."
    )

    result = validate_all()

    print(
        "Validation completed."
    )

    print(
        f"Total failures: {len(result)}"
    )

    if result.empty:
        print(
            "No validation failures found."
        )
        return

    print(
        "\nFailures by severity:"
    )

    print(
        result["severity"].value_counts()
    )

    print(
        "\nFailures by rule:"
    )

    print(
        result["rule_id"].value_counts()
    )

    print(
        "\nReport saved to: "
        f"{OUTPUT_DIR / 'validation_failures.csv'}"
    )


if __name__ == "__main__":
    main()