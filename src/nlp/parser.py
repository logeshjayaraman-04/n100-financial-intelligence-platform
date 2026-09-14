from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT_DIR / "data" / "raw" / "analysis.xlsx"
DB_FILE = ROOT_DIR / "data" / "db" / "n100.db"
OUTPUT_DIR = ROOT_DIR / "output"

PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_FILE = OUTPUT_DIR / "parse_failures.csv"
DIVERGENCE_FILE = OUTPUT_DIR / "cagr_divergence_flags.csv"


# =========================================================
# TARGET FIELDS
# =========================================================

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# =========================================================
# REQUIRED REGEX
# =========================================================

YEAR_PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)%"
)


# =========================================================
# PARSE ONE VALUE
# =========================================================

def parse_metric_text(
    text: object,
) -> tuple[int, float] | None:
    """
    Parse text such as:

        10 Years: 21%
        5 Years: 24%
        3 Years: 17%

    using the Sprint 5 required regex.
    """

    if pd.isna(text):
        return None

    text = str(text).strip()

    match = YEAR_PATTERN.search(text)

    if not match:
        return None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


# =========================================================
# LOAD ANALYSIS FILE
# =========================================================

def load_analysis() -> pd.DataFrame:

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Analysis file not found: {INPUT_FILE}"
        )

    df = pd.read_excel(
        INPUT_FILE,
        header=1,
    )

    required_columns = [
        "company_id",
        *TARGET_FIELDS,
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    return df


# =========================================================
# PARSE ANALYSIS DATA
# =========================================================

def build_parsed_output(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    parsed_rows = []
    failure_rows = []

    for _, row in df.iterrows():

        company_id = row["company_id"]

        if pd.isna(company_id):
            continue

        company_id = str(company_id).strip()

        for metric_type in TARGET_FIELDS:

            raw_text = row[metric_type]

            parsed = parse_metric_text(raw_text)

            if parsed is None:

                if not pd.isna(raw_text):

                    failure_rows.append(
                        {
                            "company_id": company_id,
                            "metric_type": metric_type,
                            "raw_text": str(raw_text),
                        }
                    )

                continue

            period_years, value_pct = parsed

            parsed_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": period_years,
                    "value_pct": value_pct,
                }
            )

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "raw_text",
        ],
    )

    return parsed_df, failures_df


# =========================================================
# LOAD RATIO ENGINE CAGR DATA
# =========================================================

def load_ratio_cagr_data() -> pd.DataFrame:

    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_FILE}"
        )

    query = """
        SELECT
            company_id,
            year,
            revenue_cagr_5yr,
            pat_cagr_5yr
        FROM financial_ratios
        WHERE revenue_cagr_5yr IS NOT NULL
           OR pat_cagr_5yr IS NOT NULL
        ORDER BY company_id, year
    """

    with sqlite3.connect(DB_FILE) as conn:

        ratios = pd.read_sql_query(
            query,
            conn,
        )

    return ratios


# =========================================================
# CROSS-VALIDATE CAGR VALUES
# =========================================================

def build_divergence_flags(
    parsed_df: pd.DataFrame,
    ratios_df: pd.DataFrame,
) -> pd.DataFrame:

    if parsed_df.empty or ratios_df.empty:

        return pd.DataFrame(
            columns=[
                "company_id",
                "metric_type",
                "period_years",
                "parsed_value_pct",
                "ratio_engine_value_pct",
                "absolute_divergence_pct",
                "manual_review",
            ]
        )

    ratio_rows = []

    for company_id, group in ratios_df.groupby(
        "company_id"
    ):

        group = group.copy()

        group["_year_num"] = (
            group["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )

        group = group.sort_values(
            "_year_num"
        )

        latest = group.iloc[-1]

        if pd.notna(
            latest["revenue_cagr_5yr"]
        ):

            ratio_rows.append(
                {
                    "company_id": str(company_id),
                    "metric_type": "compounded_sales_growth",
                    "ratio_engine_value_pct": float(
                        latest["revenue_cagr_5yr"]
                    ),
                }
            )

        if pd.notna(
            latest["pat_cagr_5yr"]
        ):

            ratio_rows.append(
                {
                    "company_id": str(company_id),
                    "metric_type": "compounded_profit_growth",
                    "ratio_engine_value_pct": float(
                        latest["pat_cagr_5yr"]
                    ),
                }
            )

    ratio_lookup = pd.DataFrame(
        ratio_rows
    )

    if ratio_lookup.empty:

        return pd.DataFrame(
            columns=[
                "company_id",
                "metric_type",
                "period_years",
                "parsed_value_pct",
                "ratio_engine_value_pct",
                "absolute_divergence_pct",
                "manual_review",
            ]
        )

    cagr_metrics = [
        "compounded_sales_growth",
        "compounded_profit_growth",
    ]

    parsed_cagr = parsed_df[
        parsed_df["metric_type"].isin(
            cagr_metrics
        )
    ].copy()

    merged = parsed_cagr.merge(
        ratio_lookup,
        on=[
            "company_id",
            "metric_type",
        ],
        how="left",
    )

    merged["parsed_value_pct"] = pd.to_numeric(
        merged["value_pct"],
        errors="coerce",
    )

    merged["absolute_divergence_pct"] = (
        merged["parsed_value_pct"]
        - merged["ratio_engine_value_pct"]
    ).abs()

    merged["manual_review"] = (
        merged["ratio_engine_value_pct"].notna()
        & (
            merged["absolute_divergence_pct"]
            > 5.0
        )
    )

    result = merged[
        [
            "company_id",
            "metric_type",
            "period_years",
            "parsed_value_pct",
            "ratio_engine_value_pct",
            "absolute_divergence_pct",
            "manual_review",
        ]
    ].copy()

    return result.sort_values(
        [
            "company_id",
            "metric_type",
            "period_years",
        ]
    )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    analysis_df = load_analysis()

    parsed_df, failures_df = (
        build_parsed_output(
            analysis_df
        )
    )

    ratios_df = load_ratio_cagr_data()

    divergence_df = build_divergence_flags(
        parsed_df,
        ratios_df,
    )

    parsed_df.to_csv(
        PARSED_FILE,
        index=False,
    )

    failures_df.to_csv(
        FAILURES_FILE,
        index=False,
    )

    divergence_df.to_csv(
        DIVERGENCE_FILE,
        index=False,
    )

    review_count = int(
        divergence_df["manual_review"]
        .fillna(False)
        .sum()
    )

    print("=== NLP ANALYSIS PARSER ===")
    print(
        f"Input rows: {len(analysis_df)}"
    )
    print(
        f"Parsed rows: {len(parsed_df)}"
    )
    print(
        f"Parse failures: {len(failures_df)}"
    )
    print(
        f"CAGR comparisons: {len(divergence_df)}"
    )
    print(
        f"Divergence > 5%: {review_count}"
    )
    print(
        f"Parsed output: {PARSED_FILE}"
    )
    print(
        f"Failures output: {FAILURES_FILE}"
    )
    print(
        f"Divergence output: {DIVERGENCE_FILE}"
    )


if __name__ == "__main__":
    main()