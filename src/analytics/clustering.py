"""Module providing N100 financial intelligence functionality."""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "n100.db"
OUTPUT_PATH = ROOT / "output" / "cluster_labels.csv"
ELBOW_PATH = ROOT / "reports" / "elbow_plot.png"

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def load_data():
    """Load latest financial metrics for every company."""
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name
        FROM companies
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

    # The database has free_cash_flow_cr rather than fcf_cagr_5yr.
    # Use the latest FCF value as the available FCF feature.
    latest["fcf_cagr_5yr"] = latest["free_cash_flow_cr"]

    data = companies.merge(
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

    return data


def sector_median_impute(data):
    """Impute missing feature values using sector medians."""
    conn = sqlite3.connect(DB_PATH)

    sectors = pd.read_sql_query(
        """
        SELECT company_id, broad_sector
        FROM sectors
        """,
        conn,
    )

    conn.close()

    data = data.merge(sectors, on="company_id", how="left")

    for feature in FEATURES:
        data[feature] = pd.to_numeric(data[feature], errors="coerce")
        sector_medians = data.groupby("broad_sector")[feature].transform("median")
        data[feature] = data[feature].fillna(sector_medians)
        data[feature] = data[feature].fillna(data[feature].median())

    return data


def make_elbow_plot(X_scaled):
    """Generate the KMeans elbow plot for k=2 through k=10."""
    ks = list(range(2, 11))
    inertias = []

    for k in ks:
        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=20,
        )
        model.fit(X_scaled)
        inertias.append(model.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(ks, inertias, marker="o")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")
    plt.xticks(ks)
    plt.tight_layout()
    plt.savefig(ELBOW_PATH, dpi=150)
    plt.close()


def assign_cluster_names(profile):
    """Assign descriptive archetype names from cluster financial profiles."""
    names = {}

    ordered = profile.sort_values("quality_score", ascending=False).index.tolist()

    if len(ordered) != 5:
        raise ValueError("Expected exactly 5 clusters.")

    names[ordered[0]] = "High-Quality Compounders"
    names[ordered[1]] = "Emerging Growth"
    names[ordered[2]] = "Defensive Dividend Payers"
    names[ordered[3]] = "Value Cyclicals"
    names[ordered[4]] = "Distressed or Turnaround"

    return names


def main():
    """Run the complete Day 36 clustering workflow."""
    print("=== DAY 36 KMEANS CLUSTERING ===")

    data = load_data()
    print("Companies loaded:", len(data))

    data = sector_median_impute(data)

    X = data[FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    make_elbow_plot(X_scaled)

    model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=20,
    )

    data["cluster_id"] = model.fit_predict(X_scaled)

    distances = model.transform(X_scaled)
    data["distance_from_centroid"] = [
        distances[i, cluster_id] for i, cluster_id in enumerate(data["cluster_id"])
    ]

    profile = data.groupby("cluster_id")[FEATURES].mean()

    # Higher ROE, revenue CAGR and OPM are positive.
    # Lower debt is positive.
    profile["quality_score"] = (
        profile["return_on_equity_pct"]
        + profile["revenue_cagr_5yr"]
        + profile["operating_profit_margin_pct"]
        - profile["debt_to_equity"]
        + profile["fcf_cagr_5yr"]
    )

    cluster_names = assign_cluster_names(profile)

    data["cluster_name"] = data["cluster_id"].map(cluster_names)

    result = data[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].sort_values("company_id")

    result.to_csv(OUTPUT_PATH, index=False)

    print()
    print("=== VALIDATION ===")
    print("Cluster rows:", len(result))
    print("Unique companies:", result["company_id"].nunique())
    print("Unique clusters:", result["cluster_id"].nunique())
    print()
    print("Cluster distribution:")
    print(result["cluster_name"].value_counts().to_string())

    print()
    print("Output:", OUTPUT_PATH)
    print("Elbow plot:", ELBOW_PATH)
    print("=== DAY 36 COMPLETE ===")


if __name__ == "__main__":
    main()
