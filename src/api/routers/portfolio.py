"""Module providing N100 financial intelligence functionality."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "db" / "n100.db"

router = APIRouter(tags=["Portfolio"])


def get_connection():
    """Retrieve connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/portfolio/stats")
def portfolio_stats():
    """Handle portfolio stats."""
    conn = get_connection()

    try:
        company_count = conn.execute("""
            SELECT COUNT(*)
            FROM companies
            """).fetchone()[0]

        latest_ratios = conn.execute("""
            SELECT
                fr.company_id,
                fr.return_on_equity_pct,
                fr.debt_to_equity,
                fr.revenue_cagr_5yr,
                fr.operating_profit_margin_pct,
                fr.composite_quality_score,
                fr.free_cash_flow_cr
            FROM financial_ratios fr
            INNER JOIN (
                SELECT company_id, MAX(year) AS max_year
                FROM financial_ratios
                GROUP BY company_id
            ) latest
                ON latest.company_id = fr.company_id
                AND latest.max_year = fr.year
            """).fetchall()

        latest_market = conn.execute("""
            SELECT
                mc.company_id,
                mc.market_cap_crore,
                mc.pe_ratio,
                mc.dividend_yield_pct
            FROM market_cap mc
            INNER JOIN (
                SELECT company_id, MAX(year) AS max_year
                FROM market_cap
                GROUP BY company_id
            ) latest
                ON latest.company_id = mc.company_id
                AND latest.max_year = mc.year
            """).fetchall()

        def average(rows, key):
            """Handle average."""
            values = [row[key] for row in rows if row[key] is not None]

            if not values:
                return None

            return round(sum(values) / len(values), 2)

        kpis = {
            "company_count": company_count,
            "average_roe_pct": average(
                latest_ratios,
                "return_on_equity_pct",
            ),
            "average_debt_to_equity": average(
                latest_ratios,
                "debt_to_equity",
            ),
            "average_revenue_cagr_5yr_pct": average(
                latest_ratios,
                "revenue_cagr_5yr",
            ),
            "average_operating_profit_margin_pct": average(
                latest_ratios,
                "operating_profit_margin_pct",
            ),
            "average_composite_quality_score": average(
                latest_ratios,
                "composite_quality_score",
            ),
            "average_free_cash_flow_cr": average(
                latest_ratios,
                "free_cash_flow_cr",
            ),
            "average_market_cap_crore": average(
                latest_market,
                "market_cap_crore",
            ),
            "average_pe_ratio": average(
                latest_market,
                "pe_ratio",
            ),
            "average_dividend_yield_pct": average(
                latest_market,
                "dividend_yield_pct",
            ),
        }

        return {
            "count": len(kpis),
            "kpis": kpis,
            "ratio_companies": len(latest_ratios),
            "market_data_companies": len(latest_market),
        }

    finally:
        conn.close()
