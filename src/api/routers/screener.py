"""Module providing N100 financial intelligence functionality."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Query

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "db" / "n100.db"

router = APIRouter(tags=["Screener"])


def get_connection():
    """Return a SQLite connection with dictionary-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/screener")
def screener(
    min_roe: float | None = Query(None),
    max_debt_to_equity: float | None = Query(None),
    min_revenue_cagr: float | None = Query(None),
    min_opm: float | None = Query(None),
    min_quality_score: float | None = Query(None),
    sector: str | None = Query(None),
    market_cap_category: str | None = Query(None),
):
    """
    Screen companies using financial quality and growth filters.
    """

    conn = get_connection()

    try:
        query = """
            SELECT
                c.id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                s.market_cap_category,
                fr.year,
                fr.return_on_equity_pct AS roe_pct,
                fr.debt_to_equity,
                fr.revenue_cagr_5yr,
                fr.operating_profit_margin_pct AS opm_pct,
                fr.composite_quality_score
            FROM companies c
            LEFT JOIN sectors s
                ON s.company_id = c.id
            LEFT JOIN financial_ratios fr
                ON fr.company_id = c.id
            WHERE fr.year = (
                SELECT MAX(fr2.year)
                FROM financial_ratios fr2
                WHERE fr2.company_id = c.id
            )
        """

        params = []

        if min_roe is not None:
            query += " AND fr.return_on_equity_pct >= ?"
            params.append(min_roe)

        if max_debt_to_equity is not None:
            query += " AND fr.debt_to_equity <= ?"
            params.append(max_debt_to_equity)

        if min_revenue_cagr is not None:
            query += " AND fr.revenue_cagr_5yr >= ?"
            params.append(min_revenue_cagr)

        if min_opm is not None:
            query += " AND fr.operating_profit_margin_pct >= ?"
            params.append(min_opm)

        if min_quality_score is not None:
            query += " AND fr.composite_quality_score >= ?"
            params.append(min_quality_score)

        if sector:
            query += """
                AND (
                    LOWER(s.broad_sector) = LOWER(?)
                    OR LOWER(s.sub_sector) = LOWER(?)
                )
            """
            params.extend([sector, sector])

        if market_cap_category:
            query += """
                AND LOWER(s.market_cap_category) = LOWER(?)
            """
            params.append(market_cap_category)

        query += """
            ORDER BY
                fr.composite_quality_score DESC,
                fr.return_on_equity_pct DESC,
                c.company_name
        """

        rows = conn.execute(query, params).fetchall()

        return {
            "count": len(rows),
            "results": [dict(row) for row in rows],
        }

    finally:
        conn.close()
