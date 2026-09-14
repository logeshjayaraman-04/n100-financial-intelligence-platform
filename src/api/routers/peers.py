from pathlib import Path
import sqlite3

from fastapi import APIRouter, HTTPException


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "db" / "n100.db"

router = APIRouter(tags=["Peers"])


def get_connection():
    """Return a SQLite connection with dictionary-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/peers")
def list_peer_groups():
    """Return peer groups with their company membership."""
    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                peer_group_name,
                COUNT(DISTINCT company_id) AS company_count
            FROM peer_groups
            GROUP BY peer_group_name
            ORDER BY peer_group_name
            """
        ).fetchall()

        return {
            "count": len(rows),
            "peer_groups": [dict(row) for row in rows],
        }

    finally:
        conn.close()


@router.get("/peers/{ticker}")
def company_peers(ticker: str):
    """Return the peer group membership for a company."""
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
                pg.peer_group_name,
                pg.company_id,
                c.company_name,
                pg.is_benchmark
            FROM peer_groups pg
            JOIN companies c
                ON c.id = pg.company_id
            WHERE pg.peer_group_name IN (
                SELECT peer_group_name
                FROM peer_groups
                WHERE company_id = ?
            )
            ORDER BY pg.peer_group_name, c.company_name
            """,
            (company["id"],),
        ).fetchall()

        return {
            "ticker": company["id"],
            "company_name": company["company_name"],
            "peers": [dict(row) for row in rows],
        }

    finally:
        conn.close()


@router.get("/peers/{ticker}/compare")
def peer_compare(ticker: str):
    """Compare the company with its peers using stored percentile metrics."""
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
                pp.company_id,
                c.company_name,
                pp.peer_group_name,
                pp.metric,
                pp.value,
                pp.percentile_rank,
                pp.year
            FROM peer_percentiles pp
            JOIN companies c
                ON c.id = pp.company_id
            WHERE pp.peer_group_name IN (
                SELECT peer_group_name
                FROM peer_groups
                WHERE company_id = ?
            )
            ORDER BY
                pp.peer_group_name,
                pp.metric,
                pp.percentile_rank DESC,
                c.company_name
            """,
            (company["id"],),
        ).fetchall()

        return {
            "ticker": company["id"],
            "company_name": company["company_name"],
            "comparisons": [dict(row) for row in rows],
        }

    finally:
        conn.close()