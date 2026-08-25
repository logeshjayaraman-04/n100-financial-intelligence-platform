"""
N100 Financial Intelligence Platform
Sprint 1 ETL pipeline.

Reads raw Excel files, normalises them, applies known source-data
cleanup rules, and writes standardised CSV files to data/processed/.
"""

from pathlib import Path

import pandas as pd

from src.etl.normaliser import read_excel_normalized


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def clean_source_data(df, file_name):
    """Apply targeted source-data cleanup rules."""

    # ------------------------------------------------------------------
    # Known conflicting ABB records.
    # ------------------------------------------------------------------
    if file_name in {
        "cashflow.xlsx",
        "financial_ratios.xlsx",
    }:
        if {"company_id", "year"}.issubset(df.columns):

            mask = (
                df["company_id"]
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("ABB")
            )

            abb = df[mask].copy()

            if not abb.empty:
                before = len(df)

                abb = abb.drop_duplicates(
                    subset=["company_id", "year"],
                    keep="first",
                )

                df = pd.concat(
                    [
                        df[~mask],
                        abb,
                    ],
                    ignore_index=True,
                )

                removed = before - len(df)

                if removed:
                    print(
                        f"{file_name}: "
                        f"removed {removed} conflicting ABB rows"
                    )

    # ------------------------------------------------------------------
    # Remove duplicate records where the business data is identical.
    # ------------------------------------------------------------------
    if file_name in {
        "profitandloss.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "financial_ratios.xlsx",
    }:
        if {"company_id", "year"}.issubset(df.columns):

            before = len(df)

            df = df.drop_duplicates(
                subset=["company_id", "year"],
                keep="first",
            ).reset_index(drop=True)

            removed = before - len(df)

            if removed:
                print(
                    f"{file_name}: "
                    f"removed {removed} identical duplicate rows"
                )

    # ------------------------------------------------------------------
    # Known invalid source record.
    #
    # ADANIENSOL Mar 2014 contains zero sales and zero financial values.
    # DQ-06 requires positive sales, so remove this invalid source row.
    # ------------------------------------------------------------------
    if file_name == "profitandloss.xlsx":
        if {"company_id", "year", "sales"}.issubset(df.columns):

            mask = (
                df["company_id"]
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("ADANIENSOL")
                & df["year"]
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("MAR 2014")
                & pd.to_numeric(
                    df["sales"],
                    errors="coerce",
                ).eq(0)
            )

            removed = int(mask.sum())

            if removed:
                df = df.loc[~mask].copy()

                print(
                    f"{file_name}: "
                    f"removed {removed} invalid "
                    f"ADANIENSOL Mar 2014 row"
                )

    # ------------------------------------------------------------------
    # Known ticker typo in source data.
    #
    # AGTL is a typo for ATGL. ATGL exists in companies.csv.
    # ------------------------------------------------------------------
    if "company_id" in df.columns:

        mask = (
            df["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
            .eq("AGTL")
        )

        corrected = int(mask.sum())

        if corrected:
            df.loc[mask, "company_id"] = "ATGL"

            print(
                f"{file_name}: "
                f"corrected {corrected} AGTL rows to ATGL"
            )

    return df


def run_pipeline() -> None:
    """Normalise all raw Excel files and write processed CSV files."""

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        RAW_DIR.glob("*.xlsx")
    )

    if not files:
        raise FileNotFoundError(
            f"No Excel files found in {RAW_DIR}"
        )

    print(
        "Running N100 ETL pipeline..."
    )

    for file_path in files:

        df = read_excel_normalized(
            file_path
        )

        df = clean_source_data(
            df,
            file_path.name.lower(),
        )

        output_path = (
            PROCESSED_DIR /
            f"{file_path.stem}.csv"
        )

        df.to_csv(
            output_path,
            index=False,
        )

        print(
            f"{file_path.name} -> "
            f"{output_path.name} "
            f"({len(df)} rows, "
            f"{len(df.columns)} columns)"
        )

    print(
        "ETL pipeline completed."
    )


if __name__ == "__main__":
    run_pipeline()