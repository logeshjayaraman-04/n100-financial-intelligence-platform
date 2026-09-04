from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import get_companies, get_ratios


st.title("Nifty 100 Analytics")
st.subheader("Market Overview")


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("No company data available.")
    st.stop()


# ---------------------------------------------------------
# Year selector
# ---------------------------------------------------------

years = list(range(2019, 2025))

selected_year = st.sidebar.selectbox(
    "Select Year",
    years,
    index=len(years) - 1,
)


# ---------------------------------------------------------
# Load latest ratios for all companies
# ---------------------------------------------------------

ratio_frames = []

for company_id in companies["company_id"].dropna().unique():
    try:
        ratios = get_ratios(str(company_id), selected_year)

        if not ratios.empty:
            latest = ratios.sort_values("year").tail(1).copy()
            ratio_frames.append(latest)
    except Exception:
        continue


if ratio_frames:
    ratios_df = pd.concat(ratio_frames, ignore_index=True)
else:
    ratios_df = pd.DataFrame()


# ---------------------------------------------------------
# Merge company + ratio data
# ---------------------------------------------------------

if not ratios_df.empty:
    data = companies.merge(
        ratios_df,
        on="company_id",
        how="left",
        suffixes=("", "_ratio"),
    )
else:
    data = companies.copy()


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def numeric_median(column: str):
    if column not in data.columns:
        return None

    values = pd.to_numeric(data[column], errors="coerce").dropna()

    if values.empty:
        return None

    return values.median()


def numeric_mean(column: str):
    if column not in data.columns:
        return None

    values = pd.to_numeric(data[column], errors="coerce").dropna()

    if values.empty:
        return None

    return values.mean()


# ---------------------------------------------------------
# KPI values
# ---------------------------------------------------------

average_roe = numeric_mean("return_on_equity_pct")

median_pe = None
median_de = numeric_median("debt_to_equity")
median_revenue_cagr = numeric_median("revenue_cagr_5yr")

if "market_cap" in data.columns:
    median_pe = numeric_median("pe_ratio")


# P/E is stored in market_cap, so load latest market data
try:
    from src.dashboard.utils.db import _read_sql

    market_df = _read_sql(
        """
        SELECT company_id, year, pe_ratio
        FROM market_cap
        WHERE year = ?
        """,
        (selected_year,),
    )

    if not market_df.empty:
        data = data.drop(columns=["pe_ratio"], errors="ignore")
        data = data.merge(
            market_df,
            on="company_id",
            how="left",
        )

        median_pe = numeric_median("pe_ratio")

except Exception:
    pass


debt_free_count = 0

if "debt_to_equity" in data.columns:
    de_values = pd.to_numeric(
        data["debt_to_equity"],
        errors="coerce",
    )

    debt_free_count = int((de_values == 0).sum())


# ---------------------------------------------------------
# KPI tiles
# ---------------------------------------------------------

col1, col2, col3, col4, col5, col6 = st.columns(6)


with col1:
    st.metric(
        "Average ROE",
        f"{average_roe:.2f}%" if average_roe is not None else "N/A",
    )


with col2:
    st.metric(
        "Median P/E",
        f"{median_pe:.2f}" if median_pe is not None else "N/A",
    )


with col3:
    st.metric(
        "Median D/E",
        f"{median_de:.2f}" if median_de is not None else "N/A",
    )


with col4:
    st.metric(
        "Total Companies",
        f"{len(companies):,}",
    )


with col5:
    st.metric(
        "Median Revenue CAGR 5yr",
        (
            f"{median_revenue_cagr:.2f}%"
            if median_revenue_cagr is not None
            else "N/A"
        ),
    )


with col6:
    st.metric(
        "Debt-Free Companies",
        f"{debt_free_count:,}",
    )


# ---------------------------------------------------------
# Sector breakdown
# ---------------------------------------------------------

st.divider()

left, right = st.columns([1, 1])


with left:
    st.subheader("Sector Breakdown")

    sector_counts = (
        companies["broad_sector"]
        .fillna("Unknown")
        .value_counts()
        .reset_index()
    )

    sector_counts.columns = ["broad_sector", "company_count"]

    fig_sector = px.pie(
        sector_counts,
        names="broad_sector",
        values="company_count",
        hole=0.45,
        title="Companies by Sector",
    )

    fig_sector.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    st.plotly_chart(
        fig_sector,
        use_container_width=True,
    )


# ---------------------------------------------------------
# Top 5 companies
# ---------------------------------------------------------

with right:
    st.subheader("Top 5 Companies by Composite Quality Score")

    if "composite_quality_score" in data.columns:

        top5 = data[
            [
                "company_id",
                "company_name",
                "broad_sector",
                "composite_quality_score",
            ]
        ].copy()

        top5["composite_quality_score"] = pd.to_numeric(
            top5["composite_quality_score"],
            errors="coerce",
        )

        top5 = (
            top5
            .dropna(subset=["composite_quality_score"])
            .sort_values(
                "composite_quality_score",
                ascending=False,
            )
            .head(5)
        )

        top5["composite_quality_score"] = top5[
            "composite_quality_score"
        ].round(2)

        st.dataframe(
            top5,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "Composite quality score is not available for the selected year."
        )


# ---------------------------------------------------------
# Footer information
# ---------------------------------------------------------

st.divider()

st.caption(
    f"Dashboard data view: {selected_year} | "
    f"Companies available: {len(companies)}"
)