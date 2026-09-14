from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[2]
DB_FILE = ROOT_DIR / "data" / "db" / "n100.db"
OUTPUT_DIR = ROOT_DIR / "output"

INTELLIGENCE_FILE = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_FILE = OUTPUT_DIR / "distress_alerts.csv"


# ============================================================
# SPRINT 2 / DAY 11 KPI HELPERS
# ============================================================

def free_cash_flow(operating_activity, investing_activity):
    if pd.isna(operating_activity) or pd.isna(investing_activity):
        return None

    return float(operating_activity) + float(investing_activity)


def cfo_quality_score(cfo, pat):
    if pd.isna(cfo) or pd.isna(pat) or pat == 0:
        return None

    return float(cfo) / float(pat)


def cfo_quality_label(score):
    if score is None or pd.isna(score):
        return "Unavailable"

    if score >= 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def capex_intensity(investing_activity, sales):
    if pd.isna(investing_activity) or pd.isna(sales) or sales == 0:
        return None

    return abs(float(investing_activity)) / abs(float(sales)) * 100


def capex_intensity_label(value):
    if value is None or pd.isna(value):
        return "Unavailable"

    if value < 5:
        return "Asset Light"

    if value < 10:
        return "Moderate"

    return "Capital Intensive"


def fcf_conversion_rate(fcf, operating_profit):
    if pd.isna(fcf) or pd.isna(operating_profit) or operating_profit == 0:
        return None

    return float(fcf) / float(operating_profit) * 100


def cash_flow_sign(value):
    if pd.isna(value):
        return "0"

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


def capital_allocation_pattern(
    cfo,
    cfi,
    cff,
    cfo_pat_ratio=None,
):
    if cfo < 0 and cfi < 0 and cff < 0:
        return "Pre-Revenue"

    if cfo < 0 and cfi < 0 and cff > 0:
        return "Growth Funded by Debt"

    if cfo < 0 and cfi > 0 and cff >= 0:
        return "Distress Signal"

    if cfo > 0 and cfi > 0 and cff > 0:
        return "Cash Accumulator"

    if cfo > 0 and cfi > 0 and cff < 0:
        return "Liquidating Assets"

    if (
        cfo > 0
        and cfi < 0
        and cff < 0
        and cfo_pat_ratio is not None
        and cfo_pat_ratio >= 1.5
    ):
        return "Shareholder Returns"

    if cfo > 0 and cfi < 0 and cff < 0:
        return "Reinvestor"

    return "Mixed"


# ============================================================
# DAY 31 CASH FLOW INTELLIGENCE
# ============================================================

def load_table(conn, table, columns):
    query = f"""
        SELECT {", ".join(columns)}
        FROM {table}
        ORDER BY company_id, year
    """
    return pd.read_sql_query(query, conn)


def period_sort(value):
    if pd.isna(value):
        return -1

    text = str(value).strip()

    if text.upper() == "TTM":
        return 9999

    try:
        return int(text)
    except ValueError:
        digits = "".join(c for c in text if c.isdigit())

        if len(digits) >= 4:
            return int(digits[-4:])

    return -1


def latest(df, company_id):
    rows = df[df["company_id"] == company_id].copy()

    if rows.empty:
        return None

    rows["_sort"] = rows["year"].apply(period_sort)
    rows = rows.sort_values("_sort")

    return rows.iloc[-1]


def previous(df, company_id):
    rows = df[df["company_id"] == company_id].copy()

    if len(rows) < 2:
        return None

    rows["_sort"] = rows["year"].apply(period_sort)
    rows = rows.sort_values("_sort")

    return rows.iloc[-2]


def number(value):
    if pd.isna(value):
        return np.nan

    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def cfo_pat_quality(cfo, pat):
    if pd.isna(cfo) or pd.isna(pat):
        return np.nan, "Unavailable"

    if pat == 0:
        if cfo > 0:
            return np.inf, "Strong"
        if cfo < 0:
            return -np.inf, "Poor"
        return np.nan, "Unavailable"

    ratio = cfo / pat

    if ratio > 1.20:
        quality = "Strong"
    elif ratio >= 0.80:
        quality = "Healthy"
    elif ratio >= 0.50:
        quality = "Weak"
    else:
        quality = "Poor"

    return ratio, quality


def capex_intensity_day31(capex, cfo, sales):
    if pd.isna(capex):
        return np.nan, "Unavailable"

    if not pd.isna(cfo) and cfo != 0:
        value = abs(capex) / abs(cfo) * 100

        if value <= 30:
            label = "Low"
        elif value <= 60:
            label = "Medium"
        else:
            label = "High"

        return value, label

    if not pd.isna(sales) and sales != 0:
        value = abs(capex) / abs(sales) * 100
        return value, "Sales-based"

    return np.nan, "Unavailable"


