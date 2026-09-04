"""
Sprint 3 - Day 15
Screener Filter Engine

Loads the latest available financial data and applies configurable
threshold filters to the Nifty 100 universe.

Day 17 composite quality score:
    35% Profitability
    30% Cash Quality
    20% Growth
    15% Leverage

Each component metric is winsorised using P10/P90 and scaled to 0-100.
Scores are calculated relative to broad_sector.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "screener_config.yaml"


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_year(value: Any) -> int | None:
    """Extract a four-digit year from values such as 'Mar 2024'."""

    if pd.isna(value):
        return None

    import re

    match = re.search(r"(\d{4})", str(value))

    if match is None:
        return None

    return int(match.group(1))


def load_config(
    path: str | Path = DEFAULT_CONFIG,
) -> dict:
    """Load screener configuration from YAML."""

    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _latest_pnl(
    pnl: pd.DataFrame,
) -> pd.DataFrame:
    """Keep the latest annual P&L row per company."""

    data = pnl.copy()

    data["_year_num"] = data["year"].apply(
        normalize_year
    )

    data = data[
        data["_year_num"].notna()
    ].copy()

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


# ============================================================
# P10 / P90 NORMALISATION
# ============================================================

def _winsor_scale_series(
    series: pd.Series,
    higher_is_better: bool = True,
) -> pd.Series:
    """
    Winsorise a series at P10/P90 and scale to 0-100.

    If all valid values are equal, return 50 for those values.
    Missing values remain missing.
    """

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    result = pd.Series(
        float("nan"),
        index=series.index,
        dtype="float64",
    )

    valid = values.notna()

    if not valid.any():
        return result

    clean = values[valid].copy()

    clean = clean.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    ).dropna()

    if clean.empty:
        return result

    p10 = clean.quantile(0.10)
    p90 = clean.quantile(0.90)

    if p10 == p90:
        result.loc[clean.index] = 50.0
        return result

    clipped = clean.clip(
        lower=p10,
        upper=p90,
    )

    scaled = (
        (clipped - p10)
        / (p90 - p10)
    ) * 100

    if not higher_is_better:
        scaled = 100 - scaled

    result.loc[scaled.index] = scaled

    return result
    clean = values[valid].copy()

    # Infinity is valid conceptually for ICR, but percentile
    # calculations cannot use it directly.
    clean = clean.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    ).dropna()

    if clean.empty:
        result.loc[valid] = 50.0
        return result

    p10 = float(clean.quantile(0.10))
    p90 = float(clean.quantile(0.90))

    if p90 == p10:
        result.loc[valid] = 50.0
        return result

    clipped = values.clip(
        lower=p10,
        upper=p90,
    )

    scaled = (
        (clipped - p10)
        / (p90 - p10)
        * 100.0
    )

    if not higher_is_better:
        scaled = 100.0 - scaled

    result.loc[valid] = scaled.loc[valid]

    return result


def _sector_relative_score(
    df: pd.DataFrame,
    column: str,
    higher_is_better: bool = True,
) -> pd.Series:
    """
    Calculate a sector-relative 0-100 score for one metric.

    Higher values are better by default.
    For inverse metrics such as D/E, lower values receive higher scores.
    """
    values = pd.to_numeric(df[column], errors="coerce")
    result = pd.Series(50.0, index=df.index, dtype=float)

    valid = values.notna()

    if not valid.any():
        return result

    working = pd.DataFrame(
        {
            "value": values,
            "sector": df["broad_sector"].fillna("Unknown"),
        },
        index=df.index,
    )

    def score_group(group: pd.DataFrame) -> pd.Series:
        vals = group["value"]

        if len(vals) == 1:
            return pd.Series(50.0, index=group.index)

        if higher_is_better:
            scores = vals.rank(method="average", pct=True) * 100
        else:
            scores = vals.rank(method="average", pct=True, ascending=False) * 100

        return scores

    scored = working.loc[valid].groupby(
        "sector",
        group_keys=False,
    ).apply(score_group)

    result.loc[scored.index] = scored.astype(float)

    return result.clip(0, 100)# ============================================================
# COMPOSITE QUALITY SCORE
# ============================================================

def _calculate_fcf_cagr(
    ratios: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate 5-year FCF CAGR from financial_ratios.

    Uses the latest available annual observation and the
    observation five years earlier.

    CAGR is only calculated when both values are positive.
    """

    data = ratios[
        [
            "company_id",
            "year",
            "free_cash_flow_cr",
        ]
    ].copy()

    data["_year_num"] = data["year"].apply(
        normalize_year
    )

    data["free_cash_flow_cr"] = pd.to_numeric(
        data["free_cash_flow_cr"],
        errors="coerce",
    )

    data = data[
        data["_year_num"].notna()
    ].copy()

    data = (
        data.sort_values(
            ["company_id", "_year_num"]
        )
        .drop_duplicates(
            subset=[
                "company_id",
                "_year_num",
            ],
            keep="last",
        )
    )

    records = []

    for company_id, group in data.groupby(
        "company_id"
    ):

        group = group.sort_values(
            "_year_num"
        )

        latest_year = int(
            group["_year_num"].max()
        )

        latest = group[
            group["_year_num"] == latest_year
        ]

        previous = group[
            group["_year_num"]
            == latest_year - 5
        ]

        fcf_cagr = pd.NA

        if (
            not latest.empty
            and not previous.empty
        ):

            end_value = latest[
                "free_cash_flow_cr"
            ].iloc[-1]

            start_value = previous[
                "free_cash_flow_cr"
            ].iloc[-1]

            if (
                pd.notna(start_value)
                and pd.notna(end_value)
                and float(start_value) > 0
                and float(end_value) > 0
            ):
                fcf_cagr = (
                    (
                        float(end_value)
                        / float(start_value)
                    )
                    ** (1 / 5)
                    - 1
                ) * 100.0

        records.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": fcf_cagr,
            }
        )

    return pd.DataFrame(records)


