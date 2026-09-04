from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_pros_cons,
)


st.title("Company Profile")

# ---------------------------------------------------------
# Load companies
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("No company data available.")
    st.stop()


# ---------------------------------------------------------
# Company search
# ---------------------------------------------------------

search_text = st.text_input(
    "Search company or ticker",
    placeholder="Type company name or ticker...",
)


if search_text.strip():

    search = search_text.strip().lower()

    matches = companies[
        companies["company_id"]
        .astype(str)
        .str.lower()
        .str.contains(search, na=False)
        |
        companies["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(search, na=False)
    ].copy()

    if matches.empty:
        st.warning("Ticker not found — please try another")
        st.stop()

    selected_company = st.selectbox(
        "Select company",
        matches["company_id"].tolist(),
        format_func=lambda x: (
            f"{x} — "
            f"{matches.loc[matches['company_id'] == x, 'company_name'].iloc[0]}"
        ),
    )

else:

    selected_company = st.selectbox(
        "Select a company",
        companies["company_id"].tolist(),
        format_func=lambda x: (
            f"{x} — "
            f"{companies.loc[companies['company_id'] == x, 'company_name'].iloc[0]}"
        ),
    )


# ---------------------------------------------------------
# Company information
# ---------------------------------------------------------

company_row = companies[
    companies["company_id"] == selected_company
].iloc[0]


company_name = company_row["company_name"]

sector = company_row.get(
    "broad_sector",
    "N/A",
)

sub_sector = company_row.get(
    "sub_sector",
    "N/A",
)

about = company_row.get(
    "about_company",
    "N/A",
)

nse_profile = company_row.get(
    "nse_profile",
    "",
)


st.header(company_name)


info1, info2, info3, info4 = st.columns(4)


with info1:
    st.write("**Ticker**")
    st.write(selected_company)


with info2:
    st.write("**Sector**")
    st.write(
        sector
        if pd.notna(sector)
        else "N/A"
    )


with info3:
    st.write("**Sub-sector**")
    st.write(
        sub_sector
        if pd.notna(sub_sector)
        else "N/A"
    )


with info4:
    st.write("**NSE Profile**")

    if (
        pd.notna(nse_profile)
        and str(nse_profile).strip()
    ):
        st.link_button(
            "Open NSE Profile",
            str(nse_profile),
        )
    else:
        st.write("N/A")


if (
    pd.notna(about)
    and str(about).strip()
):
    st.info(str(about))


# ---------------------------------------------------------
# Load financial data
# ---------------------------------------------------------

ratios = get_ratios(
    str(selected_company)
)

pl = get_pl(
    str(selected_company)
)

pros_cons = get_pros_cons(
    str(selected_company)
)


if ratios.empty:

    st.warning(
        "Financial ratio data is not available for this company."
    )

    st.stop()


# ---------------------------------------------------------
# Normalize year
# ---------------------------------------------------------

ratios = ratios.copy()

ratios["year_text"] = (
    ratios["year"]
    .astype(str)
)

ratios["year_num"] = pd.to_numeric(
    ratios["year_text"]
    .str.extract(r"(\d{4})")[0],
    errors="coerce",
)

ratios = ratios.sort_values(
    "year_num"
)


# ---------------------------------------------------------
# Latest ratio record
# ---------------------------------------------------------

latest_ratio = (
    ratios
    .dropna(subset=["year_num"])
    .tail(1)
)


if latest_ratio.empty:

    st.warning(
        "Latest financial data is not available."
    )

    st.stop()


latest = latest_ratio.iloc[0]


# ---------------------------------------------------------
# Formatting helper
# ---------------------------------------------------------

def safe_number(
    value,
    suffix="",
):
    if pd.isna(value):
        return "N/A"

    try:
        return (
            f"{float(value):.2f}"
            f"{suffix}"
        )
    except (
        TypeError,
        ValueError,
    ):
        return "N/A"


# ---------------------------------------------------------
# KPI cards
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Key Financial Metrics"
)


k1, k2, k3, k4, k5, k6 = st.columns(6)


with k1:

    st.metric(
        "ROE",
        safe_number(
            latest.get(
                "return_on_equity_pct"
            ),
            "%",
        ),
    )


with k2:

    st.metric(
        "ROCE",
        safe_number(
            company_row.get(
                "roce_percentage"
            ),
            "%",
        ),
    )


with k3:

    st.metric(
        "Net Profit Margin",
        safe_number(
            latest.get(
                "net_profit_margin_pct"
            ),
            "%",
        ),
    )


