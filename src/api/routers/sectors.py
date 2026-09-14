from pathlib import Path
import sqlite3

from fastapi import APIRouter, HTTPException


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "db" / "n100.db"

router = APIRouter(tags=["Sectors"])


def get_connection():
    """Return a SQLite connection with dictionary-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/sectors")
def list_sectors():
    """Return sector summary information."""
    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                broad_sector,
                COUNT(DISTINCT company_id) AS company_count,
                SUM(index_weight_pct) AS total_index_weight_pct
            FROM sectors
            GROUP BY broad_sector
            ORDER BY broad_sector
            """
        ).fetchall()

        return {
            "count": len(rows),
            "sectors": [dict(row) for row in rows],
        }

    finally:
        conn.close()


@router.get("/sectors/{sector_name}/companies")
def sector_companies(sector_name: str):
    """Return companies belonging to a broad or sub-sector."""
    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                s.index_weight_pct,
                s.market_cap_category
            FROM companies c
            JOIN sectors s
                ON s.company_id = c.id
            WHERE
                LOWER(s.broad_sector) = LOWER(?)
                OR LOWER(s.sub_sector) = LOWER(?)
            ORDER BY c.company_name
            """,
            (sector_name, sector_name),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="Sector not found or contains no companies",
            )

        return {
            "sector": sector_name,
            "count": len(rows),
            "companies": [dict(row) for row in rows],
        }

    finally:
        conn.close()