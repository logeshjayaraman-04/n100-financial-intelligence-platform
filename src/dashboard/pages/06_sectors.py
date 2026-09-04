from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_pl,
    get_ratios,
)


st.title("Sector Analysis")

st.write(
    "Explore company fundamentals and sector-level benchmarks."
)


# ---------------------------------------------------------
# Load companies
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


# ---------------------------------------------------------
# Sector selector
# ---------------------------------------------------------

sectors = sorted(
    companies["broad_sector"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


if not sectors:
    st.warning("No sector data is available.")
    st.stop()


selected_sector = st.selectbox(
    "Select sector",
    sectors,
)


sector_df = companies[
    companies["broad_sector"].astype(str)
    == selected_sector
].copy()


if sector_df.empty:
    st.warning(
        "No companies are available for this sector."
    )
    st.stop()


# ---------------------------------------------------------
# Load company financial data
# ---------------------------------------------------------

financial_rows = []


for _, company in sector_df.iterrows():

    company_id = company["company_id"]

    ratios = get_ratios(company_id)

    if ratios.empty:
        continue

    ratios = ratios.copy()

    ratios["year_num"] = pd.to_numeric(
        ratios["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})",
            expand=False,
        ),
        errors="coerce",
    )

    ratios = ratios.dropna(
        subset=["year_num"]
    )

    if ratios.empty:
        continue

    ratios = ratios.sort_values(
        "year_num"
    )

    latest = ratios.iloc[-1]

    revenue = None

    pl = get_pl(company_id)

    if not pl.empty:

        pl = pl.copy()

        pl["year_num"] = pd.to_numeric(
            pl["year"]
            .astype(str)
            .str.extract(
                r"(\d{4})",
                expand=False,
            ),
            errors="coerce",
        )

        pl = pl.dropna(
            subset=["year_num"]
        )

        if not pl.empty:

            pl = pl.sort_values(
                "year_num"
            )

            latest_pl = pl.iloc[-1]

            revenue = latest_pl.get(
                "sales"
            )

    financial_rows.append(
        {
            "company_id": company_id,
            "company_name": company[
                "company_name"
            ],
            "sub_sector": company[
                "sub_sector"
            ],
            "revenue": revenue,
            "roe": latest.get(
                "return_on_equity_pct"
            ),
            "market_cap": None,
        }
    )


financial_df = pd.DataFrame(
    financial_rows
)


# ---------------------------------------------------------
# Market cap from database
# ---------------------------------------------------------

try:

    import sqlite3
    from pathlib import Path

    db_path = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "db"
        / "n100.db"
    )

    with sqlite3.connect(db_path) as conn:

        market_cap_df = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                market_cap_crore
            FROM market_cap
            """,
            conn,
        )

except Exception:

    market_cap_df = pd.DataFrame()


if not market_cap_df.empty:

    market_cap_df["year_num"] = pd.to_numeric(
        market_cap_df["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})",
            expand=False,
        ),
        errors="coerce",
    )

    market_cap_df = market_cap_df.dropna(
        subset=["year_num"]
    )

    market_cap_df = (
        market_cap_df
        .sort_values(
            "year_num"
        )
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    market_cap_df = market_cap_df[
        [
            "company_id",
            "market_cap_crore",
        ]
    ]

    financial_df = financial_df.merge(
        market_cap_df,
        on="company_id",
        how="left",
    )

    financial_df["market_cap"] = (
        financial_df["market_cap_crore"]
    )


# ---------------------------------------------------------
# Convert numeric columns
# ---------------------------------------------------------

for column in [
    "revenue",
    "roe",
    "market_cap",
]:

    if column in financial_df.columns:

        financial_df[column] = pd.to_numeric(
            financial_df[column],
            errors="coerce",
        )


# ---------------------------------------------------------
# Bubble chart
# ---------------------------------------------------------

st.subheader(
    f"{selected_sector} — Company Overview"
)


bubble_df = financial_df.dropna(
    subset=[
        "revenue",
        "roe",
    ]
).copy()


if bubble_df.empty:

    st.info(
        "Revenue and ROE data are not available "
        "for this sector."
    )

else:

    # Prevent zero/negative marker sizes.
    bubble_df["bubble_size"] = (
        bubble_df["market_cap"]
        .fillna(0)
        .clip(lower=1)
    )

    fig = px.scatter(
        bubble_df,
        x="revenue",
        y="roe",
        size="bubble_size",
        color="sub_sector",
        hover_name="company_name",
        hover_data=[
            "company_id",
            "revenue",
            "roe",
            "market_cap",
            "sub_sector",
        ],
        labels={
            "revenue": "Revenue",
            "roe": "ROE (%)",
            "bubble_size": "Market Cap",
            "sub_sector": "Sub-sector",
        },
        title=(
            f"{selected_sector} — "
            "Revenue vs ROE"
        ),
    )

    fig.update_layout(
        height=600,
        margin=dict(
            l=50,
            r=40,
            t=70,
            b=50,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------
# Sector median KPIs
# ---------------------------------------------------------

st.subheader("Sector Median KPIs")


kpi_columns = {
    "ROE": "roe",
    "Revenue": "revenue",
    "Market Cap": "market_cap",
}


median_rows = []


for label, column in kpi_columns.items():

    if column not in financial_df.columns:
        continue

    values = pd.to_numeric(
        financial_df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        continue

    median_rows.append(
        {
            "Metric": label,
            "Median": values.median(),
        }
    )


median_df = pd.DataFrame(
    median_rows
)


if median_df.empty:

    st.info(
        "Sector median data is not available."
    )

else:

    median_df["Median"] = median_df[
        "Median"
    ].round(2)

    fig = px.bar(
        median_df,
        x="Metric",
        y="Median",
        text="Median",
        title=(
            f"{selected_sector} — "
            "Sector Median"
        ),
    )

    fig.update_layout(
        height=450,
        margin=dict(
            l=50,
            r=40,
            t=70,
            b=50,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------
# Company table
# ---------------------------------------------------------

st.subheader("Sector Companies")


table_df = financial_df[
    [
        "company_id",
        "company_name",
        "sub_sector",
        "revenue",
        "roe",
        "market_cap",
    ]
].copy()


table_df = table_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "sub_sector": "Sub-sector",
        "revenue": "Revenue",
        "roe": "ROE",
        "market_cap": "Market Cap",
    }
)


for column in [
    "Revenue",
    "ROE",
    "Market Cap",
]:

    table_df[column] = pd.to_numeric(
        table_df[column],
        errors="coerce",
    ).round(2)


st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
)