with k4:

    st.metric(
        "D/E",
        safe_number(
            latest.get(
                "debt_to_equity"
            )
        ),
    )


with k5:

    st.metric(
        "Revenue CAGR 5yr",
        safe_number(
            latest.get(
                "revenue_cagr_5yr"
            ),
            "%",
        ),
    )


with k6:

    st.metric(
        "FCF",
        safe_number(
            latest.get(
                "free_cash_flow_cr"
            ),
            " Cr",
        ),
    )


# ---------------------------------------------------------
# Revenue and Net Profit
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Revenue and Net Profit — 10 Year History"
)


if not pl.empty:

    pl = pl.copy()

    pl["year_num"] = pd.to_numeric(
        pl["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    pl["sales"] = pd.to_numeric(
        pl["sales"],
        errors="coerce",
    )

    pl["net_profit"] = pd.to_numeric(
        pl["net_profit"],
        errors="coerce",
    )

    pl_chart = (
        pl[
            [
                "year_num",
                "sales",
                "net_profit",
            ]
        ]
        .dropna(
            subset=["year_num"]
        )
        .sort_values(
            "year_num"
        )
        .tail(10)
    )


    fig = go.Figure()


    fig.add_trace(
        go.Bar(
            x=pl_chart["year_num"],
            y=pl_chart["sales"],
            name="Revenue",
        )
    )


    fig.add_trace(
        go.Bar(
            x=pl_chart["year_num"],
            y=pl_chart["net_profit"],
            name="Net Profit",
        )
    )


    fig.update_layout(
        barmode="group",
        height=450,
        xaxis_title="Year",
        yaxis_title="₹ Crore",
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20,
        ),
    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )

else:

    st.info(
        "Profit and loss history is not available."
    )


# ---------------------------------------------------------
# ROE and ROCE
# ---------------------------------------------------------

st.subheader(
    "ROE and ROCE — 10 Year History"
)


roe_chart = ratios[
    [
        "year_num",
        "return_on_equity_pct",
    ]
].copy()


roe_chart["roe"] = pd.to_numeric(
    roe_chart[
        "return_on_equity_pct"
    ],
    errors="coerce",
)


roe_chart = (
    roe_chart[
        [
            "year_num",
            "roe",
        ]
    ]
    .dropna(
        subset=["year_num"]
    )
    .sort_values(
        "year_num"
    )
    .tail(10)
)


fig2 = go.Figure()


fig2.add_trace(
    go.Scatter(
        x=roe_chart["year_num"],
        y=roe_chart["roe"],
        mode="lines+markers",
        name="ROE",
    )
)


# ---------------------------------------------------------
# ROCE historical data
# ---------------------------------------------------------
#
# The companies table contains the current ROCE value,
# while financial_ratios does not contain a historical ROCE
# column. Therefore, use the available current ROCE value
# rather than inventing historical values.
# ---------------------------------------------------------

roce_value = pd.to_numeric(
    company_row.get(
        "roce_percentage"
    ),
    errors="coerce",
)


if pd.notna(roce_value):

    fig2.add_trace(
        go.Scatter(
            x=roe_chart["year_num"],
            y=[roce_value]
            * len(roe_chart),
            mode="lines+markers",
            name="ROCE",
        )
    )


fig2.update_layout(
    height=450,
    xaxis_title="Year",
    yaxis_title="Percentage",
    margin=dict(
        l=20,
        r=20,
        t=40,
        b=20,
    ),
)


st.plotly_chart(
    fig2,
    use_container_width=True,
)


# ---------------------------------------------------------
# Pros and Cons
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Pros and Cons"
)


if pros_cons.empty:

    st.info(
        "Pros and cons information is not available."
    )

else:

    row = pros_cons.iloc[0]

    pros = row.get(
        "pros",
        "",
    )

    cons = row.get(
        "cons",
        "",
    )


    left, right = st.columns(2)


    with left:

        st.markdown(
            "### ✅ Pros"
        )

        if (
            pd.notna(pros)
            and str(pros).strip()
        ):

            for item in str(
                pros
            ).split("\n"):

                if item.strip():
                    st.success(
                        item.strip()
                    )

        else:

            st.info(
                "No pros available."
            )


    with right:

        st.markdown(
            "### ❌ Cons"
        )

        if (
            pd.notna(cons)
            and str(cons).strip()
        ):

            for item in str(
                cons
            ).split("\n"):

                if item.strip():
                    st.error(
                        item.strip()
                    )

        else:

            st.info(
                "No cons available."
            )