import pandas as pd

p = pd.read_csv("data/processed/profitandloss.csv")
b = pd.read_csv("data/processed/balancesheet.csv")
c = pd.read_csv("data/processed/cashflow.csv")

print("=" * 80)
print("ABB MAR 2024 — RATIO INPUT CHECK")
print("=" * 80)

for name, df in [
    ("P&L", p),
    ("Balance Sheet", b),
    ("Cash Flow", c),
]:
    rows = df[
        (df["company_id"] == "ABB") &
        (df["year"] == "Mar 2024")
    ]

    print()
    print(name, "rows:", len(rows))
    print(rows.to_string(index=False))