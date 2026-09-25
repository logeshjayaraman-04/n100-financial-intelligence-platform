"""Module providing N100 financial intelligence functionality."""

import csv
import sqlite3
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_FILE = ROOT_DIR / "data" / "db" / "n100.db"
OUTPUT_FILE = ROOT_DIR / "output" / "pros_cons_generated.csv"


# ============================================================
# CONFIGURATION
# ============================================================

MIN_CONFIDENCE = 60


# ============================================================
# 12 PRO RULES
# ============================================================

PRO_RULES = [
    {
        "rule_id": "PRO01",
        "metric": "revenue_cagr_5yr",
        "condition": lambda x: x >= 15,
        "text": "Strong 5-year revenue growth",
        "confidence": lambda x: min(95, 65 + (x - 15) * 2),
    },
    {
        "rule_id": "PRO02",
        "metric": "pat_cagr_5yr",
        "condition": lambda x: x >= 15,
        "text": "Strong 5-year profit growth",
        "confidence": lambda x: min(95, 65 + (x - 15) * 2),
    },
    {
        "rule_id": "PRO03",
        "metric": "return_on_equity_pct",
        "condition": lambda x: x >= 15,
        "text": "Healthy return on equity",
        "confidence": lambda x: min(95, 65 + (x - 15) * 1.5),
    },
    {
        "rule_id": "PRO04",
        "metric": "operating_profit_margin_pct",
        "condition": lambda x: x >= 15,
        "text": "Healthy operating margin",
        "confidence": lambda x: min(95, 65 + (x - 15) * 1.5),
    },
    {
        "rule_id": "PRO05",
        "metric": "net_profit_margin_pct",
        "condition": lambda x: x >= 10,
        "text": "Healthy net profit margin",
        "confidence": lambda x: min(95, 65 + (x - 10) * 1.5),
    },
    {
        "rule_id": "PRO06",
        "metric": "interest_coverage",
        "condition": lambda x: x >= 5,
        "text": "Strong interest coverage",
        "confidence": lambda x: min(95, 70 + (x - 5) * 2),
    },
    {
        "rule_id": "PRO07",
        "metric": "debt_to_equity",
        "condition": lambda x: x <= 0.5,
        "text": "Conservative debt-to-equity profile",
        "confidence": lambda x: min(95, 65 + (0.5 - x) * 30),
    },
    {
        "rule_id": "PRO08",
        "metric": "free_cash_flow_cr",
        "condition": lambda x: x > 0,
        "text": "Positive free cash flow",
        "confidence": lambda x: 80,
    },
    {
        "rule_id": "PRO09",
        "metric": "cash_from_operations_cr",
        "condition": lambda x: x > 0,
        "text": "Positive operating cash flow",
        "confidence": lambda x: 80,
    },
    {
        "rule_id": "PRO10",
        "metric": "eps_cagr_5yr",
        "condition": lambda x: x >= 10,
        "text": "Positive long-term EPS growth",
        "confidence": lambda x: min(95, 65 + (x - 10) * 2),
    },
    {
        "rule_id": "PRO11",
        "metric": "composite_quality_score",
        "condition": lambda x: x >= 70,
        "text": "High composite quality score",
        "confidence": lambda x: min(95, x),
    },
    {
        "rule_id": "PRO12",
        "metric": "asset_turnover",
        "condition": lambda x: x >= 0.5,
        "text": "Reasonable asset utilization",
        "confidence": lambda x: min(95, 65 + x * 20),
    },
]


# ============================================================
# 12 CON RULES
# ============================================================

CON_RULES = [
    {
        "rule_id": "CON01",
        "metric": "revenue_cagr_5yr",
        "condition": lambda x: x < 5,
        "text": "Weak 5-year revenue growth",
        "confidence": lambda x: min(95, 65 + (5 - x) * 3),
    },
    {
        "rule_id": "CON02",
        "metric": "pat_cagr_5yr",
        "condition": lambda x: x < 5,
        "text": "Weak 5-year profit growth",
        "confidence": lambda x: min(95, 65 + (5 - x) * 3),
    },
    {
        "rule_id": "CON03",
        "metric": "return_on_equity_pct",
        "condition": lambda x: x < 10,
        "text": "Low return on equity",
        "confidence": lambda x: min(95, 65 + (10 - x) * 2),
    },
    {
        "rule_id": "CON04",
        "metric": "operating_profit_margin_pct",
        "condition": lambda x: x < 10,
        "text": "Low operating margin",
        "confidence": lambda x: min(95, 65 + (10 - x) * 2),
    },
    {
        "rule_id": "CON05",
        "metric": "net_profit_margin_pct",
        "condition": lambda x: x < 5,
        "text": "Low net profit margin",
        "confidence": lambda x: min(95, 65 + (5 - x) * 3),
    },
    {
        "rule_id": "CON06",
        "metric": "interest_coverage",
        "condition": lambda x: x < 2,
        "text": "Weak interest coverage",
        "confidence": lambda x: min(95, 65 + (2 - x) * 10),
    },
    {
        "rule_id": "CON07",
        "metric": "debt_to_equity",
        "condition": lambda x: x > 1,
        "text": "High debt-to-equity profile",
        "confidence": lambda x: min(95, 65 + (x - 1) * 10),
    },
    {
        "rule_id": "CON08",
        "metric": "free_cash_flow_cr",
        "condition": lambda x: x < 0,
        "text": "Negative free cash flow",
        "confidence": lambda x: 85,
    },
    {
        "rule_id": "CON09",
        "metric": "cash_from_operations_cr",
        "condition": lambda x: x < 0,
        "text": "Negative operating cash flow",
        "confidence": lambda x: 85,
    },
    {
        "rule_id": "CON10",
        "metric": "eps_cagr_5yr",
        "condition": lambda x: x < 0,
        "text": "Declining long-term EPS",
        "confidence": lambda x: min(95, 70 + abs(x) * 2),
    },
    {
        "rule_id": "CON11",
        "metric": "composite_quality_score",
        "condition": lambda x: x < 50,
        "text": "Low composite quality score",
        "confidence": lambda x: min(95, 100 - x),
    },
    {
        "rule_id": "CON12",
        "metric": "asset_turnover",
        "condition": lambda x: x < 0.3,
        "text": "Low asset utilization",
        "confidence": lambda x: min(95, 65 + (0.3 - x) * 100),
    },
]


