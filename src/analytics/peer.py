"""
SPRINT 3 — DAY 18
Peer Percentile Rankings

Computes percentile rankings for 10 metrics within each peer group
and stores the results in SQLite table: peer_percentiles.
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


DB_PATH = Path("data/db/n100.db")
PEER_GROUPS_PATH = Path(
    "data/processed/peer_groups.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

METRICS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "roce",
    "Net Profit Margin": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "PAT CAGR 5yr": "pat_cagr_5yr",
    "Revenue CAGR 5yr": "revenue_cagr_5yr",
    "EPS CAGR 5yr": "eps_cagr_5yr",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
}


# ============================================================
# HELPERS
# ============================================================

def find_column(df, candidates):
    """
    Return the first available column from candidates.
    """

    for column in candidates:
        if column in df.columns:
            return column

    return None


def percentile_rank(series):
    """
    Percentile rank from 0 to 100.

    Highest value receives 100.
    Lowest value receives 0.

    For D/E the caller reverses the result.
    """

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = values.notna()

    result = pd.Series(
        np.nan,
        index=series.index,
        dtype=float,
    )

    if valid.sum() == 0:
        return result

    if valid.sum() == 1:
        result.loc[valid] = 100.0
        return result

    ranks = (
        values.loc[valid]
        .rank(
            method="min",
            pct=True,
        )
        * 100
    )

    result.loc[valid] = ranks

    return result


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 80)
    print("DAY 18 — PEER PERCENTILE RANKINGS")
    print("=" * 80)

    peer_groups = pd.read_csv(
        PEER_GROUPS_PATH
    )

    print(
        "Peer groups:",
        peer_groups["peer_group_name"]
        .nunique(),
    )

    print(
        "Companies in peer groups:",
        peer_groups["company_id"]
        .nunique(),
    )

    db = sqlite3.connect(
        DB_PATH
    )

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        db,
    )

    companies = pd.read_sql_query(
        "SELECT * FROM companies",
        db,
    )

    db.close()

    return (
        peer_groups,
        ratios,
        companies,
    )


# ============================================================
# PREPARE RATIO DATA
# ============================================================

def prepare_ratios(ratios, companies):

    df = ratios.copy()

    # --------------------------------------------------------
    # Resolve ROE
    # --------------------------------------------------------

    if (
        "return_on_equity_pct"
        not in df.columns
    ):

        raise ValueError(
            "financial_ratios is missing "
            "return_on_equity_pct"
        )

    # --------------------------------------------------------
    # Resolve ROCE
    # --------------------------------------------------------

    roce_column = find_column(
        df,
        [
            "roce",
            "return_on_capital_employed_pct",
        ],
    )

    if roce_column is None:

        # Calculate ROCE from available source data.

        required = [
            "return_on_equity_pct"
        ]

        if "roce_percentage" in companies.columns:

            source_roce = companies[
                [
                    "id",
                    "roce_percentage",
                ]
            ].rename(
                columns={
                    "id": "company_id",
                    "roce_percentage": "roce",
                }
            )

            df = df.merge(
                source_roce,
                on="company_id",
                how="left",
            )

            roce_column = "roce"

        else:

            df["roce"] = np.nan
            roce_column = "roce"

    # --------------------------------------------------------
    # Resolve all remaining metrics
    # --------------------------------------------------------

    return df, roce_column


# ============================================================
# BUILD PEER PERCENTILES
# ============================================================

def build_peer_percentiles(
    peer_groups,
    ratios,
    companies,
):

    ratios, roce_column = prepare_ratios(
        ratios,
        companies,
    )

    metric_columns = {
        "ROE": "return_on_equity_pct",
        "ROCE": roce_column,
        "Net Profit Margin": "net_profit_margin_pct",
        "D/E": "debt_to_equity",
        "FCF": "free_cash_flow_cr",
        "PAT CAGR 5yr": "pat_cagr_5yr",
        "Revenue CAGR 5yr": "revenue_cagr_5yr",
        "EPS CAGR 5yr": "eps_cagr_5yr",
        "Interest Coverage": "interest_coverage",
        "Asset Turnover": "asset_turnover",
    }

    output_rows = []

    # --------------------------------------------------------
    # Every peer group
    # --------------------------------------------------------

    for peer_group_name, members in peer_groups.groupby(
        "peer_group_name"
    ):

        company_ids = (
            members["company_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        print()
        print(
            f"Peer group: {peer_group_name}"
        )

        print(
            "Members:",
            len(company_ids),
        )

        # ----------------------------------------------------
        # Latest available year for each company
        # ----------------------------------------------------

        group_ratios = ratios[
            ratios["company_id"]
            .astype(str)
            .isin(company_ids)
        ].copy()

        if group_ratios.empty:
            print(
                "No financial data available."
            )
            continue

        group_ratios["_year_num"] = pd.to_numeric(
            group_ratios["year"]
            .astype(str)
            .str.extract(
                r"(\d{4})"
            )[0],
            errors="coerce",
        )

        group_ratios = (
            group_ratios
            .dropna(
                subset=["_year_num"]
            )
            .sort_values(
                [
                    "company_id",
                    "_year_num",
                ]
            )
        )

        # Latest row per company.

        latest = (
            group_ratios
            .groupby(
                "company_id",
                as_index=False,
            )
            .tail(1)
        )

        # ----------------------------------------------------
        # Calculate 10 metric percentiles
        # ----------------------------------------------------

        for metric_name, column in metric_columns.items():

            if column not in latest.columns:
                continue

            ranks = percentile_rank(
                latest[column]
            )

            # D/E: lower is better.

            if metric_name == "D/E":
                ranks = 100 - ranks

            for idx in latest.index:

                value = latest.loc[
                    idx,
                    column,
                ]

                percentile = ranks.loc[
                    idx
                ]

                if pd.isna(value):
                    continue

                output_rows.append(
                    {
                        "company_id": latest.loc[
                            idx,
                            "company_id",
                        ],
                        "peer_group_name": peer_group_name,
                        "metric": metric_name,
                        "value": value,
                        "percentile_rank": round(
                            float(percentile),
                            2,
                        )
                        if not pd.isna(
                            percentile
                        )
                        else None,
                        "year": latest.loc[
                            idx,
                            "year",
                        ],
                    }
                )

    return pd.DataFrame(
        output_rows
    )


# ============================================================
# WRITE SQLITE
# ============================================================

def write_to_sqlite(
    percentile_df,
):

    db = sqlite3.connect(
        DB_PATH
    )

    # --------------------------------------------------------
    # Create table
    # --------------------------------------------------------

    db.execute(
        """
        DROP TABLE IF EXISTS peer_percentiles
        """
    )

    db.execute(
        """
        CREATE TABLE peer_percentiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year TEXT
        )
        """
    )

    # --------------------------------------------------------
    # Insert rows
    # --------------------------------------------------------

    if not percentile_df.empty:

        percentile_df.to_sql(
            "peer_percentiles",
            db,
            if_exists="append",
            index=False,
        )

    db.commit()

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    count = db.execute(
        """
        SELECT COUNT(*)
        FROM peer_percentiles
        """
    ).fetchone()[0]

    groups = db.execute(
        """
        SELECT COUNT(
            DISTINCT peer_group_name
        )
        FROM peer_percentiles
        """
    ).fetchone()[0]

    companies = db.execute(
        """
        SELECT COUNT(
            DISTINCT company_id
        )
        FROM peer_percentiles
        """
    ).fetchone()[0]

    db.close()

    print()
    print("=" * 80)
    print("PEER PERCENTILE TABLE CREATED")
    print("=" * 80)
    print(
        "Rows:",
        count,
    )

    print(
        "Peer groups:",
        groups,
    )

    print(
        "Companies:",
        companies,
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_peer_percentiles():

    db = sqlite3.connect(
        DB_PATH
    )

    df = pd.read_sql_query(
        """
        SELECT *
        FROM peer_percentiles
        """,
        db,
    )

    db.close()

    print()
    print("=" * 80)
    print("DAY 18 — VALIDATION")
    print("=" * 80)

    print(
        "Total rows:",
        len(df),
    )

    print(
        "Peer groups:",
        df["peer_group_name"]
        .nunique()
        if not df.empty
        else 0,
    )

    print(
        "Metrics:",
        df["metric"]
        .nunique()
        if not df.empty
        else 0,
    )

    if not df.empty:

        print()
        print(
            "Metric counts:"
        )

        print(
            df.groupby(
                "metric"
            )
            .size()
            .to_string()
        )

        print()
        print(
            "Peer group counts:"
        )

        print(
            df.groupby(
                "peer_group_name"
            )
            .size()
            .to_string()
        )

        print()
        print(
            "Sample:"
        )

        print(
            df.head(20)
            .to_string(
                index=False
            )
        )

        # Percentile range check.

        invalid = df[
            (
                df["percentile_rank"]
                < 0
            )
            |
            (
                df["percentile_rank"]
                > 100
            )
        ]

        print()

        print(
            "Invalid percentile rows:",
            len(invalid),
        )


# ============================================================
# MAIN
# ============================================================

def main():

    (
        peer_groups,
        ratios,
        companies,
    ) = load_data()

    percentile_df = build_peer_percentiles(
        peer_groups,
        ratios,
        companies,
    )

    write_to_sqlite(
        percentile_df
    )

    validate_peer_percentiles()

    print()
    print("=" * 80)
    print("SUCCESS: DAY 18 PEER PERCENTILES COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()