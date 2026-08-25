import pandas as pd
from pathlib import Path

from src.analytics.cashflow_kpis import (
    cfo_quality_score,
    capital_allocation_pattern,
    cash_flow_sign,
)


INPUT_FILE = Path("data/processed/cashflow.csv")
OUTPUT_FILE = Path("output/capital_allocation.csv")


def main():
    print("Generating capital allocation report...")

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing columns: {missing}"
        )

    results = []

    for _, row in df.iterrows():
        cfo = row["operating_activity"]
        cfi = row["investing_activity"]
        cff = row["financing_activity"]

        ratio = None

        # CFO/PAT is optional here because PAT is not
        # available in the cash-flow file itself.
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
    print("Output:", OUTPUT_FILE)

    print()
    print("Pattern counts:")
    print(
        result_df["pattern_label"]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()