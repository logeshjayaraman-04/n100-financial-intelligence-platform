import sqlite3
from financial_engine import get_connection


def get_stock_data(company_id):
    """Get historical stock prices for a company."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
    date,
    close_price
FROM stock_prices
            WHERE company_id = ?
            ORDER BY date
            """,
            (company_id,),
        ).fetchall()

    return rows


def calculate_stock_metrics(company_id):
    """Calculate basic stock-performance metrics."""

    rows = get_stock_data(company_id)

    if not rows:
        return None

    prices = [float(row["close_price"]) for row in rows]

    first_price = prices[0]
    latest_price = prices[-1]

    total_return = (
        ((latest_price - first_price) / first_price) * 100
        if first_price
        else None
    )

    highest_price = max(prices)
    lowest_price = min(prices)

    return {
        "company_id": company_id,
        "price_records": len(prices),
        "first_price": first_price,
        "latest_price": latest_price,
        "highest_price": highest_price,
        "lowest_price": lowest_price,
        "total_return_pct": total_return,
    }


def print_stock_analysis(company_id):
    """Print stock-performance analysis."""

    analysis = calculate_stock_metrics(company_id)

    if not analysis:
        print("No stock-price data available.")
        return

    print()
    print("=" * 70)
    print("STOCK PERFORMANCE ANALYSIS")
    print("=" * 70)

    print("Company ID:", analysis["company_id"])
    print("Price records:", analysis["price_records"])

    print()
    print("PRICE")
    print("-" * 70)
    print(
        f"First price:     {analysis['first_price']:.2f}"
    )
    print(
        f"Latest price:    {analysis['latest_price']:.2f}"
    )
    print(
        f"Highest price:   {analysis['highest_price']:.2f}"
    )
    print(
        f"Lowest price:    {analysis['lowest_price']:.2f}"
    )

    print()
    print("PERFORMANCE")
    print("-" * 70)
    print(
        f"Total return:    "
        f"{analysis['total_return_pct']:.2f}%"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    print_stock_analysis("ABB")