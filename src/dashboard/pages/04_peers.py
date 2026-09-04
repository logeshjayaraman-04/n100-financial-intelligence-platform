from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.db import get_companies, get_peer_groups, get_peers


st.title("Peer Comparison")
st.caption("Compare a company against its selected peer group using 8 peer metrics.")


# =========================================================
# LOAD DATA
# =========================================================

companies = get_companies()
peer_groups = get_peer_groups()

if companies.empty:
    st.warning("Company data is unavailable.")
    st.stop()

if peer_groups.empty:
    st.warning("Peer-group data is unavailable.")
    st.stop()


# =========================================================
# PEER GROUP SELECTOR
# =========================================================

groups = sorted(
    peer_groups["peer_group_name"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_group = st.selectbox(
    "Peer Group",
    groups,
)


# =========================================================
# LOAD SELECTED PEER GROUP
# =========================================================

peer_data = get_peers(selected_group)

if peer_data.empty:
    st.warning("No peer data is available for this group.")
    st.stop()

peer_data["company_id"] = peer_data["company_id"].astype(str)


# =========================================================
# COMPANY LIST FOR SELECTED PEER GROUP
# =========================================================

group_company_ids = (
    peer_data["company_id"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

available_companies = companies[
    companies["company_id"]
    .astype(str)
    .isin(group_company_ids)
].copy()


if available_companies.empty:
    st.warning(
        "No companies are available for the selected peer group."
    )
    st.stop()


available_companies = available_companies.sort_values(
    "company_name"
)


company_options = (
    available_companies["company_id"]
    .astype(str)
    .tolist()
)

company_labels = {
    str(row["company_id"]): str(row["company_name"])
    for _, row in available_companies.iterrows()
}


# =========================================================
# COMPANY SELECTOR
# =========================================================

selected_company = st.selectbox(
    "Select Company",
    company_options,
    format_func=lambda x: company_labels.get(x, x),
)


company_name = company_labels.get(
    str(selected_company),
    str(selected_company),
)

st.subheader(company_name)


# =========================================================
# COMPANY PEER DATA
# =========================================================

company_peer = peer_data[
    peer_data["company_id"] == str(selected_company)
].copy()


if company_peer.empty:
    st.info(
        "This company does not have percentile data in the selected peer group."
    )
    st.stop()


# =========================================================
# SELECT UP TO 8 METRICS
# =========================================================

metrics = (
    company_peer["metric"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .tolist()
)

metrics = metrics[:8]


if not metrics:
    st.warning("No comparison metrics are available.")
    st.stop()


# =========================================================
# RADAR CHART
# =========================================================

st.subheader("Peer Benchmark Radar")


radar_values = []

for metric in metrics:

    metric_row = company_peer[
        company_peer["metric"].astype(str) == metric
    ]

    if metric_row.empty:
        radar_values.append(0)
        continue

    value = metric_row.iloc[0]["percentile_rank"]

    try:
        radar_values.append(float(value))
    except (TypeError, ValueError):
        radar_values.append(0)


radar_metrics = metrics + [metrics[0]]
radar_company = radar_values + [radar_values[0]]
peer_average = [50.0] * len(radar_metrics)


fig = go.Figure()


fig.add_trace(
    go.Scatterpolar(
        r=peer_average,
        theta=radar_metrics,
        fill="toself",
        name="Peer Average",
    )
)


fig.add_trace(
    go.Scatterpolar(
        r=radar_company,
        theta=radar_metrics,
        fill="toself",
        name=company_name,
    )
)


fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
        )
    ),
    height=520,
    margin=dict(
        l=30,
        r=30,
        t=40,
        b=30,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# KPI COMPARISON
# =========================================================

st.subheader("Peer KPI Comparison")


comparison_rows = []


for metric in metrics:

    metric_row = company_peer[
        company_peer["metric"].astype(str) == metric
    ]

    company_value = None
    company_percentile = None

    if not metric_row.empty:

        company_value = metric_row.iloc[0]["value"]

        company_percentile = metric_row.iloc[0][
            "percentile_rank"
        ]

    comparison_rows.append(
        {
            "Metric": metric,
            "Company Value": company_value,
            "Percentile": company_percentile,
            "Peer Average": 50.0,
        }
    )


comparison_df = pd.DataFrame(comparison_rows)


st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# BENCHMARK SUMMARY
# =========================================================

st.subheader("Benchmark Summary")


if not comparison_df.empty:

    valid_percentiles = pd.to_numeric(
        comparison_df["Percentile"],
        errors="coerce",
    ).dropna()


    if not valid_percentiles.empty:

        average_percentile = valid_percentiles.mean()

        col1, col2, col3 = st.columns(3)


        with col1:
            st.metric(
                "Average Percentile",
                f"{average_percentile:.1f}",
            )


        with col2:
            st.metric(
                "Metrics Compared",
                len(valid_percentiles),
            )


        with col3:

            if average_percentile >= 75:
                benchmark = "Strong"

            elif average_percentile >= 50:
                benchmark = "Above Average"

            elif average_percentile >= 25:
                benchmark = "Below Average"

            else:
                benchmark = "Weak"


            st.metric(
                "Benchmark",
                benchmark,
            )