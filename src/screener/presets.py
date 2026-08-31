"""
Sprint 3 - Day 16
Six preset screener definitions.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .engine import (
    build_screener_dataframe,
    apply_filters,
)


# ============================================================
# DAY 16 — PRESET DEFINITIONS
# ============================================================

PRESETS = {
    "Quality Compounder": {
        "roe_min": 15,
        "de_max": 1.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 10,
    },

    "Value Pick": {
        "pe_max": 20,
        "pb_max": 3.0,
        "de_max": 2.0,
        "dividend_yield_min": 1,
    },

    "Growth Accelerator": {
        "pat_cagr_5yr_min": 20,
        "revenue_cagr_5yr_min": 15,
        "de_max": 2.0,
    },

    "Dividend Champion": {
        "dividend_yield_min": 2,
        "dividend_payout_max": 80,
        "fcf_min": 0,
    },

    "Debt-Free Blue Chip": {
        "de_exact": 0,
        "roe_min": 12,
        "sales_min": 5000,
    },
}


# ============================================================
# RUN ONE OF THE FIVE STANDARD PRESETS
# ============================================================

def run_preset(
    name: str,
    db_path: str | Path = "data/db/n100.db",
) -> pd.DataFrame:
    """Run one named preset."""

    if name not in PRESETS:
        raise ValueError(
            f"Unknown preset: {name}. "
            f"Available: {list(PRESETS)}"
        )

    df = build_screener_dataframe(db_path)

    return apply_filters(
        df,
        PRESETS[name],
        skip_financials_for_de=True,
    )


# ============================================================
# DAY 16 — TURNAROUND WATCH
# ============================================================

def run_turnaround_watch(
    db_path: str | Path = "data/db/n100.db",
) -> pd.DataFrame:
    """
    Turnaround Watch conditions:

    1. Revenue CAGR 3yr > 10%
    2. Latest-year FCF > 0
    3. D/E declining year-over-year
    """

    import sqlite3

    db_path = Path(db_path)

    db = sqlite3.connect(db_path)

    # --------------------------------------------------------
    # Load P&L
    # --------------------------------------------------------

    pnl = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales
        FROM profitandloss
        """,
        db,
    )

    # --------------------------------------------------------
    # Load Balance Sheet
    # --------------------------------------------------------

    balance = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            equity_capital,
            reserves,
            borrowings
        FROM balancesheet
        """,
        db,
    )

    # --------------------------------------------------------
    # Load Financial Ratios
    # --------------------------------------------------------

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            free_cash_flow_cr,
            debt_to_equity
        FROM financial_ratios
        """,
        db,
    )

    db.close()

    # ========================================================
    # NORMALIZE YEARS
    # ========================================================

    for df in [pnl, balance, ratios]:

        df["_year_num"] = pd.to_numeric(
            df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce",
        )

    pnl = pnl.dropna(
        subset=["_year_num"]
    ).copy()

    balance = balance.dropna(
        subset=["_year_num"]
    ).copy()

    ratios = ratios.dropna(
        subset=["_year_num"]
    ).copy()

    # ========================================================
    # 1. CALCULATE 3-YEAR REVENUE CAGR
    # ========================================================

    revenue_results = []

    for company_id, group in pnl.groupby(
        "company_id"
    ):

        group = (
            group
            .sort_values("_year_num")
            .drop_duplicates(
                subset=["_year_num"],
                keep="last",
            )
        )

        group["sales"] = pd.to_numeric(
            group["sales"],
            errors="coerce",
        )

        values = dict(
            zip(
                group["_year_num"].astype(int),
                group["sales"],
            )
        )

        latest_year = int(
            group["_year_num"].max()
        )

        start_year = latest_year - 3

        start_sales = values.get(
            start_year
        )

        end_sales = values.get(
            latest_year
        )

        revenue_cagr_3yr = None

        if (
            start_sales is not None
            and end_sales is not None
            and pd.notna(start_sales)
            and pd.notna(end_sales)
            and float(start_sales) > 0
            and float(end_sales) > 0
        ):

            revenue_cagr_3yr = (
                (
                    float(end_sales)
                    / float(start_sales)
                )
                ** (1 / 3)
                - 1
            ) * 100

        revenue_results.append(
            {
                "company_id": company_id,
                "latest_year": latest_year,
                "revenue_cagr_3yr": revenue_cagr_3yr,
            }
        )

    revenue_df = pd.DataFrame(
        revenue_results
    )

    # ========================================================
    # 2. GET LATEST FCF
    # ========================================================

    ratios = (
        ratios
        .sort_values(
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

    latest_ratios = (
        ratios
        .sort_values(
            ["company_id", "_year_num"]
        )
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    latest_ratios = latest_ratios[
        [
            "company_id",
            "_year_num",
            "free_cash_flow_cr",
            "debt_to_equity",
        ]
    ].rename(
        columns={
            "_year_num": "latest_year",
            "free_cash_flow_cr": "fcf",
            "debt_to_equity": "latest_de",
        }
    )

    # ========================================================
    # 3. CALCULATE PREVIOUS-YEAR D/E
    # ========================================================

    balance = (
        balance
        .sort_values(
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

    balance["equity"] = (
        pd.to_numeric(
            balance["equity_capital"],
            errors="coerce",
        )
        +
        pd.to_numeric(
            balance["reserves"],
            errors="coerce",
        )
    )

    balance["borrowings"] = pd.to_numeric(
        balance["borrowings"],
        errors="coerce",
    )

    balance["calculated_de"] = pd.NA

    valid = (
        balance["equity"].notna()
        & (balance["equity"] > 0)
        & balance["borrowings"].notna()
    )

    balance.loc[
        valid,
        "calculated_de",
    ] = (
        balance.loc[
            valid,
            "borrowings",
        ]
        /
        balance.loc[
            valid,
            "equity",
        ]
    )

    balance["previous_de"] = (
        balance
        .groupby("company_id")[
            "calculated_de"
        ]
        .shift(1)
    )

    # Latest balance-sheet row per company

    latest_balance = (
        balance
        .sort_values(
            ["company_id", "_year_num"]
        )
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    latest_balance = latest_balance[
        [
            "company_id",
            "_year_num",
            "calculated_de",
            "previous_de",
        ]
    ].rename(
        columns={
            "_year_num": "latest_year",
            "calculated_de":
                "latest_de_from_balance",
        }
    )

    # ========================================================
    # 4. COMBINE DATA
    # ========================================================

    result = revenue_df.merge(
        latest_ratios,
        on=[
            "company_id",
            "latest_year",
        ],
        how="inner",
    )

    result = result.merge(
        latest_balance,
        on=[
            "company_id",
            "latest_year",
        ],
        how="left",
    )

    # ========================================================
    # 5. APPLY TURNAROUND WATCH CONDITIONS
    # ========================================================

    # Revenue CAGR 3yr > 10%

    result = result[
        result["revenue_cagr_3yr"].notna()
        &
        (
            result["revenue_cagr_3yr"] > 10
        )
    ]

    # Latest FCF > 0

    result = result[
        result["fcf"].notna()
        &
        (
            result["fcf"] > 0
        )
    ]

    # Latest D/E < previous D/E

    result = result[
        result[
            "latest_de_from_balance"
        ].notna()
        &
        result[
            "previous_de"
        ].notna()
        &
        (
            result[
                "latest_de_from_balance"
            ]
            <
            result[
                "previous_de"
            ]
        )
    ]

    return (
        result
        .sort_values(
            "revenue_cagr_3yr",
            ascending=False,
        )
        .reset_index(drop=True)
    )


# ============================================================
# RUN ALL SIX PRESETS
# ============================================================

def run_all_presets(
    db_path: str | Path = "data/db/n100.db",
) -> dict[str, pd.DataFrame]:
    """Run all six Sprint 3 presets."""

    results = {}

    # Five standard presets

    for name in PRESETS:

        results[name] = run_preset(
            name,
            db_path,
        )

    # Sixth preset

    results["Turnaround Watch"] = (
        run_turnaround_watch(
            db_path
        )
    )

    return results


# ============================================================
# PRINT DAY 16 REPORT
# ============================================================

def print_preset_results(
    db_path: str | Path = "data/db/n100.db",
) -> None:
    """Print Day 16 preset validation report."""

    print("=" * 80)
    print("DAY 16 — PRESET SCREENER CHECK")
    print("=" * 80)

    results = run_all_presets(
        db_path
    )

    for name, result in results.items():

        print()
        print("-" * 80)
        print(name)
        print("-" * 80)

        print(
            "Rows:",
            len(result),
        )

        if "company_id" in result.columns:

            print(
                "Unique companies:",
                result[
                    "company_id"
                ].nunique(),
            )

        if result.empty:

            print(
                "No companies matched."
            )

            continue

        if name == "Turnaround Watch":

            columns = [
                "company_id",
                "latest_year",
                "revenue_cagr_3yr",
                "fcf",
                "latest_de_from_balance",
                "previous_de",
            ]

        else:

            columns = [
                "company_id",
                "roe",
                "de",
                "fcf",
                "revenue_cagr_5yr",
                "pat_cagr_5yr",
                "dividend_payout_ratio_pct",
            ]

        available = [
            column
            for column in columns
            if column in result.columns
        ]

        print(
            result[
                available
            ]
            .head(10)
            .to_string(index=False)
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print_preset_results()