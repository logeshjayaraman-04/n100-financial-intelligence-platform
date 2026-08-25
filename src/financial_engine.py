from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "db" / "n100.db"


def get_connection():
    """Open a read-only connection to the N100 database."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def get_company(company_id):
    """Return basic company information."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                company_name,
                website,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

    return dict(row) if row else None


def get_profit_loss(company_id):
    """Return profit and loss history."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                year,
                sales,
                expenses,
                operating_profit,
                opm_percentage,
                other_income,
                interest,
                depreciation,
                profit_before_tax,
                tax_percentage,
                net_profit,
                eps,
                dividend_payout
            FROM profitandloss
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_balance_sheet(company_id):
    """Return balance sheet history."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                year,
                equity_capital,
                reserves,
                borrowings,
                other_liabilities,
                total_liabilities,
                fixed_assets,
                cwip,
                investments,
                other_asset,
                total_assets
            FROM balancesheet
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_cash_flow(company_id):
    """Return cash flow history."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_ratios(company_id):
    """Return financial ratio history."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                year,
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                debt_to_equity,
                interest_coverage,
                asset_turnover,
                free_cash_flow_cr,
                capex_cr,
                earnings_per_share,
                book_value_per_share,
                dividend_payout_ratio_pct,
                total_debt_cr,
                cash_from_operations_cr
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_market_data(company_id):
    """Return market valuation history."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_stock_prices(company_id):
    """Return historical stock prices."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                adjusted_close
            FROM stock_prices
            WHERE company_id = ?
            ORDER BY date
            """,
            (company_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_company_summary(company_id):
    """Return all available financial information for a company."""
    company = get_company(company_id)

    if not company:
        return None

    return {
        "company": company,
        "profit_loss": get_profit_loss(company_id),
        "balance_sheet": get_balance_sheet(company_id),
        "cash_flow": get_cash_flow(company_id),
        "ratios": get_ratios(company_id),
        "market_data": get_market_data(company_id),
        "stock_prices": get_stock_prices(company_id),
    }


if __name__ == "__main__":
    company_id = "ABB"

    summary = get_company_summary(company_id)

    if summary is None:
        print(f"Company not found: {company_id}")
    else:
        print("Financial Intelligence Engine")
        print("=" * 40)
        print("Company:", summary["company"]["company_name"])
        print("P&L records:", len(summary["profit_loss"]))
        print("Balance sheet records:", len(summary["balance_sheet"]))
        print("Cash flow records:", len(summary["cash_flow"]))
        print("Ratio records:", len(summary["ratios"]))
        print("Market records:", len(summary["market_data"]))
        print("Stock price records:", len(summary["stock_prices"]))
def calculate_growth(values):
    """Calculate CAGR-style growth between first and last valid values."""
    if len(values) < 2:
        return None

    first = values[0]
    last = values[-1]

    if first is None or last is None or first <= 0:
        return None

    periods = len(values) - 1

    return ((last / first) ** (1 / periods) - 1) * 100


def calculate_financial_health(company_id):
    """Calculate a basic financial-health profile."""

    summary = get_company_summary(company_id)

    if summary is None:
        return None

    pnl = summary["profit_loss"]
    ratios = summary["ratios"]
    cashflow = summary["cash_flow"]

    result = {
        "company_id": company_id,
        "company_name": summary["company"]["company_name"],
        "sales_growth_pct": None,
        "profit_growth_pct": None,
        "latest_opm_pct": None,
        "latest_roe_pct": None,
        "latest_debt_to_equity": None,
        "latest_interest_coverage": None,
        "latest_eps": None,
        "latest_free_cash_flow_cr": None,
        "latest_cash_from_operations_cr": None,
        "financial_health_score": 0,
    }

    # -------------------------
    # Growth
    # -------------------------

    sales = [
        row["sales"]
        for row in pnl
        if row["sales"] is not None
        and row["sales"] > 0
    ]

    profits = [
        row["net_profit"]
        for row in pnl
        if row["net_profit"] is not None
        and row["net_profit"] > 0
    ]

    result["sales_growth_pct"] = calculate_growth(sales)
    result["profit_growth_pct"] = calculate_growth(profits)

    # -------------------------
    # Latest P&L data
    # -------------------------

    if pnl:
        latest_pnl = pnl[-1]

        result["latest_opm_pct"] = (
            latest_pnl["opm_percentage"]
        )

        result["latest_eps"] = latest_pnl["eps"]

    # -------------------------
    # Latest ratio data
    # -------------------------

    if ratios:
        latest_ratio = ratios[-1]

        result["latest_roe_pct"] = (
            latest_ratio["return_on_equity_pct"]
        )

        result["latest_debt_to_equity"] = (
            latest_ratio["debt_to_equity"]
        )

        result["latest_interest_coverage"] = (
            latest_ratio["interest_coverage"]
        )

        result["latest_free_cash_flow_cr"] = (
            latest_ratio["free_cash_flow_cr"]
        )

        result["latest_cash_from_operations_cr"] = (
            latest_ratio["cash_from_operations_cr"]
        )

    # -------------------------
    # Financial health score
    # -------------------------

    score = 0

    # Growth
    if (
        result["sales_growth_pct"] is not None
        and result["sales_growth_pct"] > 10
    ):
        score += 20

    if (
        result["profit_growth_pct"] is not None
        and result["profit_growth_pct"] > 10
    ):
        score += 20

    # Profitability
    if (
        result["latest_opm_pct"] is not None
        and result["latest_opm_pct"] > 15
    ):
        score += 15

    if (
        result["latest_roe_pct"] is not None
        and result["latest_roe_pct"] > 15
    ):
        score += 15

    # Debt
    if (
        result["latest_debt_to_equity"] is not None
        and result["latest_debt_to_equity"] < 1
    ):
        score += 10

    # Interest coverage
    if (
        result["latest_interest_coverage"] is not None
        and result["latest_interest_coverage"] > 3
    ):
        score += 10

    # Cash flow
    if (
        result["latest_cash_from_operations_cr"] is not None
        and result["latest_cash_from_operations_cr"] > 0
    ):
        score += 10

    result["financial_health_score"] = score

    return result


def print_financial_health(company_id):
    """Print a readable financial-health report."""

    result = calculate_financial_health(company_id)

    if result is None:
        print(f"Company not found: {company_id}")
        return

    print()
    print("=" * 55)
    print("FINANCIAL HEALTH REPORT")
    print("=" * 55)

    print("Company:", result["company_name"])
    print("Company ID:", result["company_id"])

    print()
    print("GROWTH")
    print("-" * 55)

    print(
        "Sales growth:",
        format_percent(result["sales_growth_pct"])
    )

    print(
        "Profit growth:",
        format_percent(result["profit_growth_pct"])
    )

    print()
    print("PROFITABILITY")
    print("-" * 55)

    print(
        "Operating margin:",
        format_percent(result["latest_opm_pct"])
    )

    print(
        "ROE:",
        format_percent(result["latest_roe_pct"])
    )

    print()
    print("BALANCE SHEET / DEBT")
    print("-" * 55)

    print(
        "Debt / Equity:",
        format_number(result["latest_debt_to_equity"])
    )

    print(
        "Interest coverage:",
        format_number(
            result["latest_interest_coverage"]
        )
    )

    print()
    print("CASH FLOW")
    print("-" * 55)

    print(
        "Free cash flow:",
        format_number(
            result["latest_free_cash_flow_cr"]
        ),
        "Cr"
    )

    print(
        "Cash from operations:",
        format_number(
            result["latest_cash_from_operations_cr"]
        ),
        "Cr"
    )

    print()
    print("VALUATION / EPS")
    print("-" * 55)

    print(
        "Latest EPS:",
        format_number(result["latest_eps"])
    )

    print()
    print("=" * 55)
    print(
        "FINANCIAL HEALTH SCORE:",
        result["financial_health_score"],
        "/ 100"
    )
    print("=" * 55)


def format_number(value):
    """Format a numeric value safely."""

    if value is None:
        return "N/A"

    return f"{value:.2f}"


def format_percent(value):
    """Format percentage safely."""

    if value is None:
        return "N/A"

    return f"{value:.2f}%"

print_financial_health("ABB")

def analyze_company(company_id):
    """Return a complete financial intelligence profile."""

    result = calculate_financial_health(company_id)

    if result is None:
        return None

    summary = get_company_summary(company_id)

    return {
        "company": result["company_name"],
        "company_id": company_id,
        "sales_growth_pct": result["sales_growth_pct"],
        "profit_growth_pct": result["profit_growth_pct"],
        "operating_margin_pct": result["latest_opm_pct"],
        "roe_pct": result["latest_roe_pct"],
        "debt_to_equity": result["latest_debt_to_equity"],
        "interest_coverage": result["latest_interest_coverage"],
        "free_cash_flow_cr": result["latest_free_cash_flow_cr"],
        "cash_from_operations_cr": result[
            "latest_cash_from_operations_cr"
        ],
        "eps": result["latest_eps"],
        "health_score": result["financial_health_score"],
        "profit_loss_years": len(summary["profit_loss"]),
        "balance_sheet_years": len(summary["balance_sheet"]),
        "cash_flow_years": len(summary["cash_flow"]),
        "stock_price_records": len(summary["stock_prices"]),
    }


if __name__ == "__main__":
    company = analyze_company("ABB")

    if company:
        print("\nCOMPANY INTELLIGENCE")
        print("=" * 55)

        for key, value in company.items():
            print(f"{key}: {value}")
    else:
        print("Company not found.")