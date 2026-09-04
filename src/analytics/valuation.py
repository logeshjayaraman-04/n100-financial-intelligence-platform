from __future__ import annotations

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


# =========================================================
# Paths
# =========================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    ROOT_DIR
    / "data"
    / "db"
    / "n100.db"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "output"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "valuation_summary.xlsx"
)

FLAGS_PATH = (
    OUTPUT_DIR
    / "valuation_flags.csv"
)


# =========================================================
# Database helper
# =========================================================

def read_sql(
    query: str,
    params: tuple = (),
) -> pd.DataFrame:

    with sqlite3.connect(DB_PATH) as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )


# =========================================================
# Load company master
# =========================================================

def load_companies() -> pd.DataFrame:

    return read_sql(
        """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        ORDER BY c.company_name
        """
    )


# =========================================================
# Load market valuation data
# =========================================================

def load_market_cap() -> pd.DataFrame:

    return read_sql(
        """
        SELECT
            company_id,
            year,
            market_cap_crore,
            enterprise_value_crore,
            pe_ratio,
            pb_ratio,
            ev_ebitda,
            dividend_yield_pct
        FROM market_cap
        """
    )


# =========================================================
# Load financial ratios
# =========================================================

def load_ratios() -> pd.DataFrame:

    return read_sql(
        """
        SELECT
            company_id,
            year,
            free_cash_flow_cr
        FROM financial_ratios
        """
    )


# =========================================================
# Year extraction
# =========================================================

def extract_year(
    series: pd.Series,
) -> pd.Series:

    return pd.to_numeric(
        series.astype(str)
        .str.extract(
            r"(\d{4})",
            expand=False,
        ),
        errors="coerce",
    )


# =========================================================
# Latest valuation record
# =========================================================

