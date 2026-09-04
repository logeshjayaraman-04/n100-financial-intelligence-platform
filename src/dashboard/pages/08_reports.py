from __future__ import annotations

import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_reports,
)


st.title("Annual Reports")

st.write(
    "Access available annual reports and company filings."
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
# Company information
# ---------------------------------------------------------

st.subheader(
    selected_row["company_name"]
)

st.caption(
    f"Ticker: {ticker}"
)


# ---------------------------------------------------------
# Load reports
# ---------------------------------------------------------

reports = get_reports(ticker)


if reports.empty:

    st.warning(
        "No annual reports are available "
        "for this company."
    )

    st.stop()


# ---------------------------------------------------------
# Clean report data
# ---------------------------------------------------------

reports = reports.copy()


reports["year_text"] = (
    reports["year"]
    .astype(str)
)


reports["year_num"] = (
    reports["year_text"]
    .str.extract(
        r"(\d{4})",
        expand=False,
    )
)


reports["year_num"] = (
    reports["year_num"]
    .astype("Int64")
)


reports = reports.sort_values(
    "year_num",
    ascending=False,
)


# ---------------------------------------------------------
# Available years
# ---------------------------------------------------------

available_years = [
    int(year)
    for year in reports["year_num"]
    .dropna()
    .unique()
]


if not available_years:

    st.warning(
        "Annual report years could not be determined."
    )

    st.stop()


selected_year = st.selectbox(
    "Select annual report year",
    available_years,
)


# ---------------------------------------------------------
# Selected report
# ---------------------------------------------------------

selected_reports = reports[
    reports["year_num"]
    == selected_year
]


if selected_reports.empty:

    st.warning(
        "No report is available for "
        f"{selected_year}."
    )

else:

    for _, report in selected_reports.iterrows():

        report_url = report.get(
            "annual_report"
        )


        # Convert database value to string
        if report_url is None:

            report_url = ""

        else:

            report_url = str(
                report_url
            ).strip()


        st.subheader(
            f"Annual Report {selected_year}"
        )


        # -------------------------------------------------
        # Missing URL
        # -------------------------------------------------

        if not report_url:

            st.error(
                "Unavailable — no report link "
                "is stored for this year."
            )

            continue


        # -------------------------------------------------
        # Basic URL validation
        # -------------------------------------------------

        valid_url = (
            report_url.startswith(
                "http://"
            )
            or report_url.startswith(
                "https://"
            )
        )


        if not valid_url:

            st.error(
                "Unavailable — the stored report "
                "link is not a valid web URL."
            )

            continue


        # -------------------------------------------------
        # Report link
        # -------------------------------------------------

        st.success(
            f"Annual Report {selected_year} available"
        )


        st.markdown(
            f"[Open BSE Annual Report]({report_url})"
        )


# ---------------------------------------------------------
# Report history
# ---------------------------------------------------------

st.subheader("Report History")


history_rows = []


for _, report in reports.iterrows():

    year = report.get(
        "year_num"
    )

    report_url = report.get(
        "annual_report"
    )


    if report_url is None:
        report_url = ""

    report_url = str(
        report_url
    ).strip()


    if not report_url:

        status = "Unavailable"

    elif (
        report_url.startswith("http://")
        or report_url.startswith("https://")
    ):

        status = "Available"

    else:

        status = "Unavailable"


    history_rows.append(
        {
            "Year": (
                int(year)
                if year == year
                else "N/A"
            ),
            "Status": status,
            "Report": report_url,
        }
    )


for row in history_rows:

    year = row["Year"]
    status = row["Status"]
    report_url = row["Report"]


    if status == "Available":

        st.markdown(
            f"**{year}** — "
            f"🟢 Available — "
            f"[Open Report]({report_url})"
        )

    else:

        st.markdown(
            f"**{year}** — "
            "🔴 Unavailable"
        )


st.caption(
    "Report availability is based on the document "
    "links stored in the database."
)