def _add_composite_quality_score(
    result: pd.DataFrame,
    ratios_history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add the required 0-100 sector-relative composite score.

    Profitability: 35%
        ROE 15%
        ROCE 10%
        NPM 10%

    Cash Quality: 30%
        FCF CAGR 15%
        CFO/PAT 10%
        FCF positive flag 5%

    Growth: 20%
        Revenue CAGR 10%
        PAT CAGR 10%

    Leverage: 15%
        D/E score 10%
        ICR score 5%
    """

    df = result.copy()

    # --------------------------------------------------------
    # ROCE
    # --------------------------------------------------------

    companies_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "companies.csv"
    )

    if companies_path.exists():

        companies = pd.read_csv(
            companies_path
        )

        company_columns = [
            "id",
            "roce_percentage",
        ]

        if all(
            c in companies.columns
            for c in company_columns
        ):

            roce = companies[
                company_columns
            ].copy()

            roce = roce.rename(
                columns={
                    "id": "company_id",
                    "roce_percentage": "roce",
                }
            )

            df = df.merge(
                roce,
                on="company_id",
                how="left",
            )

        else:
            df["roce"] = pd.NA

    else:
        df["roce"] = pd.NA

    # --------------------------------------------------------
    # CFO / PAT
    # --------------------------------------------------------

    df["cfo_pat_ratio"] = pd.NA

    cfo = pd.to_numeric(
        df["cash_from_operations_cr"],
        errors="coerce",
    )

    pat = pd.to_numeric(
        df["net_profit"],
        errors="coerce",
    )

    valid_pat = (
        pat.notna()
        & (pat != 0)
    )

    df.loc[
        valid_pat,
        "cfo_pat_ratio",
    ] = (
        cfo[valid_pat]
        / pat[valid_pat]
    )

    # --------------------------------------------------------
    # FCF CAGR
    # --------------------------------------------------------

    fcf_cagr = _calculate_fcf_cagr(
        ratios_history
    )

    df = df.merge(
        fcf_cagr,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # FCF positive flag
    # --------------------------------------------------------

    df["fcf_positive_flag"] = (
        pd.to_numeric(
            df["fcf"],
            errors="coerce",
        ) > 0
    ).astype(float) * 100.0

    # --------------------------------------------------------
    # ICR handling
    # --------------------------------------------------------

    # Debt-free companies are treated as infinite ICR.
    # They therefore receive the maximum ICR score.
    df["icr_score_input"] = pd.to_numeric(
        df["icr"],
        errors="coerce",
    )

    debt_free = (
        pd.to_numeric(
            df["de"],
            errors="coerce",
        )
        == 0
    )

    df.loc[
        debt_free,
        "icr_score_input",
    ] = float("inf")

    # --------------------------------------------------------
    # Sector-relative metric scores
    # --------------------------------------------------------

    df["score_roe"] = _sector_relative_score(
        df,
        "roe",
        higher_is_better=True,
    )

    df["score_roce"] = _sector_relative_score(
        df,
        "roce",
        higher_is_better=True,
    )

    df["score_npm"] = _sector_relative_score(
        df,
        "net_profit_margin_pct",
        higher_is_better=True,
    )

    df["score_fcf_cagr"] = _sector_relative_score(
        df,
        "fcf_cagr_5yr",
        higher_is_better=True,
    )

    df["score_cfo_pat"] = _sector_relative_score(
        df,
        "cfo_pat_ratio",
        higher_is_better=True,
    )

    df["score_revenue_cagr"] = _sector_relative_score(
        df,
        "revenue_cagr_5yr",
        higher_is_better=True,
    )

    df["score_pat_cagr"] = _sector_relative_score(
        df,
        "pat_cagr_5yr",
        higher_is_better=True,
    )

    # D/E: lower is better.
    df["score_de"] = _sector_relative_score(
        df,
        "de",
        higher_is_better=False,
    )

    # ICR: higher is better.
    df["score_icr"] = _sector_relative_score(
        df,
        "icr_score_input",
        higher_is_better=True,
    )

    # --------------------------------------------------------
    # Weighted score
    # --------------------------------------------------------

    weighted_columns = [
        ("score_roe", 15.0),
        ("score_roce", 10.0),
        ("score_npm", 10.0),

        ("score_fcf_cagr", 15.0),
        ("score_cfo_pat", 10.0),
        ("fcf_positive_flag", 5.0),

        ("score_revenue_cagr", 10.0),
        ("score_pat_cagr", 10.0),

        ("score_de", 10.0),
        ("score_icr", 5.0),
    ]

    numerator = pd.Series(
        0.0,
        index=df.index,
    )

    denominator = pd.Series(
        0.0,
        index=df.index,
    )

    for column, weight in weighted_columns:

        values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        valid = values.notna()

        numerator.loc[valid] += (
            values.loc[valid]
            * weight
        )

        denominator.loc[valid] += weight

    # Renormalise available weights so missing metrics
    # cannot push the score outside 0-100.
    df["composite_quality_score"] = (
        numerator
        / denominator
    )

    df.loc[
        denominator == 0,
        "composite_quality_score",
    ] = 0.0

    # Numerical safety.
    df["composite_quality_score"] = (
        pd.to_numeric(
            df["composite_quality_score"],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(0.0, 100.0)
    )

    return df


# ============================================================
# BUILD SCREENER DATAFRAME
# ============================================================

def build_screener_dataframe(
    db_path: str | Path = "data/db/n100.db",
) -> pd.DataFrame:
    """
    Build the unified latest-year screener dataset.
    """

    import sqlite3

    db_path = Path(db_path)

    db = sqlite3.connect(
        db_path
    )

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        db,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector
        FROM sectors
        """,
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

    ratios_history = ratios.copy()

    # --------------------------------------------------------
    # Normalize years
    # --------------------------------------------------------

    ratios["_year_num"] = ratios[
        "year"
    ].apply(normalize_year)

    pnl["_year_num"] = pnl[
        "year"
    ].apply(normalize_year)

    market_cap["_year_num"] = market_cap[
        "year"
    ].apply(normalize_year)

    # --------------------------------------------------------
    # Latest ratio row per company
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Latest annual P&L
    # --------------------------------------------------------

    pnl = _latest_pnl(
        pnl
    )

    pnl = (
        pnl.sort_values(
            ["company_id", "_year_num"]
        )
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    # --------------------------------------------------------
    # Latest market cap
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Standardised screener names
    # --------------------------------------------------------

    result["roe"] = result[
        "return_on_equity_pct"
    ]

    result["de"] = result[
        "debt_to_equity"
    ]

    result["fcf"] = result[
        "free_cash_flow_cr"
    ]

    result["opm"] = result[
        "operating_profit_margin_pct"
    ]

    result["pe"] = result[
        "pe_ratio"
    ]

    result["pb"] = result[
        "pb_ratio"
    ]

    result["dividend_yield"] = result[
        "dividend_yield_pct"
    ]

    result["icr"] = result[
        "interest_coverage"
    ]

    result["market_cap"] = result[
        "market_cap_crore"
    ]

    result["eps_cagr"] = result[
        "eps_cagr_5yr"
    ]

    result["asset_turnover"] = result[
        "asset_turnover"
    ]

    result["sales"] = result[
        "sales"
    ]

    # --------------------------------------------------------
    # Debt-free companies behave as infinite ICR.
    # --------------------------------------------------------

    result["icr_screener"] = result[
        "icr"
    ].fillna(float("inf"))

    # --------------------------------------------------------
    # Recalculate composite score correctly.
    # --------------------------------------------------------

    result = _add_composite_quality_score(
        result,
        ratios_history,
    )

    return result.reset_index(
        drop=True
    )


# ============================================================
# FILTER HELPERS
# ============================================================

def _apply_min(
    df: pd.DataFrame,
    column: str,
    threshold: Any,
) -> pd.DataFrame:
    """Apply a minimum threshold."""

    if threshold is None:
        return df

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    return df[
        values.notna()
        & (
            values
            >= float(threshold)
        )
    ]


def _apply_max(
    df: pd.DataFrame,
    column: str,
    threshold: Any,
) -> pd.DataFrame:
    """Apply a maximum threshold."""

    if threshold is None:
        return df

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    return df[
        values.notna()
        & (
            values
            <= float(threshold)
        )
    ]


# ============================================================
# APPLY SCREENER FILTERS
# ============================================================

def apply_filters(
    df: pd.DataFrame,
    filters: dict[str, Any],
    skip_financials_for_de: bool = True,
) -> pd.DataFrame:
    """
    Apply all supported screener thresholds.
    """

    result = df.copy()

    # --------------------------------------------------------
    # Minimum filters
    # --------------------------------------------------------

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
            filters.get(
                threshold_name
            ),
        )

    # --------------------------------------------------------
    # Dividend payout maximum
    # --------------------------------------------------------

    dividend_payout_max = filters.get(
        "dividend_payout_max"
    )

    if dividend_payout_max is not None:

        values = pd.to_numeric(
            result[
                "dividend_payout_ratio_pct"
            ],
            errors="coerce",
        )

        result = result[
            values.notna()
            & (
                values
                < float(
                    dividend_payout_max
                )
            )
        ]

    # --------------------------------------------------------
    # P/E maximum
    # --------------------------------------------------------

    result = _apply_max(
        result,
        "pe",
        filters.get(
            "pe_max"
        ),
    )

    # --------------------------------------------------------
    # P/B maximum
    # --------------------------------------------------------

    result = _apply_max(
        result,
        "pb",
        filters.get(
            "pb_max"
        ),
    )

    # --------------------------------------------------------
    # Exact D/E
    # --------------------------------------------------------

    de_exact = filters.get(
        "de_exact"
    )

    if de_exact is not None:

        values = pd.to_numeric(
            result["de"],
            errors="coerce",
        )

        result = result[
            values.notna()
            & (
                values
                == float(de_exact)
            )
        ]

    # --------------------------------------------------------
    # D/E maximum
    #
    # Financials are automatically excluded from the D/E
    # filter when requested.
    # --------------------------------------------------------

    de_max = filters.get(
        "de_max"
    )

    if de_max is not None:

        if skip_financials_for_de:

            sector = (
                result[
                    "broad_sector"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            non_financials = result[
                sector != "financials"
            ]

            financials = result[
                sector == "financials"
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

    # --------------------------------------------------------
    # ICR minimum
    #
    # Debt-free companies have infinity and always pass.
    # --------------------------------------------------------

    icr_min = filters.get(
        "icr_min"
    )

    if icr_min is not None:

        result = result[
            result[
                "icr_screener"
            ]
            >= float(icr_min)
        ]

    # --------------------------------------------------------
    # Sort by composite quality score
    # --------------------------------------------------------

    if (
        "composite_quality_score"
        in result.columns
    ):

        result = result.sort_values(
            "composite_quality_score",
            ascending=False,
        )

    return result.reset_index(
        drop=True
    )


# ============================================================
# PUBLIC SCREENER API
# ============================================================

def run_screener(
    filters: dict[str, Any],
    db_path: str | Path = "data/db/n100.db",
) -> pd.DataFrame:
    """
    Build the screener dataset and apply filters.
    """

    config = load_config()

    options = config.get(
        "options",
        {},
    )

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


# ============================================================
# DAY 15 CHECK
# ============================================================

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

    print()

    print(
        "Composite score range: "
        f"{df['composite_quality_score'].min():.2f}"
        " - "
        f"{df['composite_quality_score'].max():.2f}"
    )

    print(
        "Scores above 100: "
        f"{(df['composite_quality_score'] > 100).sum()}"
    )