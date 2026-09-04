from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "db"
    / "n100.db"
)


def _read_sql(query: str, params: tuple = ()) -> pd.DataFrame:
    """Run a read-only SQLite query and return a DataFrame."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Return the company master list with sector information."""
    return _read_sql(
        """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.about_company,
            c.website,
            c.nse_profile,
            c.bse_profile,
            c.face_value,
            c.book_value,
            c.roce_percentage,
            c.roe_percentage,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        ORDER BY c.company_name
        """
    )


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year=None) -> pd.DataFrame:
    """Return financial ratios for a company."""
    if year is None:
        return _read_sql(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
            """,
            (ticker,),
        )

    return _read_sql(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
          AND year = ?
        ORDER BY year
        """,
        (ticker, year),
    )


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Return profit and loss history."""
    return _read_sql(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Return balance sheet history."""
    return _read_sql(
        """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Return cash flow history."""
    return _read_sql(
        """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Return sector mapping."""
    return _read_sql(
        """
        SELECT *
        FROM sectors
        ORDER BY broad_sector, sub_sector, company_id
        """
    )


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """Return peer percentile data for one peer group."""
    return _read_sql(
        """
        SELECT *
        FROM peer_percentiles
        WHERE peer_group_name = ?
        ORDER BY company_id, metric
        """,
        (group_name,),
    )


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    """Return valuation data for one company from the valuation workbook."""
    valuation_path = (
        Path(__file__).resolve().parents[3]
        / "output"
        / "valuation_summary.xlsx"
    )

    if not valuation_path.exists():
        return pd.DataFrame()

    df = pd.read_excel(valuation_path)

    if "company_id" not in df.columns:
        return pd.DataFrame()

    return df[df["company_id"].astype(str) == str(ticker)].copy()


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> pd.DataFrame:
    """Return company pros and cons."""
    return _read_sql(
        """
        SELECT *
        FROM prosandcons
        WHERE company_id = ?
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_reports(ticker: str) -> pd.DataFrame:
    """Return annual report records."""
    return _read_sql(
        """
        SELECT *
        FROM documents
        WHERE company_id = ?
        ORDER BY year DESC
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_peer_groups() -> pd.DataFrame:
    """Return the peer-group membership table."""
    return _read_sql(
        """
        SELECT *
        FROM peer_groups
        ORDER BY peer_group_name, company_id
        """
    )