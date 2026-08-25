from pathlib import Path
import pandas as pd

from src.analytics.ratios import (
    return_on_equity,
    return_on_capital_employed,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

COMPANIES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "companies.csv"
)

PNL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "profitandloss.csv"
)

BALANCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "balancesheet.csv"
)

SECTORS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sectors.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "output"
    / "ratio_edge_cases.log"
)


def number(value):
    if pd.isna(value):
        return None

    return float(value)


def category(difference, threshold):
    """
    Categorise source/computed differences.

    These are review categories rather than automatic
    proof of the underlying cause.
    """

    if difference > threshold:
        return "DATA_SOURCE_ISSUE"

    return "NO_ANOMALY"


def main():

    print("=" * 80)
    print("DAY 13 — RATIO EDGE CASE CHECK")
    print("=" * 80)

    companies = pd.read_csv(
        COMPANIES_FILE
    )

    pnl = pd.read_csv(
        PNL_FILE
    )

    balance = pd.read_csv(
        BALANCE_FILE
    )

    sectors = pd.read_csv(
        SECTORS_FILE
    )

    # ---------------------------------------------------------
    # Normalize IDs
    # ---------------------------------------------------------

    for df in [
        companies,
        pnl,
        balance,
        sectors,
    ]:

        id_column = (
            "company_id"
            if "company_id" in df.columns
            else "id"
        )

        df[id_column] = (
            df[id_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # ---------------------------------------------------------
    # Normalize years
    # ---------------------------------------------------------

    pnl["_year"] = pd.to_numeric(
        pnl["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    balance["_year"] = pd.to_numeric(
        balance["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    # ---------------------------------------------------------
    # Build source master
    # ---------------------------------------------------------

    master = companies[
        [
            "id",
            "company_name",
            "roce_percentage",
            "roe_percentage",
        ]
    ].copy()

    master = master.rename(
        columns={
            "id": "company_id",
            "roce_percentage": "source_roce",
            "roe_percentage": "source_roe",
        }
    )

    # ---------------------------------------------------------
    # Merge financial data
    # ---------------------------------------------------------

    data = pnl.merge(
        balance,
        left_on=[
            "company_id",
            "_year",
        ],
        right_on=[
            "company_id",
            "_year",
        ],
        how="left",
        suffixes=("_pnl", "_bs"),
    )

    data = data.merge(
        master,
        on="company_id",
        how="left",
    )

    # ---------------------------------------------------------
    # Calculate and compare
    # ---------------------------------------------------------

    anomalies = []

    for _, row in data.iterrows():

        company_id = row["company_id"]

        year = row["year_pnl"]

        net_profit = number(
            row.get("net_profit")
        )

        equity_capital = number(
            row.get("equity_capital")
        )

        reserves = number(
            row.get("reserves")
        )

        operating_profit = number(
            row.get("operating_profit")
        )

        borrowings = number(
            row.get("borrowings")
        )

        calculated_roe = return_on_equity(
            net_profit,
            equity_capital,
            reserves,
        )

        calculated_roce = (
            return_on_capital_employed(
                operating_profit,
                equity_capital,
                reserves,
                borrowings,
            )
        )

        source_roe = number(
            row.get("source_roe")
        )

        source_roce = number(
            row.get("source_roce")
        )

        # -----------------------------------------------------
        # ROCE anomaly
        # -----------------------------------------------------

        if (
            calculated_roce is not None
            and source_roce is not None
        ):

            roce_difference = abs(
                calculated_roce
                - source_roce
            )

            if roce_difference > 5:

                anomalies.append(
                    {
                        "company_id": company_id,
                        "year": year,
                        "metric": "ROCE",
                        "calculated": calculated_roce,
                        "source": source_roce,
                        "difference": roce_difference,
                        "category": "DATA_SOURCE_ISSUE",
                    }
                )

        # -----------------------------------------------------
        # ROE anomaly
        # -----------------------------------------------------

        if (
            calculated_roe is not None
            and source_roe is not None
        ):

            roe_difference = abs(
                calculated_roe
                - source_roe
            )

            if roe_difference > 5:

                anomalies.append(
                    {
                        "company_id": company_id,
                        "year": year,
                        "metric": "ROE",
                        "calculated": calculated_roe,
                        "source": source_roe,
                        "difference": roe_difference,
                        "category": "DATA_SOURCE_ISSUE",
                    }
                )

    # ---------------------------------------------------------
    # Write log
    # ---------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "N100 FINANCIAL INTELLIGENCE PLATFORM\n"
        )

        file.write(
            "DAY 13 — RATIO EDGE CASE LOG\n"
        )

        file.write(
            "=" * 80 + "\n\n"
        )

        file.write(
            "Comparison:\n"
        )

        file.write(
            "Computed ROCE vs source ROCE: "
            "anomaly threshold > 5 percentage points\n"
        )

        file.write(
            "Computed ROE vs source ROE: "
            "anomaly threshold > 5 percentage points\n\n"
        )

        if not anomalies:

            file.write(
                "NO ANOMALIES FOUND.\n"
            )

        else:

            for item in anomalies:

                file.write(
                    "-" * 80 + "\n"
                )

                file.write(
                    f"Company: {item['company_id']}\n"
                )

                file.write(
                    f"Year: {item['year']}\n"
                )

                file.write(
                    f"Metric: {item['metric']}\n"
                )

                file.write(
                    f"Calculated: {item['calculated']:.4f}\n"
                )

                file.write(
                    f"Source: {item['source']:.4f}\n"
                )

                file.write(
                    f"Difference: {item['difference']:.4f}\n"
                )

                file.write(
                    f"Category: {item['category']}\n"
                )

                file.write(
                    "Explanation: Source financial inputs produce a materially different "
"ratio-engine result. The specified formula is retained for analytics; "
"the source ratio is retained for display/reference.\n"
                )

    print()
    print(
        "Anomalies found:",
        len(anomalies),
    )

    print(
        "Log:",
        OUTPUT_FILE,
    )

    print()
    print(
        "DAY 13 EDGE-CASE CHECK COMPLETE."
    )


if __name__ == "__main__":
    main()