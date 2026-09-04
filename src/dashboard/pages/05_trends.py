from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
)


st.title("Trend Analysis")

st.write(
    "Explore long-term financial trends for a selected company."
)


# ---------------------------------------------------------
# Load companies
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


# ---------------------------------------------------------
# Company search
# ---------------------------------------------------------

search_text = st.text_input(
    "Search company",
    placeholder="Enter company name or ticker",
)


filtered = companies.copy()


if search_text.strip():

    search_lower = search_text.strip().lower()

    filtered = filtered[
        filtered["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_lower,
            na=False,
        )
        |
        filtered["company_id"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_lower,
            na=False,
        )
    ]


if filtered.empty:

    st.warning(
        "No matching company was found. "
        "Please check the company name or ticker."
    )

    st.stop()


# ---------------------------------------------------------
# Company selector
# ---------------------------------------------------------

filtered = filtered.sort_values(
    "company_name"
)


company_labels = (
    filtered["company_name"].astype(str)
    + " ("
    + filtered["company_id"].astype(str)
    + ")"
).tolist()


selected_label = st.selectbox(
    "Select company",
    company_labels,
)


selected_row = filtered.iloc[
    company_labels.index(selected_label)
]


ticker = selected_row["company_id"]


# ---------------------------------------------------------
# Load ratios
# ---------------------------------------------------------

ratios = get_ratios(ticker)


if ratios.empty:

    st.warning(
        "Historical financial data is not available "
        "for this company."
    )

    st.stop()


# ---------------------------------------------------------
# Prepare year
# ---------------------------------------------------------

ratios = ratios.copy()


ratios["year_text"] = (
    ratios["year"]
    .astype(str)
)


ratios["year_num"] = pd.to_numeric(
    ratios["year_text"]
    .str.extract(r"(\d{4})", expand=False),
    errors="coerce",
)


ratios = ratios.dropna(
    subset=["year_num"]
)


ratios["year_num"] = (
    ratios["year_num"]
    .astype(int)
)


ratios = ratios.sort_values(
    "year_num"
)


# Keep latest 10 years
ratios = ratios.tail(10)


# ---------------------------------------------------------
# Available metrics
# ---------------------------------------------------------

metric_options = {
    "ROE": "return_on_equity_pct",
    "Operating Profit Margin": "operating_profit_margin_pct",
    "Net Profit Margin": "net_profit_margin_pct",
    "Debt to Equity": "debt_to_equity",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
    "Free Cash Flow": "free_cash_flow_cr",
    "Revenue CAGR (5Y)": "revenue_cagr_5yr",
    "PAT CAGR (5Y)": "pat_cagr_5yr",
    "EPS CAGR (5Y)": "eps_cagr_5yr",
}


available_metrics = [
    label
    for label, column in metric_options.items()
    if column in ratios.columns
]


# ---------------------------------------------------------
# Metric selector
# ---------------------------------------------------------

selected_metrics = st.multiselect(
    "Select up to 3 metrics",
    available_metrics,
    default=available_metrics[:2],
    max_selections=3,
)


if not selected_metrics:

    st.info(
        "Select at least one metric to display the trend."
    )

    st.stop()


# ---------------------------------------------------------
# Trend chart
# ---------------------------------------------------------

st.subheader("10-Year Financial Trends")


fig = go.Figure()


for metric in selected_metrics:

    column = metric_options[metric]

    values = pd.to_numeric(
        ratios[column],
        errors="coerce",
    )


    fig.add_trace(
        go.Scatter(
            x=ratios["year_num"],
            y=values,
            mode="lines+markers",
            name=metric,
        )
    )


fig.update_layout(
    height=550,
    hovermode="x unified",
    xaxis_title="Year",
    yaxis_title="Value",
    margin=dict(
        l=50,
        r=40,
        t=50,
        b=50,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# ---------------------------------------------------------
# YoY annotation
# ---------------------------------------------------------

st.subheader("Year-over-Year Change")


yoy_tables = []


for metric in selected_metrics:

    column = metric_options[metric]

    temp = ratios[
        [
            "year_num",
            column,
        ]
    ].copy()


    temp["Value"] = pd.to_numeric(
        temp[column],
        errors="coerce",
    )


    temp["YoY %"] = (
        temp["Value"]
        .pct_change()
        * 100
    )


    temp = temp[
        [
            "year_num",
            "Value",
            "YoY %",
        ]
    ]


    temp["Metric"] = metric


    yoy_tables.append(temp)


if yoy_tables:

    yoy_df = pd.concat(
        yoy_tables,
        ignore_index=True,
    )


    yoy_df = yoy_df.rename(
        columns={
            "year_num": "Year",
        }
    )


    yoy_df["Value"] = yoy_df[
        "Value"
    ].round(2)


    yoy_df["YoY %"] = yoy_df[
        "YoY %"
    ].round(2)


    st.dataframe(
        yoy_df[
            [
                "Year",
                "Metric",
                "Value",
                "YoY %",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.caption(
    f"Showing the latest {len(ratios)} available years "
    f"for {selected_row['company_name']} ({ticker})."
)