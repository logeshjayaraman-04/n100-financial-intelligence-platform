from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]

CAPITAL_FILE = ROOT_DIR / "output" / "capital_allocation.csv"
INTELLIGENCE_FILE = ROOT_DIR / "output" / "cashflow_intelligence.xlsx"

PATTERN_SUMMARY_FILE = ROOT_DIR / "output" / "capital_allocation_pattern_summary.csv"
PATTERN_CHANGES_FILE = ROOT_DIR / "output" / "pattern_changes.csv"


EXPECTED_PATTERNS = [
    "Reinvestor",
    "Shareholder Returns",
    "Liquidating Assets",
    "Growth Funded by Debt",
    "Distress Signal",
    "Pre-Revenue",
    "Cash Accumulator",
    "Mixed",
]


def main():
    print("=== DAY 32 CAPITAL ALLOCATION ===")

    # --------------------------------------------------------
    # Load capital allocation data
    # --------------------------------------------------------

    capital = pd.read_csv(CAPITAL_FILE)

    required_capital_columns = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]

    missing = [
        column
        for column in required_capital_columns
        if column not in capital.columns
    ]

    if missing:
        raise ValueError(
            f"Missing capital allocation columns: {missing}"
        )

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    company_count = capital["company_id"].nunique()
    row_count = len(capital)

    duplicate_count = capital.duplicated(
        ["company_id", "year"]
    ).sum()

    pattern_count = capital["pattern_label"].nunique()

    print()
    print("CAPITAL ALLOCATION VALIDATION")
    print("Rows:", row_count)
    print("Companies:", company_count)
    print("Duplicate company-year rows:", duplicate_count)
    print("Unique patterns:", pattern_count)

    if duplicate_count != 0:
        raise ValueError(
            "Duplicate company-year rows detected."
        )

    missing_patterns = [
        pattern
        for pattern in EXPECTED_PATTERNS
        if pattern not in set(capital["pattern_label"])
    ]

    if missing_patterns:
        raise ValueError(
            f"Missing expected patterns: {missing_patterns}"
        )

    if pattern_count != 8:
        raise ValueError(
            f"Expected 8 patterns, found {pattern_count}."
        )

    # --------------------------------------------------------
    # Pattern distribution
    # --------------------------------------------------------

    summary = (
        capital["pattern_label"]
        .value_counts()
        .rename_axis("pattern_label")
        .reset_index(name="row_count")
    )

    summary["percentage"] = (
        summary["row_count"] / row_count * 100
    ).round(2)

    summary.to_csv(
        PATTERN_SUMMARY_FILE,
        index=False,
    )

    print()
    print("PATTERN DISTRIBUTION")
    print(summary.to_string(index=False))

    # --------------------------------------------------------
    # Load Day 31 cash-flow intelligence
    # --------------------------------------------------------

    intelligence = pd.read_excel(
        INTELLIGENCE_FILE,
        sheet_name="cashflow_intelligence",
    )

    required_intelligence_columns = [
        "company_id",
        "year",
    ]

    missing = [
        column
        for column in required_intelligence_columns
        if column not in intelligence.columns
    ]

    if missing:
        raise ValueError(
            f"Missing intelligence columns: {missing}"
        )

    # --------------------------------------------------------
    # Add latest capital allocation pattern
    # --------------------------------------------------------

    latest_capital = capital.copy()

    latest_capital["_year_sort"] = (
        latest_capital["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .fillna("0")
        .astype(int)
    )

    latest_capital = (
        latest_capital
        .sort_values(
            ["company_id", "_year_sort"]
        )
        .groupby("company_id", as_index=False)
        .tail(1)
    )

    latest_capital = latest_capital[
        [
            "company_id",
            "pattern_label",
        ]
    ].rename(
        columns={
            "pattern_label":
                "capital_allocation_pattern"
        }
    )

    intelligence = intelligence.drop(
        columns=["capital_allocation_pattern"],
        errors="ignore",
    )

    intelligence = intelligence.merge(
        latest_capital,
        on="company_id",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Validate latest pattern coverage
    # --------------------------------------------------------

    missing_company_patterns = intelligence[
        "capital_allocation_pattern"
    ].isna().sum()

    print()
    print(
        "Companies missing latest capital allocation pattern:",
        missing_company_patterns,
    )

    if missing_company_patterns != 0:
        raise ValueError(
            "Some companies are missing capital allocation patterns."
        )

    # --------------------------------------------------------
    # Pattern changes
    # --------------------------------------------------------

    history = capital.copy()

    history["_year_sort"] = (
        history["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .fillna("0")
        .astype(int)
    )

    history = history.sort_values(
        ["company_id", "_year_sort"]
    )

    history["previous_pattern"] = (
        history
        .groupby("company_id")["pattern_label"]
        .shift(1)
    )

    changes = history[
        history["previous_pattern"].notna()
        & (
            history["previous_pattern"]
            != history["pattern_label"]
        )
    ].copy()

    changes = changes[
        [
            "company_id",
            "year",
            "previous_pattern",
            "pattern_label",
        ]
    ].rename(
        columns={
            "pattern_label": "current_pattern"
        }
    )

    changes.to_csv(
        PATTERN_CHANGES_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Save updated intelligence workbook
    # --------------------------------------------------------

    intelligence.to_excel(
        INTELLIGENCE_FILE,
        sheet_name="cashflow_intelligence",
        index=False,
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    print()
    print("FINAL VALIDATION")
    print(
        "Intelligence companies:",
        intelligence["company_id"].nunique(),
    )
    print(
        "Capital allocation companies:",
        capital["company_id"].nunique(),
    )
    print(
        "Latest patterns:",
        intelligence[
            "capital_allocation_pattern"
        ].nunique(),
    )
    print(
        "Pattern changes:",
        len(changes),
    )

    print()
    print(
        "Pattern summary:",
        PATTERN_SUMMARY_FILE,
    )
    print(
        "Pattern changes:",
        PATTERN_CHANGES_FILE,
    )
    print(
        "Updated intelligence:",
        INTELLIGENCE_FILE,
    )

    print()
    print("=== DAY 32 COMPLETE ===")


if __name__ == "__main__":
    main()