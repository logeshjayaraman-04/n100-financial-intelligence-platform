import pandas as pd

print("=" * 80)
print("ABB MAR 2024 SOURCE CHECK")
print("=" * 80)

p = pd.read_csv("data/processed/profitandloss.csv")

rows = p[
    (p["company_id"] == "ABB") &
    (p["year"] == "Mar 2024")
]

print()
print("P&L rows:", len(rows))
print(rows.to_string(index=False))

print()

b = pd.read_csv("data/processed/balancesheet.csv")

rows = b[
    (b["company_id"] == "ABB") &
    (b["year"] == "Mar 2024")
]

print("Balance Sheet rows:", len(rows))
print(rows.to_string(index=False))