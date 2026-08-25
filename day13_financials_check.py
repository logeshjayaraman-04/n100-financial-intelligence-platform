import pandas as pd

companies = pd.read_csv(
    "data/processed/companies.csv"
)

sectors = pd.read_csv(
    "data/processed/sectors.csv"
)

companies["id"] = (
    companies["id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

sectors["company_id"] = (
    sectors["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("=" * 80)
print("DAY 13 — FINANCIALS SECTOR CHECK")
print("=" * 80)

print("Companies:", len(companies))
print("Sector rows:", len(sectors))
print()

print("Sector columns:")
print(sectors.columns.tolist())
print()

financials = sectors[
    sectors["broad_sector"]
    .astype(str)
    .str.strip()
    .str.lower()
    .eq("financials")
]

print("Financials companies:", len(financials))
print()

print(
    financials[
        ["company_id", "broad_sector"]
    ].to_string(index=False)
)