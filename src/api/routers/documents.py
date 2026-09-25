"""Module providing N100 financial intelligence functionality."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "db" / "n100.db"

router = APIRouter(tags=["Documents"])


def get_connection():
    """Retrieve connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/documents/{ticker}")
def company_documents(ticker: str):
    """Handle company documents."""
    conn = get_connection()

    try:
        company = conn.execute(
            """
            SELECT id, company_name
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail="Company not found",
            )

        rows = conn.execute(
            """
            SELECT
                id,
                year,
                annual_report
            FROM documents
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            (company["id"],),
        ).fetchall()

        return {
            "ticker": company["id"],
            "company_name": company["company_name"],
            "count": len(rows),
            "documents": [dict(row) for row in rows],
        }

    finally:
        conn.close()
