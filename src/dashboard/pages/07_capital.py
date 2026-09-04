from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
)


st.title("Capital Allocation")

st.write(
    "Explore companies by their capital allocation and "
    "financial characteristics."
)


# ---------------------------------------------------------
# Load companies
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


# ---------------------------------------------------------
# Load latest financial ratios
# ---------------------------------------------------------

rows = []


for _, company in companies.iterrows():

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

    rows.append(
        {
            "company_id": company_id,
            "company_name": company[
                "company_name"
            ],
            "broad_sector": company[
                "broad_sector"
            ],
            "roe": latest.get(
                "return_on_equity_pct"
            ),
            "debt_to_equity": latest.get(
                "debt_to_equity"
            ),
            "free_cash_flow_cr": latest.get(
                "free_cash_flow_cr"
            ),
            "dividend_payout_ratio_pct": latest.get(
                "dividend_payout_ratio_pct"
            ),
            "capex_cr": latest.get(
                "capex_cr"
            ),
            "cash_from_operations_cr": latest.get(
                "cash_from_operations_cr"
            ),
        }
    )


df = pd.DataFrame(rows)


if df.empty:
    st.warning(
        "No financial data is available "
        "for capital allocation analysis."
    )
    st.stop()


# ---------------------------------------------------------
# Convert numeric fields
# ---------------------------------------------------------

numeric_columns = [
    "roe",
    "debt_to_equity",
    "free_cash_flow_cr",
    "dividend_payout_ratio_pct",
    "capex_cr",
    "cash_from_operations_cr",
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )


# ---------------------------------------------------------
# Capital allocation classification
# ---------------------------------------------------------

def classify_company(row):

    roe = row["roe"]
    debt = row["debt_to_equity"]
    fcf = row["free_cash_flow_cr"]
    dividend = row[
        "dividend_payout_ratio_pct"
    ]
    capex = row["capex_cr"]
    cfo = row[
        "cash_from_operations_cr"
    ]

    # -----------------------------------------------------
    # Missing data
    # -----------------------------------------------------

    if (
        pd.isna(roe)
        and pd.isna(debt)
        and pd.isna(fcf)
    ):
        return "Insufficient Data"


    # -----------------------------------------------------
    # 1. High Return Compounder
    # -----------------------------------------------------

    if (
        pd.notna(roe)
        and roe >= 20
        and (
            pd.isna(debt)
            or debt <= 1
        )
        and (
            pd.isna(fcf)
            or fcf >= 0
        )
    ):
        return "High Return Compounder"


    # -----------------------------------------------------
    # 2. Dividend / Shareholder Return
    # -----------------------------------------------------

    if (
        pd.notna(dividend)
        and dividend >= 40
        and (
            pd.isna(fcf)
            or fcf >= 0
        )
    ):
        return "Dividend / Shareholder Return"


    # -----------------------------------------------------
    # 3. Debt Reduction / Conservative
    # -----------------------------------------------------

    if (
        pd.notna(debt)
        and debt <= 0.25
        and (
            pd.isna(roe)
            or roe >= 12
        )
    ):
        return "Debt Reduction / Conservative"


    # -----------------------------------------------------
    # 4. Growth Reinvestment
    # -----------------------------------------------------

    if (
        pd.notna(capex)
        and pd.notna(cfo)
        and capex > 0
        and cfo > 0
        and capex >= cfo * 0.35
    ):
        return "Growth Reinvestment"


    # -----------------------------------------------------
    # 5. Cash Generation
    # -----------------------------------------------------

    if (
        pd.notna(fcf)
        and fcf > 0
        and (
            pd.isna(dividend)
            or dividend < 40
        )
    ):
        return "Cash Generation"


    # -----------------------------------------------------
    # 6. Leveraged Expansion
    # -----------------------------------------------------

    if (
        pd.notna(debt)
        and debt > 1
        and (
            pd.isna(roe)
            or roe >= 12
        )
    ):
        return "Leveraged Expansion"


    # -----------------------------------------------------
    # 7. Turnaround / Restructuring
    # -----------------------------------------------------

    if (
        (
            pd.notna(roe)
            and roe < 10
        )
        or (
            pd.notna(fcf)
            and fcf < 0
        )
    ):
        return "Turnaround / Restructuring"


    # -----------------------------------------------------
    # 8. Balanced Allocation
    # -----------------------------------------------------

    return "Balanced Allocation"