# ============================================================
# DATABASE
# ============================================================


def load_latest_ratios():
    """
    Load the latest available financial-ratio row for every company.
    """

    conn = sqlite3.connect(DB_FILE)

    query = """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            free_cash_flow_cr,
            cash_from_operations_cr,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr,
            composite_quality_score
        FROM financial_ratios
        WHERE year = (
            SELECT MAX(fr2.year)
            FROM financial_ratios fr2
            WHERE fr2.company_id = financial_ratios.company_id
        )
        ORDER BY company_id
    """

    rows = conn.execute(query).fetchall()
    columns = [description[0] for description in conn.execute(query).description]

    conn.close()

    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# RULE EVALUATION
# ============================================================


def evaluate_rules(row):
    """Handle evaluate rules."""
    results = []

    for rule in PRO_RULES + CON_RULES:
        metric = rule["metric"]
        value = row.get(metric)

        if value is None:
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if rule["condition"](value):
            confidence = rule["confidence"](value)

            confidence = max(0, min(100, round(confidence, 2)))

            if confidence > MIN_CONFIDENCE:
                result_type = "pro" if rule["rule_id"].startswith("PRO") else "con"

                results.append(
                    {
                        "company_id": row["company_id"],
                        "type": result_type,
                        "rule_id": rule["rule_id"],
                        "text": rule["text"],
                        "confidence_pct": confidence,
                    }
                )

    return results


# ============================================================
# FALLBACK RULES
# ============================================================


def apply_fallbacks(row, results):
    """
    Guarantee at least one pro and one con where the available
    financial data permits a meaningful classification.
    """

    has_pro = any(r["type"] == "pro" for r in results)
    has_con = any(r["type"] == "con" for r in results)

    company_id = row["company_id"]

    if not has_pro:
        results.append(
            {
                "company_id": company_id,
                "type": "pro",
                "rule_id": "PRO_FALLBACK",
                "text": "Financial profile contains at least one positive indicator",
                "confidence_pct": 61,
            }
        )

    if not has_con:
        results.append(
            {
                "company_id": company_id,
                "type": "con",
                "rule_id": "CON_FALLBACK",
                "text": "Financial profile warrants continued monitoring",
                "confidence_pct": 61,
            }
        )

    return results


# ============================================================
# MAIN GENERATOR
# ============================================================


def generate():
    """Handle generate."""
    print("=== NLP PROS/CONS GENERATOR ===")

    rows = load_latest_ratios()

    print(f"Companies found in financial_ratios: {len(rows)}")

    all_results = []

    for row in rows:
        results = evaluate_rules(row)
        results = apply_fallbacks(row, results)
        all_results.extend(results)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "company_id",
        "type",
        "rule_id",
        "text",
        "confidence_pct",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    company_ids = sorted({row["company_id"] for row in rows})

    pro_counts = {}
    con_counts = {}

    for result in all_results:
        company_id = result["company_id"]

        if result["type"] == "pro":
            pro_counts[company_id] = pro_counts.get(company_id, 0) + 1

        elif result["type"] == "con":
            con_counts[company_id] = con_counts.get(company_id, 0) + 1

    missing_pro = [
        company_id for company_id in company_ids if pro_counts.get(company_id, 0) == 0
    ]

    missing_con = [
        company_id for company_id in company_ids if con_counts.get(company_id, 0) == 0
    ]

    confidence_failures = [
        result
        for result in all_results
        if not (0 <= float(result["confidence_pct"]) <= 100)
    ]

    print(f"Generated rows: {len(all_results)}")
    print(f"Pro rows: {sum(pro_counts.values())}")
    print(f"Con rows: {sum(con_counts.values())}")
    print(f"Companies missing pro: {len(missing_pro)}")
    print(f"Companies missing con: {len(missing_con)}")
    print(f"Confidence failures: {len(confidence_failures)}")

    if missing_pro:
        print("Missing pro companies:")
        print(", ".join(missing_pro))

    if missing_con:
        print("Missing con companies:")
        print(", ".join(missing_con))

    if confidence_failures:
        raise ValueError("Confidence validation failed.")

    if missing_pro or missing_con:
        raise ValueError("Every company must have at least one pro and one con.")

    print(f"Output: {OUTPUT_FILE}")
    print("=== DAY 30 GENERATION COMPLETE ===")


if __name__ == "__main__":
    generate()
