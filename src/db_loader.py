from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data" / "db"
DB_PATH = DB_DIR / "n100.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
OUTPUT_DIR = PROJECT_ROOT / "output"
AUDIT_PATH = OUTPUT_DIR / "load_audit.csv"


TABLE_ORDER = [
    "companies",
    "analysis",
    "balancesheet",
    "cashflow",
    "documents",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "profitandloss",
    "prosandcons",
    "sectors",
    "stock_prices",
]


def native_value(value):
    """Convert pandas/NumPy values to SQLite-safe Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def load_database():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    try:
        # Rebuild database.
        connection.execute("PRAGMA foreign_keys = OFF")

        for table in reversed(TABLE_ORDER):
            connection.execute(
                f'DROP TABLE IF EXISTS "{table}"'
            )

        schema = SCHEMA_PATH.read_text(
            encoding="utf-8"
        )

        connection.executescript(schema)

        # FK enforcement ON for actual loading.
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        print("Loading N100 database...")

        # Load companies first.
        companies_file = PROCESSED_DIR / "companies.csv"

        companies_df = pd.read_csv(
            companies_file
        )

        company_ids = set(
            companies_df["id"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        audit_rows = []

        for table_name in TABLE_ORDER:
            csv_file = (
                PROCESSED_DIR /
                f"{table_name}.csv"
            )

            if not csv_file.exists():
                continue

            df = pd.read_csv(csv_file)

            # companies is the master table.
            if table_name == "companies":
                load_df = df.copy()
            else:
                load_df = df.copy()

                # Child tables must only contain
                # companies from the master list.
                if "company_id" in load_df.columns:
                    before = len(load_df)

                    load_df["company_id"] = (
                        load_df["company_id"]
                        .astype(str)
                        .str.strip()
                    )

                    # Correct known source ticker typo.
                    load_df["company_id"] = (
                        load_df["company_id"]
                        .replace({
                            "AGTL": "ATGL"
                        })
                    )

                    load_df = load_df[
                        load_df["company_id"].isin(
                            company_ids
                        )
                    ].copy()

                    rejected = before - len(load_df)
                else:
                    rejected = 0

            rows = [
                tuple(
                    native_value(value)
                    for value in row
                )
                for row in load_df.itertuples(
                    index=False,
                    name=None,
                )
            ]

            columns = list(load_df.columns)

            quoted_columns = ", ".join(
                f'"{column}"'
                for column in columns
            )

            placeholders = ", ".join(
                "?" for _ in columns
            )

            sql = (
                f'INSERT INTO "{table_name}" '
                f"({quoted_columns}) "
                f"VALUES ({placeholders})"
            )

            try:
                connection.executemany(
                    sql,
                    rows,
                )

                connection.commit()

                print(
                    f"{table_name}: "
                    f"{len(rows)} rows loaded, "
                    f"{rejected if table_name != 'companies' else 0} rejected"
                )

                audit_rows.append(
                    {
                        "table_name": table_name,
                        "source_file": csv_file.name,
                        "rows_loaded": len(rows),
                        "rows_rejected": (
                            rejected
                            if table_name != "companies"
                            else 0
                        ),
                        "status": (
                            "SUCCESS"
                            if (
                                table_name == "companies"
                                or rejected == 0
                            )
                            else "FILTERED_INVALID_FK"
                        ),
                    }
                )

            except Exception as exc:
                connection.rollback()

                print(
                    f"ERROR loading {table_name}: "
                    f"{type(exc).__name__}: {exc}"
                )

                audit_rows.append(
                    {
                        "table_name": table_name,
                        "source_file": csv_file.name,
                        "rows_loaded": 0,
                        "rows_rejected": len(df),
                        "status": "CRITICAL_REJECTION",
                    }
                )

        # Final FK check.
        fk_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if fk_errors:
            print(
                "Foreign-key violations:"
            )
            for error in fk_errors:
                print(error)
        else:
            print(
                "Foreign-key check: 0 violations"
            )

        connection.commit()

        audit = pd.DataFrame(
            audit_rows,
            columns=[
                "table_name",
                "source_file",
                "rows_loaded",
                "rows_rejected",
                "status",
            ],
        )

        audit.to_csv(
            AUDIT_PATH,
            index=False,
        )

        print(
            f"\nDatabase created: {DB_PATH}"
        )

        print(
            f"Load audit saved: {AUDIT_PATH}"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    load_database()