def distress_level(
    cfo,
    pat,
    fcf,
    debt_to_equity,
    interest_coverage,
    previous_debt,
    current_debt,
):
    signals = []

    if not pd.isna(cfo) and cfo < 0:
        signals.append("Negative CFO")

    if not pd.isna(pat) and pat < 0:
        signals.append("Negative PAT")

    if not pd.isna(fcf) and fcf < 0:
        signals.append("Negative FCF")

    if not pd.isna(debt_to_equity) and debt_to_equity > 1.5:
        signals.append("High debt-to-equity")

    if not pd.isna(interest_coverage) and interest_coverage < 1.5:
        signals.append("Weak interest coverage")

    if (
        not pd.isna(previous_debt)
        and not pd.isna(current_debt)
        and current_debt > previous_debt
    ):
        signals.append("Rising debt")

    if len(signals) >= 3:
        level = "High"
    elif len(signals) >= 1:
        level = "Medium"
    else:
        level = "Low"

    return level, signals


def deleveraging(previous_debt, current_debt):
    if pd.isna(previous_debt) or pd.isna(current_debt):
        return "Unavailable", np.nan

    if previous_debt == 0:
        if current_debt == 0:
            return "Stable / Zero Debt", 0.0

        return "Increasing", np.nan

    change = (current_debt - previous_debt) / abs(previous_debt) * 100

    if change <= -10:
        return "Strong Deleveraging", change

    if change < 0:
        return "Deleveraging", change

    if change <= 10:
        return "Stable", change

    return "Increasing", change


# ============================================================
# MAIN DAY 31 GENERATION
# ============================================================

