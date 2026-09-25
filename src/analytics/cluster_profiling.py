"""Module providing N100 financial intelligence functionality."""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "n100.db"

CLUSTER_FILE = ROOT / "output" / "cluster_labels.csv"
PROFILE_FILE = ROOT / "output" / "cluster_profiles.csv"
OUTLIER_FILE = ROOT / "output" / "outlier_report.csv"
STATS_FILE = ROOT / "output" / "portfolio_stats.csv"
HEATMAP_FILE = ROOT / "reports" / "correlation_heatmap.png"

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def load_cluster_data():
    """Load cluster labels and latest financial metrics."""
    clusters = pd.read_csv(CLUSTER_FILE)

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT id AS company_id, company_name
        FROM companies
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT company_id, broad_sector, sub_sector
        FROM sectors
        """,
        conn,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            debt_to_equity,
            revenue_cagr_5yr,
            free_cash_flow_cr,
            operating_profit_margin_pct
        FROM financial_ratios
        """,
        conn,
    )

    conn.close()

    ratios["year_num"] = pd.to_numeric(
        ratios["year"].astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    latest = (
        ratios.sort_values(["company_id", "year_num"])
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    latest["fcf_cagr_5yr"] = latest["free_cash_flow_cr"]

    data = (
        companies.merge(sectors, on="company_id", how="left")
        .merge(
            latest[
                [
                    "company_id",
                    "return_on_equity_pct",
                    "debt_to_equity",
                    "revenue_cagr_5yr",
                    "fcf_cagr_5yr",
                    "operating_profit_margin_pct",
                ]
            ],
            on="company_id",
            how="left",
        )
        .merge(clusters, on="company_id", how="left")
    )

    return data


def create_cluster_profile(data):
    """Create mean and median statistics for every cluster."""
    rows = []

    for cluster_id, group in data.groupby("cluster_id"):
        row = {
            "cluster_id": int(cluster_id),
            "cluster_name": group["cluster_name"].iloc[0],
            "company_count": len(group),
        }

        for feature in FEATURES:
            row[f"{feature}_mean"] = group[feature].mean()
            row[f"{feature}_median"] = group[feature].median()

        rows.append(row)

    profile = pd.DataFrame(rows).sort_values("cluster_id")
    profile.to_csv(PROFILE_FILE, index=False)

    return profile


def create_correlation_heatmap(data):
    """Create Pearson correlation heatmap for the 10 latest KPIs."""
    conn = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            free_cash_flow_cr,
            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct
        FROM financial_ratios
        """,
        conn,
    )

    conn.close()

    ratios["year_num"] = pd.to_numeric(
        ratios["year"].astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    latest = (
        ratios.sort_values(["company_id", "year_num"])
        .groupby("company_id", as_index=False)
        .tail(1)
    )

    kpis = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
    ]

    corr = latest[kpis].apply(pd.to_numeric, errors="coerce").corr(method="pearson")

    plt.figure(figsize=(12, 10))
    plt.imshow(corr, aspect="auto")
    plt.colorbar(label="Pearson correlation")
    plt.xticks(range(len(kpis)), kpis, rotation=70, ha="right")
    plt.yticks(range(len(kpis)), kpis)

    for i in range(len(kpis)):
        for j in range(len(kpis)):
            value = corr.iloc[i, j]
            if pd.notna(value):
                plt.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7)

    plt.title("Latest-Year KPI Correlation Matrix")
    plt.tight_layout()
    plt.savefig(HEATMAP_FILE, dpi=150)
    plt.close()


def create_outlier_report(data):
    """Flag observations with sector-level absolute Z-score above 3."""
    rows = []

    for sector, group in data.groupby("broad_sector", dropna=False):
        group = group.copy()

        for feature in FEATURES:
            values = pd.to_numeric(group[feature], errors="coerce")

            mean = values.mean()
            std = values.std(ddof=0)

            if pd.isna(std) or std == 0:
                group[f"{feature}_z"] = 0.0
            else:
                group[f"{feature}_z"] = (values - mean) / std

        for _, row in group.iterrows():
            flagged = []

            for feature in FEATURES:
                z = row[f"{feature}_z"]

                if pd.notna(z) and abs(z) > 3:
                    flagged.append(
                        {
                            "metric": feature,
                            "z_score": round(float(z), 4),
                        }
                    )

            if flagged:
                for item in flagged:
                    rows.append(
                        {
                            "company_id": row["company_id"],
                            "company_name": row["company_name"],
                            "broad_sector": sector,
                            "metric": item["metric"],
                            "z_score": item["z_score"],
                            "issue": "Absolute sector Z-score > 3",
                        }
                    )

    columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "metric",
        "z_score",
        "issue",
    ]

    outliers = pd.DataFrame(rows, columns=columns)
    outliers.to_csv(OUTLIER_FILE, index=False)

    return outliers


def create_portfolio_stats(data):
    """Create percentile and dispersion statistics for clustering KPIs."""
    rows = []

    for feature in FEATURES:
        values = pd.to_numeric(data[feature], errors="coerce").dropna()

        rows.append(
            {
                "kpi": feature,
                "P10": values.quantile(0.10),
                "P25": values.quantile(0.25),
                "P50": values.quantile(0.50),
                "P75": values.quantile(0.75),
                "P90": values.quantile(0.90),
                "Mean": values.mean(),
                "Std": values.std(),
            }
        )

    stats = pd.DataFrame(rows)
    stats.to_csv(STATS_FILE, index=False)

    return stats


def main():
    """Run Day 37 cluster profiling and portfolio statistics."""
    print("=== DAY 37 CLUSTER PROFILING ===")

    data = load_cluster_data()

    print("Companies:", data["company_id"].nunique())
    print("Clusters:", data["cluster_id"].nunique())

    profile = create_cluster_profile(data)
    outliers = create_outlier_report(data)
    stats = create_portfolio_stats(data)

    create_correlation_heatmap(data)

    print()
    print("=== CLUSTER PROFILE ===")
    print(
        profile[["cluster_id", "cluster_name", "company_count"]].to_string(index=False)
    )

    print()
    print("Outlier rows:", len(outliers))
    print("Portfolio statistics:", len(stats), "KPIs")

    print()
    print("Created:")
    print(PROFILE_FILE)
    print(OUTLIER_FILE)
    print(STATS_FILE)
    print(HEATMAP_FILE)

    print()
    print("=== DAY 37 COMPLETE ===")


if __name__ == "__main__":
    main()
