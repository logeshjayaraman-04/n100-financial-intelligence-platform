import sqlite3
import pandas as pd

db = sqlite3.connect("data/db/n100.db")

companies = [
    "ABB",
    "TCS",
    "RELIANCE",
]

print("=" * 80)
print("DAY 12 — MANUAL SPOT CHECK")
print("=" * 80)

for company in companies:

    print()
    print("#" * 80)
    print("COMPANY:", company)
    print("#" * 80)

    query = """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            revenue_cagr_5yr
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
    """

    result = pd.read_sql_query(
        query,
        db,
        params=[company],
    )

    print(result.to_string(index=False))

db.close()