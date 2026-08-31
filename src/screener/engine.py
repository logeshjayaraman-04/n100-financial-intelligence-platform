git add src/screener/presets.py"""
Sprint 3 - Day 15
Screener Filter Engine

Loads the latest available financial data and applies configurable
threshold filters to the Nifty 100 universe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "screener_config.yaml"


def normalize_year(value: Any) -> int | None:
    """Extract a four-digit year from values such as 'Mar 2024'."""
    if pd.isna(value):
        return None

    import re

    match = re.search(r"(\d{4})", str(value))

    if match is None:
        return None

    return int(match.group(1))


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    """Load screener configuration from YAML."""
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _latest_pnl(pnl: pd.DataFrame) -> pd.DataFrame:
    """Keep the latest non-TTM annual P&L row per company."""

    data = pnl.copy()

    data["_year_num"] = data["year"].apply(normalize_year)
    data = data[data["_year_num"].notna()].copy()

    data["_is_ttm"] = (
        data["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    )

    data = data.sort_values(
        ["company_id", "_year_num", "_is_ttm"]
    )

    return (
        data.drop_duplicates(
            subset=["company_id", "_year_num"],
            keep="first",
        )
        .reset_index(drop=True)
    )


def build_screener_dataframe(
    db_path: str | Path = "data/db/n100.db",
) -> pd.DataFrame:
    """
    Build the unified latest-year screener dataset.
    """

    import sqlite3

    db_path = Path(db_path)
    db = sqlite3.connect(db_path)

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        db,
    )

    sectors = pd.read_sql_query(
        "SELECT company_id, broad_sector FROM sectors",
        db,
    )

    pnl = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            eps,
            dividend_payout
        FROM profitandloss
        """,
        db,
    )

    market_cap = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            market_cap_crore,
            pe_ratio,
            pb_ratio,
            dividend_yield_pct
        FROM market_cap
        """,
        db,
    )

    db.close()

    # Normalize years
    ratios["_year_num"] = ratios["year"].apply(normalize_year)
    pnl["_year_num"] = pnl["year"].apply(normalize_year)
    market_cap["_year_num"] = market_cap["year"].apply(normalize_year)

    # Latest ratio row per company
    ratios = ratios[
        ratios["_year_num"].notna()
    ].copy()

    ratios = (
        ratios.sort_values(
            ["company_id", "_year_num"]
        )
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    # Latest annual P&L
    pnl = _latest_pnl(pnl)

    pnl = (
        pnl.sort_values(
            ["company_id", "_year_num"]
        )
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    # Latest market-cap row
    market_cap = (
        market_cap[
            market_cap["_year_num"].notna()
        ]
        .sort_values(
            ["company_id", "_year_num"]
        )
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    # Merge
    result = ratios.merge(
        pnl[
            [
                "company_id",
                "sales",
                "net_profit",
                "eps",
                "dividend_payout",
            ]
        ],
        on="company_id",
        how="left",
    )

    result = result.merge(
        market_cap[
            [
                "company_id",
                "market_cap_crore",
                "pe_ratio",
                "pb_ratio",
                "dividend_yield_pct",
            ]
        ],
        on="company_id",
        how="left",
    )

    result = result.merge(
        sectors,
        on="company_id",
        how="left",
    )

    # Standardized screener names
    result["roe"] = result["return_on_equity_pct"]
    result["de"] = result["debt_to_equity"]
    result["fcf"] = result["free_cash_flow_cr"]
    result["revenue_cagr_5yr"] = result["revenue_cagr_5yr"]
    result["pat_cagr_5yr"] = result["pat_cagr_5yr"]
    result["opm"] = result["operating_profit_margin_pct"]
    result["pe"] = result["pe_ratio"]
    result["pb"] = result["pb_ratio"]
    result["dividend_yield"] = result["dividend_yield_pct"]
    result["icr"] = result["interest_coverage"]
    result["market_cap"] = result["market_cap_crore"]
    result["net_profit"] = result["net_profit"]
    result["eps_cagr"] = result["eps_cagr_5yr"]
    result["asset_turnover"] = result["asset_turnover"]
    result["sales"] = result["sales"]

    # Debt-free companies behave as infinite ICR.
    result["icr_screener"] = result["icr"].fillna(float("inf"))

    return result.reset_index(drop=True)


def _apply_min(
    df: pd.DataFrame,
    column: str,
    threshold: Any,
) -> pd.DataFrame:
    """Apply a minimum threshold."""

    if threshold is None:
        return df

    return df[
        df[column].notna()
        & (df[column] >= float(threshold))
    ]


def _apply_max(
    df: pd.DataFrame,
    column: str,
    threshold: Any,
) -> pd.DataFrame:
    """Apply a maximum threshold."""

    if threshold is None:
        return df

    return df[
        df[column].notna()
        & (df[column] <= float(threshold))
    ]


def apply_filters(
    df: pd.DataFrame,
    filters: dict[str, Any],
    skip_financials_for_de: bool = True,
) -> pd.DataFrame:
    """
    Apply all supported screener thresholds.
    """

    result = df.copy()

    # Minimum filters
    minimum_filters = {
        "roe_min": "roe",
        "fcf_min": "fcf",
        "revenue_cagr_5yr_min": "revenue_cagr_5yr",
        "pat_cagr_5yr_min": "pat_cagr_5yr",
        "opm_min": "opm",
        "market_cap_min": "market_cap",
        "net_profit_min": "net_profit",
        "eps_cagr_min": "eps_cagr",
        "asset_turnover_min": "asset_turnover",
        "sales_min": "sales",
        "dividend_yield_min": "dividend_yield",
    }

    for threshold_name, column in minimum_filters.items():
        result = _apply_min(
            result,
            column,
            filters.get(threshold_name),
        )

    # Dividend payout maximum
    dividend_payout_max = filters.get(
        "dividend_payout_max"
    )

    if dividend_payout_max is not None:
        result = result[
            result["dividend_payout_ratio_pct"].notna()
            & (
                result["dividend_payout_ratio_pct"]
                < float(dividend_payout_max)
            )
        ]

    # Maximum filters
    result = _apply_max(
        result,
        "pe",
        filters.get("pe_max"),
    )

    result = _apply_max(
        result,
        "pb",
        filters.get("pb_max"),
    )

    # Exact D/E filter
    de_exact = filters.get("de_exact")

    if de_exact is not None:
        result = result[
            result["de"].notna()
            & (
                result["de"] == float(de_exact)
            )
        ]

    # D/E maximum with Financials carve-out
    de_max = filters.get("de_max")

    if de_max is not None:

        if skip_financials_for_de:

            non_financials = result[
                result["broad_sector"]
                .fillna("")
                .str.strip()
                .str.lower()
                != "financials"
            ]

            financials = result[
                result["broad_sector"]
                .fillna("")
                .str.strip()
                .str.lower()
                == "financials"
            ]

            non_financials = _apply_max(
                non_financials,
                "de",
                de_max,
            )

            result = pd.concat(
                [
                    non_financials,
                    financials,
                ],
                ignore_index=True,
            )

        else:
            result = _apply_max(
                result,
                "de",
                de_max,
            )

    # ICR
    icr_min = filters.get("icr_min")

    if icr_min is not None:
        result = result[
            result["icr_screener"]
            >= float(icr_min)
        ]

    # Sort by composite quality score
    if "composite_quality_score" in result.columns:
        result = result.sort_values(
            "composite_quality_score",
            ascending=False,
        )

    return result.reset_index(drop=True)


def run_screener(
    filters: dict[str, Any],
    db_path: str | Path = "data/db/n100.db",
) -> pd.DataFrame:
    """
    Build the screener dataset and apply filters.
    """

    config = load_config()

    options = config.get("options", {})

    df = build_screener_dataframe(
        db_path=db_path,
    )

    return apply_filters(
        df,
        filters,
        skip_financials_for_de=options.get(
            "skip_financials_for_de",
            True,
        ),
    )


if __name__ == "__main__":

    config = load_config()

    df = build_screener_dataframe()

    print("=" * 80)
    print("DAY 15 — SCREENER ENGINE CHECK")
    print("=" * 80)

    print(
        f"Companies available: "
        f"{df['company_id'].nunique()}"
    )

    print(
        f"Rows available: "
        f"{len(df)}"
    )

    print()
    print("Filterable metrics:")

    print(
        [
            "ROE",
            "D/E",
            "FCF",
            "Revenue CAGR 5yr",
            "PAT CAGR 5yr",
            "OPM",
            "P/E",
            "P/B",
            "Dividend Yield",
            "ICR",
            "Market Cap",
            "Net Profit",
            "EPS CAGR",
            "Asset Turnover",
            "Sales",
        ]
    )