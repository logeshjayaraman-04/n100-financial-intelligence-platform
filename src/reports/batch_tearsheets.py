from pathlib import Path
import csv
import sqlite3

from tearsheet import generate_tearsheet


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "n100.db"

OUTPUT_DIR = ROOT / "reports" / "tearsheets"
SKIPPED_PATH = ROOT / "output" / "skipped_tearsheets.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SKIPPED_PATH.parent.mkdir(parents=True, exist_ok=True)


def count_financial_years(conn, company_id):
    """
    Count distinct financial periods available for a company.

    We use profitandloss as the primary annual-financial-data
    source because every tearsheet needs a meaningful historical
    financial series.
    """
    rows = conn.execute(
        """
        SELECT DISTINCT year
        FROM profitandloss
        WHERE company_id = ?
        """,
        (company_id,),
    ).fetchall()

    years = {
        str(row[0]).strip()
        for row in rows
        if row[0] is not None and str(row[0]).strip()
    }

    return len(years)


def get_companies():
    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute(
        """
        SELECT id, company_name
        FROM companies
        ORDER BY id
        """
    ).fetchall()

    conn.close()

    return rows


def main():
    print("=== DAY 34 FULL TEARSHEET BATCH ===")

    companies = get_companies()

    print(f"Companies found: {len(companies)}")
    print()

    generated = []
    skipped = []
    failures = []

    conn = sqlite3.connect(DB_PATH)

    for company_id, company_name in companies:
        year_count = count_financial_years(conn, company_id)

        if year_count < 3:
            skipped.append(
                {
                    "company_id": company_id,
                    "company_name": company_name,
                    "financial_years": year_count,
                    "reason": "Fewer than 3 financial years",
                }
            )

            print(
                f"SKIPPED: {company_id} | "
                f"{company_name} | "
                f"{year_count} years"
            )

            continue

        try:
            path = generate_tearsheet(company_id)

            generated.append(
                {
                    "company_id": company_id,
                    "company_name": company_name,
                    "path": str(path),
                    "financial_years": year_count,
                }
            )

            print(
                f"Generated: {company_id} | "
                f"{company_name} | "
                f"{year_count} years"
            )

        except Exception as exc:
            failures.append(
                {
                    "company_id": company_id,
                    "company_name": company_name,
                    "financial_years": year_count,
                    "error": str(exc),
                }
            )

            print(
                f"FAILED: {company_id} | "
                f"{company_name} | "
                f"{exc}"
            )

    conn.close()

    # --------------------------------------------------------
    # Write skipped_tearsheets.csv
    # --------------------------------------------------------

    with SKIPPED_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "company_id",
                "company_name",
                "financial_years",
                "reason",
            ],
        )

        writer.writeheader()
        writer.writerows(skipped)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=== BATCH VALIDATION ===")
    print(f"Companies in database: {len(companies)}")
    print(f"Tearsheets generated: {len(generated)}")
    print(f"Companies skipped: {len(skipped)}")
    print(f"Generation failures: {len(failures)}")
    print(f"Skipped file: {SKIPPED_PATH}")

    if failures:
        print()
        print("FAILURES:")
        for failure in failures:
            print(
                failure["company_id"],
                "|",
                failure["company_name"],
                "|",
                failure["error"],
            )

    print()
    print("=== DAY 34 FULL TEARSHEET BATCH COMPLETE ===")


if __name__ == "__main__":
    main()