df["capital_allocation_pattern"] = df.apply(
    classify_company,
    axis=1,
)


# ---------------------------------------------------------
# Pattern order
# ---------------------------------------------------------

pattern_order = [
    "High Return Compounder",
    "Dividend / Shareholder Return",
    "Debt Reduction / Conservative",
    "Growth Reinvestment",
    "Cash Generation",
    "Leveraged Expansion",
    "Turnaround / Restructuring",
    "Balanced Allocation",
    "Insufficient Data",
]


# ---------------------------------------------------------
# Pattern summary
# ---------------------------------------------------------

summary = (
    df.groupby(
        "capital_allocation_pattern",
        as_index=False,
    )
    .agg(
        Companies=(
            "company_id",
            "count",
        ),
        Total_FCF=(
            "free_cash_flow_cr",
            "sum",
        ),
    )
)


summary["Pattern"] = pd.Categorical(
    summary[
        "capital_allocation_pattern"
    ],
    categories=pattern_order,
    ordered=True,
)


summary = summary.sort_values(
    "Pattern"
)


# ---------------------------------------------------------
# Treemap
# ---------------------------------------------------------

st.subheader("Capital Allocation Patterns")


if summary.empty:

    st.info(
        "No capital allocation patterns are available."
    )

else:

    fig = px.treemap(
        summary,
        path=[
            "capital_allocation_pattern"
        ],
        values="Companies",
        hover_data={
            "Companies": True,
            "Total_FCF": ":.2f",
        },
        title=(
            "Companies by Capital "
            "Allocation Pattern"
        ),
    )

    fig.update_layout(
        height=600,
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------
# Pattern selector
# ---------------------------------------------------------

st.subheader("Companies by Pattern")


available_patterns = [
    pattern
    for pattern in pattern_order
    if pattern in df[
        "capital_allocation_pattern"
    ].unique()
]


selected_pattern = st.selectbox(
    "Select a capital allocation pattern",
    available_patterns,
)


pattern_companies = df[
    df["capital_allocation_pattern"]
    == selected_pattern
].copy()


# ---------------------------------------------------------
# Pattern metrics
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "Companies",
        len(pattern_companies),
    )


with col2:

    median_roe = pd.to_numeric(
        pattern_companies["roe"],
        errors="coerce",
    ).median()

    if pd.isna(median_roe):
        st.metric(
            "Median ROE",
            "N/A",
        )
    else:
        st.metric(
            "Median ROE",
            f"{median_roe:.2f}%",
        )


with col3:

    total_fcf = pd.to_numeric(
        pattern_companies[
            "free_cash_flow_cr"
        ],
        errors="coerce",
    ).sum()

    if pd.isna(total_fcf):
        st.metric(
            "Total FCF",
            "N/A",
        )
    else:
        st.metric(
            "Total FCF",
            f"{total_fcf:,.0f} Cr",
        )


# ---------------------------------------------------------
# Company list
# ---------------------------------------------------------

display_df = pattern_companies[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "roe",
        "debt_to_equity",
        "free_cash_flow_cr",
        "dividend_payout_ratio_pct",
        "capex_cr",
    ]
].copy()


display_df = display_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "broad_sector": "Sector",
        "roe": "ROE",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF",
        "dividend_payout_ratio_pct": (
            "Dividend Payout %"
        ),
        "capex_cr": "Capex",
    }
)


for column in [
    "ROE",
    "D/E",
    "FCF",
    "Dividend Payout %",
    "Capex",
]:

    display_df[column] = pd.to_numeric(
        display_df[column],
        errors="coerce",
    ).round(2)


display_df = display_df.sort_values(
    "Company"
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


st.caption(
    "Capital allocation patterns are analytical "
    "classifications based on the latest available "
    "financial data. They are not investment advice."
)