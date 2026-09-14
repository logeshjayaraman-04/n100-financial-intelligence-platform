import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics.cashflow_kpis import (
    capital_allocation_pattern,
    cash_flow_sign,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
DB_FILE = ROOT_DIR / "data" / "db" / "n100.db"
OUTPUT_FILE = ROOT_DIR / "output" / "capital_allocation.csv"


def main():
    print("Generating capital allocation report...")

    conn = sqlite3.connect(DB_FILE)

    cashflow = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity
        FROM cashflow
        ORDER BY company_id, year
        """,
        conn,
    )

    profit = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            net_profit
        FROM profitandloss
        """,
        conn,
    )

    conn.close()

    required_cashflow = [
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
    ]

    missing = [
        column
        for column in required_cashflow
        if column not in cashflow.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing cash-flow columns: {missing}"
        )

    merged = cashflow.merge(
        profit,
        on=["company_id", "year"],
        how="left",
    )

    results = []

    for _, row in merged.iterrows():
        cfo = row["operating_activity"]
        cfi = row["investing_activity"]
        cff = row["financing_activity"]
        pat = row["net_profit"]

        ratio = None

        if (
            pd.notna(cfo)
            and pd.notna(pat)
            and pat != 0
        ):
            ratio = float(cfo) / float(pat)

        pattern = capital_allocation_pattern(
            cfo=cfo,
            cfi=cfi,
            cff=cff,
            cfo_pat_ratio=ratio,
        )

        results.append(
            {
                "company_id": row["company_id"],
                "year": row["year"],
                "cfo_sign": cash_flow_sign(cfo),
                "cfi_sign": cash_flow_sign(cfi),
                "cff_sign": cash_flow_sign(cff),
                "pattern_label": pattern,
            }
        )

    result_df = pd.DataFrame(results)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("Capital allocation report created.")
    print("Rows:", len(result_df))
    print(
        "Companies:",
        result_df["company_id"].nunique(),
    )
    print("Output:", OUTPUT_FILE)

    print()
    print("Pattern counts:")
    print(
        result_df["pattern_label"]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Unique patterns:",
        result_df["pattern_label"].nunique(),
    )


if __name__ == "__main__":
    main()