def latest_market_data(
    market_cap: pd.DataFrame,
) -> pd.DataFrame:

    market_cap = market_cap.copy()

    market_cap["year_num"] = extract_year(
        market_cap["year"]
    )

    market_cap = market_cap.dropna(
        subset=[
            "company_id",
            "year_num",
        ]
    )

    market_cap = market_cap.sort_values(
        [
            "company_id",
            "year_num",
        ]
    )

    latest = (
        market_cap
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    return latest


# =========================================================
# FCF data
# =========================================================

def latest_fcf(
    ratios: pd.DataFrame,
) -> pd.DataFrame:

    ratios = ratios.copy()

    ratios["year_num"] = extract_year(
        ratios["year"]
    )

    ratios = ratios.dropna(
        subset=[
            "company_id",
            "year_num",
        ]
    )

    ratios = ratios.sort_values(
        [
            "company_id",
            "year_num",
        ]
    )

    latest = (
        ratios
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    return latest[
        [
            "company_id",
            "free_cash_flow_cr",
        ]
    ]


# =========================================================
# Five-year median P/E
# =========================================================

def calculate_five_year_median_pe(
    market_cap: pd.DataFrame,
) -> pd.DataFrame:

    data = market_cap.copy()

    data["year_num"] = extract_year(
        data["year"]
    )

    data["pe_ratio"] = pd.to_numeric(
        data["pe_ratio"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "company_id",
            "year_num",
        ]
    )

    data = data.sort_values(
        [
            "company_id",
            "year_num",
        ]
    )

    # Latest five available years per company.
    data = (
        data
        .groupby(
            "company_id",
            group_keys=False,
        )
        .tail(5)
    )

    median_pe = (
        data
        .groupby(
            "company_id",
            as_index=False,
        )["pe_ratio"]
        .median()
        .rename(
            columns={
                "pe_ratio": "5yr_median_PE"
            }
        )
    )

    return median_pe


# =========================================================
# Sector median P/E
# =========================================================

def calculate_sector_median_pe(
    market_cap: pd.DataFrame,
    companies: pd.DataFrame,
) -> pd.DataFrame:

    data = latest_market_data(
        market_cap
    )

    data["pe_ratio"] = pd.to_numeric(
        data["pe_ratio"],
        errors="coerce",
    )

    data = data[
        [
            "company_id",
            "pe_ratio",
        ]
    ]

    data = data.merge(
        companies[
            [
                "company_id",
                "broad_sector",
            ]
        ],
        on="company_id",
        how="left",
    )

    sector_median = (
        data
        .dropna(
            subset=[
                "broad_sector",
                "pe_ratio",
            ]
        )
        .groupby(
            "broad_sector",
            as_index=False,
        )["pe_ratio"]
        .median()
        .rename(
            columns={
                "pe_ratio":
                    "sector_median_PE"
            }
        )
    )

    return sector_median


# =========================================================
# Valuation flag
# =========================================================

def valuation_flag(
    pe,
    sector_median,
):

    if pd.isna(pe) or pd.isna(
        sector_median
    ):
        return "N/A"

    if sector_median <= 0:
        return "N/A"

    if pe > sector_median * 1.5:
        return "Caution"

    if pe < sector_median * 0.7:
        return "Discount"

    return "Fair"


# =========================================================
# Build valuation summary
# =========================================================

def build_valuation_summary() -> pd.DataFrame:

    companies = load_companies()

    market_cap = load_market_cap()

    ratios = load_ratios()


    # -----------------------------------------------------
    # Latest market data
    # -----------------------------------------------------

    latest = latest_market_data(
        market_cap
    )


    # -----------------------------------------------------
    # Latest FCF
    # -----------------------------------------------------

    fcf = latest_fcf(
        ratios
    )


    # -----------------------------------------------------
    # Five-year median P/E
    # -----------------------------------------------------

    median_pe = (
        calculate_five_year_median_pe(
            market_cap
        )
    )


    # -----------------------------------------------------
    # Sector median P/E
    # -----------------------------------------------------

    sector_median = (
        calculate_sector_median_pe(
            market_cap,
            companies,
        )
    )


    # -----------------------------------------------------
    # Merge company information
    # -----------------------------------------------------

    summary = companies.merge(
        latest[
            [
                "company_id",
                "pe_ratio",
                "pb_ratio",
                "ev_ebitda",
                "market_cap_crore",
            ]
        ],
        on="company_id",
        how="left",
    )


    summary = summary.merge(
        fcf,
        on="company_id",
        how="left",
    )


    summary = summary.merge(
        median_pe,
        on="company_id",
        how="left",
    )


    summary = summary.merge(
        sector_median,
        on="broad_sector",
        how="left",
    )


    # -----------------------------------------------------
    # Numeric conversion
    # -----------------------------------------------------

    numeric_columns = [
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "market_cap_crore",
        "free_cash_flow_cr",
        "5yr_median_PE",
        "sector_median_PE",
    ]


    for column in numeric_columns:

        summary[column] = pd.to_numeric(
            summary[column],
            errors="coerce",
        )


    # -----------------------------------------------------
    # FCF Yield
    # -----------------------------------------------------

    summary["FCF_yield_pct"] = np.where(
        (
            summary[
                "market_cap_crore"
            ].notna()
            &
            (
                summary[
                    "market_cap_crore"
                ] != 0
            )
        ),
        (
            summary[
                "free_cash_flow_cr"
            ]
            /
            summary[
                "market_cap_crore"
            ]
            * 100
        ),
        np.nan,
    )


    # -----------------------------------------------------
    # P/E vs sector median
    # -----------------------------------------------------

    summary[
        "PE_vs_sector_median_pct"
    ] = np.where(
        (
            summary[
                "pe_ratio"
            ].notna()
            &
            summary[
                "sector_median_PE"
            ].notna()
            &
            (
                summary[
                    "sector_median_PE"
                ] != 0
            )
        ),
        (
            (
                summary[
                    "pe_ratio"
                ]
                /
                summary[
                    "sector_median_PE"
                ]
            )
            - 1
        )
        * 100,
        np.nan,
    )


    # -----------------------------------------------------
    # Valuation flag
    # -----------------------------------------------------

    summary["flag"] = [
        valuation_flag(
            pe,
            sector_pe,
        )
        for pe, sector_pe in zip(
            summary[
                "pe_ratio"
            ],
            summary[
                "sector_median_PE"
            ],
        )
    ]


    # -----------------------------------------------------
    # Required output columns
    # -----------------------------------------------------

    summary = summary[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag",
        ]
    ].copy()


    # -----------------------------------------------------
    # Friendly column names
    # -----------------------------------------------------

    summary = summary.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )


    summary = summary.sort_values(
        [
            "broad_sector",
            "company_name",
        ]
    ).reset_index(
        drop=True
    )


    return summary


# =========================================================
# Write output files
# =========================================================

def write_outputs(
    summary: pd.DataFrame,
) -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # -----------------------------------------------------
    # Excel summary
    # -----------------------------------------------------

    summary.to_excel(
        SUMMARY_PATH,
        index=False,
    )


    # -----------------------------------------------------
    # Flags CSV
    # -----------------------------------------------------

    flags = summary[
        summary["flag"].isin(
            [
                "Caution",
                "Discount",
            ]
        )
    ].copy()


    flags.to_csv(
        FLAGS_PATH,
        index=False,
    )


# =========================================================
# Main
# =========================================================

def main():

    print(
        "Building valuation summary..."
    )

    summary = build_valuation_summary()


    print(
        f"Companies: {len(summary)}"
    )


    print(
        "\nFlag counts:"
    )

    print(
        summary[
            "flag"
        ].value_counts(
            dropna=False
        )
    )


    print(
        "\nMissing values:"
    )

    print(
        summary.isna().sum()
    )


    write_outputs(
        summary
    )


    print(
        "\nCreated:"
    )

    print(
        SUMMARY_PATH
    )

    print(
        FLAGS_PATH
    )


if __name__ == "__main__":
    main()