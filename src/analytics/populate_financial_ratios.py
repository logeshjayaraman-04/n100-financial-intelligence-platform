from pathlib import Path
import sqlite3

import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    asset_turnover,
)

from src.analytics.cagr import (
    revenue_cagr,
    pat_cagr,
    eps_cagr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED = PROJECT_ROOT / "data" / "processed"
DB_PATH = PROJECT_ROOT / "data" / "db" / "n100.db"


def number(value):
    """Convert a value to float or None."""
    if pd.isna(value):
        return None

    return float(value)


def find_column(df, candidates):
    """Return first matching column."""
    for column in candidates:
        if column in df.columns:
            return column

    return None


def build_cagr_map(df, value_column, years):
    """
    Build CAGR values using historical rows.

    Uses exact available year positions where possible.
    """

    result = {}

    for company_id, group in df.groupby("company_id"):

        group = group.copy()

        group["_year_num"] = (
            group["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
        )

        group["_year_num"] = pd.to_numeric(
            group["_year_num"],
            errors="coerce",
        )

        group = group.dropna(
            subset=["_year_num"]
        ).sort_values("_year_num")

        values = {
            int(row["_year_num"]): number(row[value_column])
            for _, row in group.iterrows()
        }

        for _, row in group.iterrows():

            end_year = int(row["_year_num"])

            entry = {}

            for window in [3, 5, 10]:

                start_year = end_year - window

                if start_year not in values:
                    entry[f"{window}yr"] = (
                        None,
                        "INSUFFICIENT",
                    )
                    continue

                start_value = values[start_year]
                end_value = values[end_year]

                if value_column == "sales":

                    entry[f"{window}yr"] = revenue_cagr(
                        start_value,
                        end_value,
                        window,
                    )

                elif value_column == "net_profit":

                    entry[f"{window}yr"] = pat_cagr(
                        start_value,
                        end_value,
                        window,
                    )

                elif value_column == "eps":

                    entry[f"{window}yr"] = eps_cagr(
                        start_value,
                        end_value,
                        window,
                    )

            result[
                (company_id, end_year)
            ] = entry

    return result


def main():

    print("=" * 80)
    print("DAY 12 — POPULATING FINANCIAL RATIOS")
    print("=" * 80)

    pnl = pd.read_csv(
        PROCESSED / "profitandloss.csv"
    )

    balance = pd.read_csv(
        PROCESSED / "balancesheet.csv"
    )

    cashflow = pd.read_csv(
        PROCESSED / "cashflow.csv"
    )

    companies = pd.read_csv(
        PROCESSED / "companies.csv"
    )

    print()
    print("P&L rows:", len(pnl))
    print("Balance sheet rows:", len(balance))
    print("Cash-flow rows:", len(cashflow))
    print("Companies:", len(companies))

    # ---------------------------------------------------------
    # Normalize company IDs
    # ---------------------------------------------------------

    for df in [
        pnl,
        balance,
        cashflow,
    ]:

        df["company_id"] = (
            df["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    companies["id"] = (
        companies["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # ---------------------------------------------------------
    # Normalize year
    # ---------------------------------------------------------

    for df in [
        pnl,
        balance,
        cashflow,
    ]:

        df["_year_num"] = pd.to_numeric(
            df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce",
        )

        # -----------------------------
    # Merge source data
    # -----------------------------

    merged = pnl.merge(
        balance,
        on=["company_id", "year"],
        how="left",
        suffixes=("_pnl", "_bs"),
    )

    merged = merged.merge(
        cashflow,
        on=["company_id", "year"],
        how="left",
        suffixes=("", "_cf"),
    )

    merged = merged.merge(
        companies[
            [
                "id",
                "roce_percentage",
                "roe_percentage",
            ]
        ],
        left_on="company_id",
        right_on="id",
        how="left",
    )

    # ---------------------------------------------------------
    # CAGR maps
    # ---------------------------------------------------------

    revenue_map = build_cagr_map(
        pnl,
        "sales",
        [3, 5, 10],
    )

    pat_map = build_cagr_map(
        pnl,
        "net_profit",
        [3, 5, 10],
    )

    eps_map = build_cagr_map(
        pnl,
        "eps",
        [3, 5, 10],
    )

    records = []

    # ---------------------------------------------------------
    # Calculate ratios
    # ---------------------------------------------------------

    for _, row in merged.iterrows():

        company_id = row["company_id"]
        year_num = row["_year_num"]

        if pd.isna(year_num):
            continue

        year_num = int(year_num)

        sales = number(
            row.get("sales")
        )

        net_profit = number(
            row.get("net_profit")
        )

        operating_profit = number(
            row.get("operating_profit")
        )

        equity_capital = number(
            row.get("equity_capital")
        )

        reserves = number(
            row.get("reserves")
        )

        borrowings = number(
            row.get("borrowings")
        )

        interest = number(
            row.get("interest")
        )

        other_income = number(
            row.get("other_income")
        )

        total_assets = number(
            row.get("total_assets")
        )

        investments = number(
            row.get("investments")
        )

        operating_activity = number(
            row.get("operating_activity")
        )

        investing_activity = number(
            row.get("investing_activity")
        )

        eps = number(
            row.get("eps")
        )

        # -----------------------------------------------------
        # Book Value Per Share
        #
        # Source files do not contain a shares_outstanding
        # column. Therefore derive shares from:
        #
        # shares = net_profit / EPS
        #
        # Then:
        #
        # book value per share =
        # (equity capital + reserves) / shares
        # -----------------------------------------------------

        if (
            equity_capital is not None
            and reserves is not None
            and eps not in (None, 0)
            and net_profit is not None
        ):

            shares_outstanding = (
                net_profit / eps
            )

            if shares_outstanding != 0:

                book_value = (
                    equity_capital
                    + reserves
                ) / shares_outstanding

            else:

                book_value = None

        else:

            book_value = None

        dividend_payout = number(
            row.get("dividend_payout")
        )

        # -----------------------------------------------------
        # Profitability
        # -----------------------------------------------------

        npm = net_profit_margin(
            net_profit,
            sales,
        )

        opm = operating_profit_margin(
            operating_profit,
            sales,
        )

        roe = return_on_equity(
            net_profit,
            equity_capital,
            reserves,
        )

        roce = return_on_capital_employed(
            operating_profit,
            equity_capital,
            reserves,
            borrowings,
        )

        roa = return_on_assets(
            net_profit,
            total_assets,
        )

        # -----------------------------------------------------
        # Leverage
        # -----------------------------------------------------

        de = debt_to_equity(
            borrowings,
            equity_capital,
            reserves,
        )

        icr = interest_coverage_ratio(
            operating_profit,
            other_income,
            interest,
        )

        turnover = asset_turnover(
            sales,
            total_assets,
        )

        # -----------------------------------------------------
        # Cash flow
        # -----------------------------------------------------

        fcf = None

        if (
            operating_activity is not None
            and investing_activity is not None
        ):

            fcf = (
                operating_activity
                + investing_activity
            )

        capex = None

        if investing_activity is not None:
            capex = abs(investing_activity)

        # -----------------------------------------------------
        # CAGR
        # -----------------------------------------------------

        revenue_entry = revenue_map.get(
            (company_id, year_num),
            {},
        )

        pat_entry = pat_map.get(
            (company_id, year_num),
            {},
        )

        eps_entry = eps_map.get(
            (company_id, year_num),
            {},
        )

        revenue_5yr = revenue_entry.get(
            "5yr",
            (None, "INSUFFICIENT"),
        )[0]

        pat_5yr = pat_entry.get(
            "5yr",
            (None, "INSUFFICIENT"),
        )[0]

        eps_5yr = eps_entry.get(
            "5yr",
            (None, "INSUFFICIENT"),
        )[0]

        # -----------------------------------------------------
        # Composite quality score
        # -----------------------------------------------------

        score_parts = [
            npm,
            roe,
            roce,
            turnover,
        ]

        valid_scores = [
            x
            for x in score_parts
            if x is not None
        ]

        composite = None

        if valid_scores:

            composite = (
                sum(valid_scores)
                / len(valid_scores)
            )

        # -----------------------------------------------------
        # Record
        # -----------------------------------------------------

        records.append(
            {
                "company_id": company_id,
                "year": row["year"],
                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe,
                "debt_to_equity": de,
                "interest_coverage": icr,
                "asset_turnover": turnover,
                "free_cash_flow_cr": fcf,
                "capex_cr": capex,
                "earnings_per_share": eps,
                "book_value_per_share": book_value,
                "dividend_payout_ratio_pct": dividend_payout,
                "total_debt_cr": borrowings,
                "cash_from_operations_cr": operating_activity,
                "revenue_cagr_5yr": revenue_5yr,
                "pat_cagr_5yr": pat_5yr,
                "eps_cagr_5yr": eps_5yr,
                "composite_quality_score": composite,
            }
        )

    result = pd.DataFrame(records)

    print()
    print("Calculated rows:", len(result))

    # ---------------------------------------------------------
    # Write to SQLite
    # ---------------------------------------------------------

    db = sqlite3.connect(DB_PATH)

    db.execute(
        "DELETE FROM financial_ratios"
    )

    columns = list(result.columns)

    placeholders = ", ".join(
        "?"
        for _ in columns
    )

    quoted = ", ".join(
        f'"{column}"'
        for column in columns
    )

    sql = f"""
        INSERT INTO financial_ratios
        ({quoted})
        VALUES ({placeholders})
    """

    rows = [
        tuple(
            None if pd.isna(value)
            else value
            for value in row
        )
        for row in result.itertuples(
            index=False,
            name=None,
        )
    ]

    db.executemany(
        sql,
        rows,
    )

    db.commit()

    count = db.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    db.close()

    print()
    print("financial_ratios rows:", count)

    if count < 1100:

        raise RuntimeError(
            f"ERROR: expected >= 1100 rows, got {count}"
        )

    print()
    print("SUCCESS: financial_ratios populated.")


if __name__ == "__main__":
    main()