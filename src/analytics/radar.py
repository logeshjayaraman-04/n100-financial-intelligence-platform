"""
SPRINT 3 — DAY 19
Peer Group Radar Charts

Generates one radar/polar chart per company with:
- Company values
- Peer-group average
- 8 axes:
  ROE
  ROCE
  Net Profit Margin
  D/E
  FCF
  PAT CAGR 5yr
  Revenue CAGR 5yr
  Composite Score

For companies without a peer group, a standalone chart is generated
using the Nifty 100 average as the reference.
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DB_PATH = Path("data/db/n100.db")
PEER_GROUPS_PATH = Path("data/processed/peer_groups.csv")
OUTPUT_DIR = Path("reports/radar_charts")


METRICS = [
    "ROE",
    "ROCE",
    "Net Profit Margin",
    "D/E",
    "FCF",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "Composite Score",
]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    db = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        db,
    )

    companies = pd.read_sql_query(
        "SELECT * FROM companies",
        db,
    )

    db.close()

    peer_groups = pd.read_csv(
        PEER_GROUPS_PATH
    )

    return (
        ratios,
        companies,
        peer_groups,
    )


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(
    ratios,
    companies,
    peer_groups,
):

    df = ratios.copy()

    # --------------------------------------------------------
    # ROCE
    # --------------------------------------------------------

    if "roce" in df.columns:

        df["roce_value"] = pd.to_numeric(
            df["roce"],
            errors="coerce",
        )

    elif (
        "return_on_capital_employed_pct"
        in df.columns
    ):

        df["roce_value"] = pd.to_numeric(
            df[
                "return_on_capital_employed_pct"
            ],
            errors="coerce",
        )

    else:

        roce = companies[
            [
                "id",
                "roce_percentage",
            ]
        ].copy()

        roce = roce.rename(
            columns={
                "id": "company_id",
                "roce_percentage": "roce_value",
            }
        )

        df = df.merge(
            roce,
            on="company_id",
            how="left",
        )

    # --------------------------------------------------------
    # Standard metric names
    # --------------------------------------------------------

    df["ROE"] = pd.to_numeric(
        df["return_on_equity_pct"],
        errors="coerce",
    )

    df["ROCE"] = pd.to_numeric(
        df["roce_value"],
        errors="coerce",
    )

    df["Net Profit Margin"] = pd.to_numeric(
        df["net_profit_margin_pct"],
        errors="coerce",
    )

    df["D/E"] = pd.to_numeric(
        df["debt_to_equity"],
        errors="coerce",
    )

    df["FCF"] = pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce",
    )

    df["PAT CAGR 5yr"] = pd.to_numeric(
        df["pat_cagr_5yr"],
        errors="coerce",
    )

    df["Revenue CAGR 5yr"] = pd.to_numeric(
        df["revenue_cagr_5yr"],
        errors="coerce",
    )

    df["Composite Score"] = pd.to_numeric(
        df["composite_quality_score"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Year number
    # --------------------------------------------------------

    df["_year_num"] = pd.to_numeric(
        df["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Latest available row per company
    # --------------------------------------------------------

    df = (
        df
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

    latest = (
        df
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------
    # Peer group mapping
    # --------------------------------------------------------

    peer_map = peer_groups[
        [
            "company_id",
            "peer_group_name",
        ]
    ].drop_duplicates()

    latest = latest.merge(
        peer_map,
        on="company_id",
        how="left",
    )

    return latest


# ============================================================
# NORMALISATION
# ============================================================

def normalise_values(
    values,
    reference,
):

    combined = pd.concat(
        [
            values,
            reference,
        ],
        ignore_index=True,
    )

    combined = pd.to_numeric(
        combined,
        errors="coerce",
    )

    valid = combined.dropna()

    if valid.empty:
        return 0.5

    low = valid.quantile(
        0.10
    )

    high = valid.quantile(
        0.90
    )

    if high == low:
        return 0.5

    value = pd.to_numeric(
        values,
        errors="coerce",
    )

    if isinstance(value, pd.Series):

        value = value.iloc[0]

    if pd.isna(value):
        return 0.5

    value = min(
        max(value, low),
        high,
    )

    return float(
        (value - low)
        / (high - low)
    )


# ============================================================
# RADAR CHART
# ============================================================

def create_radar_chart(
    company_id,
    company_row,
    peer_rows,
    all_rows,
    output_path,
):

    angles = np.linspace(
        0,
        2 * np.pi,
        len(METRICS),
        endpoint=False,
    )

    angles = np.concatenate(
        [
            angles,
            [angles[0]],
        ]
    )

    company_values = []
    peer_values = []

    # --------------------------------------------------------
    # Metric values
    # --------------------------------------------------------

    for metric in METRICS:

        company_raw = company_row[
            metric
        ]

        if peer_rows is not None and not peer_rows.empty:

            reference_raw = peer_rows[
                metric
            ]

        else:

            reference_raw = all_rows[
                metric
            ]

        company_score = normalise_values(
            pd.Series([company_raw]),
            reference_raw,
        )

        if peer_rows is not None and not peer_rows.empty:

            peer_mean = pd.to_numeric(
                reference_raw,
                errors="coerce",
            ).mean()

        else:

            peer_mean = pd.to_numeric(
                reference_raw,
                errors="coerce",
            ).mean()

        peer_score = normalise_values(
            pd.Series([peer_mean]),
            reference_raw,
        )

        # D/E: lower is better.

        if metric == "D/E":

            company_score = 1 - company_score
            peer_score = 1 - peer_score

        company_values.append(
            company_score
        )

        peer_values.append(
            peer_score
        )

    company_values.append(
        company_values[0]
    )

    peer_values.append(
        peer_values[0]
    )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    fig = plt.figure(
        figsize=(8, 8)
    )

    ax = fig.add_subplot(
        111,
        polar=True,
    )

    ax.plot(
        angles,
        company_values,
        linewidth=2,
        label=company_id,
    )

    ax.fill(
        angles,
        company_values,
        alpha=0.20,
    )

    ax.plot(
        angles,
        peer_values,
        linestyle="--",
        linewidth=2,
        label="Peer Average",
    )

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        METRICS,
        fontsize=10,
    )

    ax.set_ylim(
        0,
        1,
    )

    ax.set_yticks(
        [
            0.25,
            0.50,
            0.75,
            1.00,
        ]
    )

    ax.set_yticklabels(
        [
            "25",
            "50",
            "75",
            "100",
        ],
        fontsize=8,
    )

    peer_name = company_row.get(
        "peer_group_name"
    )

    if pd.isna(peer_name):
        peer_name = "Nifty 100 Average"

    ax.set_title(
        f"{company_id} — {peer_name}",
        fontsize=14,
        pad=25,
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(
            1.20,
            1.10,
        ),
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)


# ============================================================
# GENERATE ALL CHARTS
# ============================================================

def generate_charts():

    print("=" * 80)
    print("DAY 19 — RADAR CHART GENERATION")
    print("=" * 80)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        ratios,
        companies,
        peer_groups,
    ) = load_data()

    latest = prepare_data(
        ratios,
        companies,
        peer_groups,
    )

    print(
        "Companies:",
        len(latest),
    )

    generated = 0

    for _, company_row in latest.iterrows():

        company_id = company_row[
            "company_id"
        ]

        peer_group = company_row[
            "peer_group_name"
        ]

        if pd.isna(peer_group):

            peer_rows = None

        else:

            peer_rows = latest[
                latest[
                    "peer_group_name"
                ]
                == peer_group
            ]

        output_path = (
            OUTPUT_DIR
            / f"{company_id}_radar.png"
        )

        create_radar_chart(
            company_id,
            company_row,
            peer_rows,
            latest,
            output_path,
        )

        generated += 1

    print()
    print("=" * 80)
    print("DAY 19 — RADAR CHARTS COMPLETE")
    print("=" * 80)
    print(
        "Charts generated:",
        generated,
    )

    print(
        "Output directory:",
        OUTPUT_DIR,
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    generate_charts()