def main():
    print("=== CASH FLOW INTELLIGENCE ===")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)

    companies = pd.read_sql_query(
        """
        SELECT id AS company_id, company_name
        FROM companies
        ORDER BY id
        """,
        conn,
    )

    ratios = load_table(
        conn,
        "financial_ratios",
        [
            "company_id",
            "year",
            "debt_to_equity",
            "interest_coverage",
            "free_cash_flow_cr",
            "capex_cr",
            "total_debt_cr",
            "cash_from_operations_cr",
            "composite_quality_score",
        ],
    )

    pl = load_table(
        conn,
        "profitandloss",
        [
            "company_id",
            "year",
            "sales",
            "net_profit",
        ],
    )

    bs = load_table(
        conn,
        "balancesheet",
        [
            "company_id",
            "year",
            "borrowings",
        ],
    )

    cf = load_table(
        conn,
        "cashflow",
        [
            "company_id",
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ],
    )

    conn.close()

    print(f"Companies: {len(companies)}")
    print(f"Financial ratio rows: {len(ratios)}")
    print(f"Profit & loss rows: {len(pl)}")
    print(f"Balance sheet rows: {len(bs)}")
    print(f"Cash flow rows: {len(cf)}")

    records = []
    alerts = []

    for _, company in companies.iterrows():
        company_id = company["company_id"]
        company_name = company["company_name"]

        r = latest(ratios, company_id)
        rp = previous(ratios, company_id)

        p = latest(pl, company_id)

        b = latest(bs, company_id)
        bp = previous(bs, company_id)

        c = latest(cf, company_id)

        if r is None:
            continue

        cfo = number(r["cash_from_operations_cr"])
        fcf = number(r["free_cash_flow_cr"])
        capex = number(r["capex_cr"])
        debt_equity = number(r["debt_to_equity"])
        interest_coverage = number(r["interest_coverage"])
        quality_score = number(r["composite_quality_score"])

        pat = number(p["net_profit"]) if p is not None else np.nan
        sales = number(p["sales"]) if p is not None else np.nan

        current_debt = number(r["total_debt_cr"])

        previous_debt = (
            number(rp["total_debt_cr"])
            if rp is not None
            else np.nan
        )

        if b is not None:
            balance_debt = number(b["borrowings"])

            if not pd.isna(balance_debt):
                current_debt = balance_debt

        if bp is not None:
            balance_previous_debt = number(bp["borrowings"])

            if not pd.isna(balance_previous_debt):
                previous_debt = balance_previous_debt

        cfo_pat_ratio, cfo_quality = cfo_pat_quality(
            cfo,
            pat,
        )

        capex_pct, capex_class = capex_intensity_day31(
            capex,
            cfo,
            sales,
        )

        distress, signals = distress_level(
            cfo,
            pat,
            fcf,
            debt_equity,
            interest_coverage,
            previous_debt,
            current_debt,
        )

        debt_status, debt_change = deleveraging(
            previous_debt,
            current_debt,
        )

        if cfo > 0 and not pd.isna(fcf) and fcf > 0:
            cashflow_status = "Strong"

        elif cfo > 0:
            cashflow_status = "Positive CFO"

        elif pd.isna(cfo):
            cashflow_status = "Unavailable"

        else:
            cashflow_status = "Negative CFO"

        record = {
            "company_id": company_id,
            "company_name": company_name,
            "year": str(r["year"]),
            "CFO_cr": cfo,
            "PAT_cr": pat,
            "FCF_cr": fcf,
            "CapEx_cr": capex,
            "CFO_PAT_ratio": cfo_pat_ratio,
            "CFO_PAT_quality": cfo_quality,
            "CapEx_intensity_pct": capex_pct,
            "CapEx_intensity_class": capex_class,
            "Debt_to_Equity": debt_equity,
            "Interest_coverage": interest_coverage,
            "Current_debt_cr": current_debt,
            "Previous_debt_cr": previous_debt,
            "Debt_change_pct": debt_change,
            "Deleveraging_status": debt_status,
            "Cashflow_status": cashflow_status,
            "Distress_level": distress,
            "Distress_signal_count": len(signals),
            "Distress_signals": "; ".join(signals),
            "Composite_quality_score": quality_score,
        }

        records.append(record)

        if distress in ["High", "Medium"]:
            alerts.append(
                {
                    "company_id": company_id,
                    "company_name": company_name,
                    "year": str(r["year"]),
                    "distress_level": distress,
                    "signal_count": len(signals),
                    "signals": "; ".join(signals),
                    "CFO_cr": cfo,
                    "PAT_cr": pat,
                    "FCF_cr": fcf,
                    "Debt_to_Equity": debt_equity,
                    "Interest_coverage": interest_coverage,
                    "Current_debt_cr": current_debt,
                    "Previous_debt_cr": previous_debt,
                }
            )

    intelligence = pd.DataFrame(records)
    distress_alerts = pd.DataFrame(alerts)

    required = [
        "company_id",
        "company_name",
        "year",
        "CFO_cr",
        "PAT_cr",
        "FCF_cr",
        "CapEx_cr",
        "CFO_PAT_ratio",
        "CFO_PAT_quality",
        "CapEx_intensity_pct",
        "CapEx_intensity_class",
        "Debt_to_Equity",
        "Interest_coverage",
        "Current_debt_cr",
        "Previous_debt_cr",
        "Debt_change_pct",
        "Deleveraging_status",
        "Cashflow_status",
        "Distress_level",
        "Distress_signal_count",
        "Distress_signals",
        "Composite_quality_score",
    ]

    missing = [
        col
        for col in required
        if col not in intelligence.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if len(intelligence) != len(companies):
        raise ValueError(
            f"Expected {len(companies)} companies, "
            f"processed {len(intelligence)}."
        )

    if intelligence["company_id"].duplicated().any():
        raise ValueError(
            "Duplicate company IDs detected."
        )

    intelligence.to_excel(
        INTELLIGENCE_FILE,
        sheet_name="cashflow_intelligence",
        index=False,
    )

    distress_alerts.to_csv(
        DISTRESS_FILE,
        index=False,
    )

    print()
    print("=== VALIDATION ===")

    print(
        f"Companies processed: {len(intelligence)}"
    )

    print(
        f"Unique companies: "
        f"{intelligence['company_id'].nunique()}"
    )

    print(
        "High distress:",
        (intelligence["Distress_level"] == "High").sum(),
    )

    print(
        "Medium distress:",
        (intelligence["Distress_level"] == "Medium").sum(),
    )

    print(
        "Low distress:",
        (intelligence["Distress_level"] == "Low").sum(),
    )

    print(
        "Strong/Healthy CFO-PAT:",
        intelligence["CFO_PAT_quality"].isin(
            ["Strong", "Healthy"]
        ).sum(),
    )

    print(
        "Deleveraging companies:",
        intelligence["Deleveraging_status"].isin(
            ["Strong Deleveraging", "Deleveraging"]
        ).sum(),
    )

    print()
    print(f"Excel output: {INTELLIGENCE_FILE}")
    print(f"Distress output: {DISTRESS_FILE}")
    print("=== DAY 31 COMPLETE ===")


if __name__ == "__main__":
    main()