"""Module providing N100 financial intelligence functionality."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "db" / "n100.db"
TEARSHEET_DIR = ROOT / "reports" / "tearsheets"

router = APIRouter(tags=["Companies"])


def get_connection():
    """Return a SQLite connection with row dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dict(rows):
    """Convert SQLite rows to dictionaries."""
    return [dict(row) for row in rows]


def get_company(conn, ticker):
    """Return a company record by ticker/company ID."""
    return conn.execute(
        """
        SELECT *
        FROM companies
        WHERE UPPER(id) = UPPER(?)
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()


def get_year_filter(year_value):
    """Extract a four-digit year from an API year parameter."""
    if year_value is None:
        return None

    value = str(year_value).strip()

    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])

    raise HTTPException(
        status_code=400,
        detail="Year must use YYYY or YYYY-MM format.",
    )


@router.get("")
def list_companies(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
):
    """Return companies with optional sector, market-cap and name filters."""
    conn = get_connection()

    try:
        query = """
            SELECT
                c.id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                c.roe_percentage AS roe_pct,
                c.roce_percentage AS roce_pct,
                s.market_cap_category
            FROM companies c
            LEFT JOIN sectors s
                ON s.company_id = c.id
            WHERE 1=1
        """

        params = []

        if sector:
            query += """
                AND (
                    LOWER(s.broad_sector) = LOWER(?)
                    OR LOWER(s.sub_sector) = LOWER(?)
                )
            """
            params.extend([sector, sector])

        if market_cap_category:
            query += " AND LOWER(s.market_cap_category) = LOWER(?)"
            params.append(market_cap_category)

        if search:
            query += """
                AND (
                    LOWER(c.id) LIKE LOWER(?)
                    OR LOWER(c.company_name) LIKE LOWER(?)
                )
            """
            search_value = f"%{search}%"
            params.extend([search_value, search_value])

        query += " ORDER BY c.company_name"

        rows = conn.execute(query, params).fetchall()
        return rows_to_dict(rows)

    finally:
        conn.close()


@router.get("/{ticker}/pl")
def company_profit_loss(
    ticker: str,
    from_year: str | None = None,
    to_year: str | None = None,
):
    """Return company profit-and-loss history."""
    conn = get_connection()

    try:
        company = get_company(conn, ticker)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        query = """
            SELECT *
            FROM profitandloss
            WHERE company_id = ?
        """
        params = [company["id"]]

        start = get_year_filter(from_year)
        end = get_year_filter(to_year)

        if start is not None:
            query += """
                AND CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) >= ?
            """
            params.append(start)

        if end is not None:
            query += """
                AND CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) <= ?
            """
            params.append(end)

        query += """
            ORDER BY CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER)
        """

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": company["id"],
            "history": rows_to_dict(rows),
        }

    finally:
        conn.close()


@router.get("/{ticker}/bs")
def company_balance_sheet(
    ticker: str,
    from_year: str | None = None,
    to_year: str | None = None,
):
    """Return company balance-sheet history."""
    conn = get_connection()

    try:
        company = get_company(conn, ticker)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        query = """
            SELECT *
            FROM balancesheet
            WHERE company_id = ?
        """
        params = [company["id"]]

        start = get_year_filter(from_year)
        end = get_year_filter(to_year)

        if start is not None:
            query += """
                AND CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) >= ?
            """
            params.append(start)

        if end is not None:
            query += """
                AND CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) <= ?
            """
            params.append(end)

        query += """
            ORDER BY CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER)
        """

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": company["id"],
            "history": rows_to_dict(rows),
        }

    finally:
        conn.close()


@router.get("/{ticker}/cashflow")
def company_cash_flow(
    ticker: str,
    from_year: str | None = None,
    to_year: str | None = None,
):
    """Return company cash-flow history."""
    conn = get_connection()

    try:
        company = get_company(conn, ticker)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        query = """
            SELECT *
            FROM cashflow
            WHERE company_id = ?
        """
        params = [company["id"]]

        start = get_year_filter(from_year)
        end = get_year_filter(to_year)

        if start is not None:
            query += """
                AND CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) >= ?
            """
            params.append(start)

        if end is not None:
            query += """
                AND CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) <= ?
            """
            params.append(end)

        query += """
            ORDER BY CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER)
        """

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": company["id"],
            "history": rows_to_dict(rows),
        }

    finally:
        conn.close()


@router.get("/{ticker}/ratios")
def company_ratios(
    ticker: str,
    year: str | None = None,
):
    """Return computed financial ratios by year."""
    conn = get_connection()

    try:
        company = get_company(conn, ticker)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        query = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
        """
        params = [company["id"]]

        selected_year = get_year_filter(year)

        if selected_year is not None:
            query += """
                AND CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) = ?
            """
            params.append(selected_year)

        query += """
            ORDER BY CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER)
        """

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": company["id"],
            "history": rows_to_dict(rows),
        }

    finally:
        conn.close()


@router.get("/{ticker}/tearsheet")
def company_tearsheet(ticker: str):
    """Return the pre-generated company tearsheet PDF."""
    conn = get_connection()

    try:
        company = get_company(conn, ticker)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        company_id = company["id"]
    finally:
        conn.close()

    candidates = [
        TEARSHEET_DIR / f"{company_id}_tearsheet.pdf",
        TEARSHEET_DIR / f"{company_id}.pdf",
    ]

    pdf_path = next((path for path in candidates if path.exists()), None)

    if pdf_path is None:
        raise HTTPException(
            status_code=404,
            detail="Tearsheet PDF not found",
        )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )


@router.get("/{ticker}")
def company_profile(ticker: str):
    """Return full company profile with latest KPI and sector data."""
    conn = get_connection()

    try:
        company = get_company(conn, ticker)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        company_id = company["id"]

        sector = conn.execute(
            """
            SELECT *
            FROM sectors
            WHERE company_id = ?
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        latest = conn.execute(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY
                CAST(substr(CAST(year AS TEXT), 1, 4) AS INTEGER) DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        return {
            "profile": dict(company),
            "sector": dict(sector) if sector else None,
            "latest_kpis": dict(latest) if latest else None,
        }

    finally:
        conn.close()
