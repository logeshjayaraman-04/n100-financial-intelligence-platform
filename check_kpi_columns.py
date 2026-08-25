import sqlite3

db = sqlite3.connect("data/db/n100.db")

columns = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "capex_cr",
    "earnings_per_share",
    "book_value_per_share",
    "dividend_payout_ratio_pct",
    "total_debt_cr",
    "cash_from_operations_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "composite_quality_score",
]

print("=" * 80)
print("DAY 12 — KPI NULL CHECK")
print("=" * 80)

for column in columns:
    count = db.execute(
        f'SELECT COUNT(*) FROM financial_ratios '
        f'WHERE "{column}" IS NOT NULL'
    ).fetchone()[0]

    print(f"{column:35} {count}")

db.close()