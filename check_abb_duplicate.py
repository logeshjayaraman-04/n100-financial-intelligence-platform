import sqlite3

db = sqlite3.connect("data/db/n100.db")

rows = db.execute("""
    SELECT
        company_id,
        year,
        id,
        return_on_equity_pct,
        debt_to_equity,
        revenue_cagr_5yr,
        pat_cagr_5yr,
        eps_cagr_5yr
    FROM financial_ratios
    WHERE company_id = ?
      AND year = ?
""", ("ABB", "Mar 2024")).fetchall()

print("=" * 80)
print("ABB MAR 2024 DUPLICATE CHECK")
print("=" * 80)

for row in rows:
    print(row)

db.close()