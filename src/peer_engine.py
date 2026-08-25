from financial_engine import analyze_company, get_connection


def get_peer_companies(company_id):
    """Find companies belonging to the same peer group."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT
                pg.peer_group_name,
                pg.company_id
            FROM peer_groups pg
            WHERE pg.peer_group_name IN (
                SELECT peer_group_name
                FROM peer_groups
                WHERE company_id = ?
            )
            ORDER BY pg.peer_group_name, pg.company_id
            """,
            (company_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def build_peer_comparison(company_id):
    """Build financial comparison between a company and its peers."""

    peers = get_peer_companies(company_id)

    if not peers:
        return None

    company_ids = []

    for peer in peers:
        peer_id = peer["company_id"]

        if peer_id not in company_ids:
            company_ids.append(peer_id)

    results = []

    for peer_id in company_ids:
        analysis = analyze_company(peer_id)

        if analysis:
            results.append(analysis)

    results.sort(
        key=lambda x: x["health_score"],
        reverse=True,
    )

    return results


def print_peer_comparison(company_id):
    """Print a readable peer comparison."""

    comparison = build_peer_comparison(company_id)

    if not comparison:
        print("No peer comparison available.")
        return

    print()
    print("=" * 95)
    print("PEER COMPARISON")
    print("=" * 95)

    print(
        f"{'Company':<35}"
        f"{'Growth':>10}"
        f"{'Profit':>10}"
        f"{'ROE':>10}"
        f"{'Debt/Eq':>10}"
        f"{'Score':>10}"
    )

    print("-" * 95)

    for company in comparison:

        growth = company["sales_growth_pct"]
        profit = company["profit_growth_pct"]
        roe = company["roe_pct"]
        debt = company["debt_to_equity"]
        score = company["health_score"]

        growth_text = (
            f"{growth:.1f}%"
            if growth is not None
            else "N/A"
        )

        profit_text = (
            f"{profit:.1f}%"
            if profit is not None
            else "N/A"
        )

        roe_text = (
            f"{roe:.1f}%"
            if roe is not None
            else "N/A"
        )

        debt_text = (
            f"{debt:.2f}"
            if debt is not None
            else "N/A"
        )

        print(
            f"{company['company'][:35]:<35}"
            f"{growth_text:>10}"
            f"{profit_text:>10}"
            f"{roe_text:>10}"
            f"{debt_text:>10}"
            f"{score:>10}"
        )

    print("-" * 95)

    ranking = None

    for index, company in enumerate(comparison, start=1):
        if company["company_id"] == company_id:
            ranking = index
            break

    target = next(
        (
            company
            for company in comparison
            if company["company_id"] == company_id
        ),
        None,
    )

    if target:
        print()
        print("TARGET COMPANY")
        print("-" * 95)
        print("Company:", target["company"])
        print("Rank:", ranking, "of", len(comparison))
        print("Health score:", target["health_score"], "/ 100")

    print()
    print("=" * 95)


if __name__ == "__main__":
    print_peer_comparison("ABB")