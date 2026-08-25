import sqlite3
import pandas as pd

db = sqlite3.connect("data/db/n100.db")

query = """
WITH latest AS (
    SELECT
        company_id,
        MAX(year) AS latest_year
    FROM financial_ratios
    GROUP BY company_id
),

deduplicated AS (
    SELECT
        company_id,
        year,
        return_on_equity_pct,
        debt_to_equity,
        ROW_NUMBER() OVER (
            PARTITION BY company_id, year
            ORDER BY return_on_equity_pct DESC
        ) AS rn
    FROM financial_ratios
)

SELECT
    company_id,
    year,
    return_on_equity_pct,
    debt_to_equity
FROM deduplicated
WHERE rn = 1
  AND return_on_equity_pct > 15
  AND debt_to_equity < 1
ORDER BY return_on_equity_pct DESC
"""

df = pd.read_sql_query(query, db)

print("=" * 80)
print("DAY 14 — FINAL SCREENER PREVIEW")
print("=" * 80)

print()
print("ROE > 15% AND D/E < 1")
print()

print("Unique companies:", df["company_id"].nunique())
print("Result rows:", len(df))
print()

print(df.to_string(index=False))

print()
print("=" * 80)

count = df["company_id"].nunique()

if 15 <= count <= 50:
    print("SCREENER STATUS: PASS")
    print(f"{count} companies found — within required range 15–50.")
else:
    print("SCREENER STATUS: REVIEW")
    print(f"{count} companies found — outside required range 15–50.")

db.close()