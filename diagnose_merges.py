import pandas as pd

print("=" * 80)
print("MERGE DUPLICATE DIAGNOSTIC")
print("=" * 80)

pnl = pd.read_csv("data/processed/profitandloss.csv")
balance = pd.read_csv("data/processed/balancesheet.csv")
cashflow = pd.read_csv("data/processed/cashflow.csv")
companies = pd.read_csv("data/processed/companies.csv")

# Recreate the year number used by the ratio engine.
# We inspect the actual source year values first.

def normalize_year(value):
    if pd.isna(value):
        return None

    text = str(value).strip()

    digits = "".join(ch for ch in text if ch.isdigit())

    if len(digits) >= 4:
        return int(digits[-4:])

    return None


for df in [pnl, balance, cashflow]:
    df["_year_num"] = df["year"].apply(normalize_year)

print()
print("ABB Mar 2024 source year numbers:")
print()

for name, df in [
    ("P&L", pnl),
    ("Balance", balance),
    ("Cash Flow", cashflow),
]:
    rows = df[
        (df["company_id"] == "ABB") &
        (df["_year_num"] == 2024)
    ]

    print(name, ":", len(rows), "rows")

print()
print("-" * 80)
print("P&L + Balance merge")
print("-" * 80)

m1 = pnl.merge(
    balance,
    on=["company_id", "_year_num"],
    how="left",
    suffixes=("_pnl", "_bs"),
)

abb_m1 = m1[
    (m1["company_id"] == "ABB") &
    (m1["_year_num"] == 2024)
]

print("ABB rows after P&L + Balance:", len(abb_m1))

print()
print("-" * 80)
print("P&L + Balance + Cash Flow merge")
print("-" * 80)

m2 = m1.merge(
    cashflow,
    on=["company_id", "_year_num"],
    how="left",
    suffixes=("", "_cf"),
)

abb_m2 = m2[
    (m2["company_id"] == "ABB") &
    (m2["_year_num"] == 2024)
]

print("ABB rows after Cash Flow:", len(abb_m2))

print()
print("-" * 80)
print("Company metadata merge")
print("-" * 80)

company_columns = [
    "id",
    "roce_percentage",
    "roe_percentage",
]

available = [
    c for c in company_columns
    if c in companies.columns
]

companies_small = companies[available].copy()

companies_small = companies_small.rename(
    columns={"id": "company_id"}
)

m3 = m2.merge(
    companies_small,
    on="company_id",
    how="left",
)

abb_m3 = m3[
    (m3["company_id"] == "ABB") &
    (m3["_year_num"] == 2024)
]

print("ABB rows after Companies merge:", len(abb_m3))

print()
print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)