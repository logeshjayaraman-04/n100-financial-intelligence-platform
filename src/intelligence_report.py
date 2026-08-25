from financial_engine import analyze_company
from peer_engine import build_peer_comparison
from stock_engine import calculate_stock_metrics


def print_intelligence_report(company_id):
    financial = analyze_company(company_id)

    if not financial:
        print("No financial data available.")
        return

    peers = build_peer_comparison(company_id)
    stock = calculate_stock_metrics(company_id)

    print()
    print("=" * 80)
    print("N100 FINANCIAL INTELLIGENCE REPORT")
    print("=" * 80)

    print()
    print("COMPANY")
    print("-" * 80)
    print("Company:", financial["company"])
    print("Company ID:", financial["company_id"])

    print()
    print("FINANCIAL HEALTH")
    print("-" * 80)
    print(
        f"Sales growth:       {financial['sales_growth_pct']:.2f}%"
    )
    print(
        f"Profit growth:      {financial['profit_growth_pct']:.2f}%"
    )
    print(
        f"Operating margin:   {financial['operating_margin_pct']:.2f}%"
    )
    print(
        f"ROE:                {financial['roe_pct']:.2f}%"
    )
    print(
        f"Debt / Equity:      {financial['debt_to_equity']:.2f}"
    )
    print(
        f"Interest coverage:  {financial['interest_coverage']:.2f}"
    )
    print(
        f"Free cash flow:     {financial['free_cash_flow_cr']:.2f} Cr"
    )
    print(
        f"Latest EPS:         {financial['eps']:.2f}"
    )

    print()
    print("=" * 80)
    print(
        f"FINANCIAL HEALTH SCORE: "
        f"{financial['health_score']} / 100"
    )
    print("=" * 80)

    if peers:
        ranking = None

        for index, peer in enumerate(peers, start=1):
            if peer["company_id"] == company_id:
                ranking = index
                break

        print()
        print("PEER POSITION")
        print("-" * 80)
        print(
            f"Rank: {ranking} of {len(peers)}"
        )

        print()
        print(
            f"{'Company':<35}"
            f"{'Score':>10}"
        )
        print("-" * 50)

        for peer in peers:
            print(
                f"{peer['company'][:35]:<35}"
                f"{peer['health_score']:>10}"
            )

    else:
        print()
        print("PEER POSITION")
        print("-" * 80)
        print("No peer comparison available.")

    if stock:
        print()
        print("STOCK PERFORMANCE")
        print("-" * 80)
        print(
            f"Price records:     {stock['price_records']}"
        )
        print(
            f"First price:       {stock['first_price']:.2f}"
        )
        print(
            f"Latest price:      {stock['latest_price']:.2f}"
        )
        print(
            f"Highest price:     {stock['highest_price']:.2f}"
        )
        print(
            f"Lowest price:      {stock['lowest_price']:.2f}"
        )
        print(
            f"Total return:      {stock['total_return_pct']:.2f}%"
        )

    else:
        print()
        print("STOCK PERFORMANCE")
        print("-" * 80)
        print("No stock-price data available.")

    print()
    print("=" * 80)
    print("END OF INTELLIGENCE REPORT")
    print("=" * 80)


if __name__ == "__main__":
    print_intelligence_report("ABB")