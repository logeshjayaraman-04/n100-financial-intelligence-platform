from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src.screener.engine import (
    build_screener_dataframe,
    apply_filters,
)
from src.screener.presets import PRESETS


st.title("Screener")

st.write(
    "Filter the Nifty 100 universe using financial quality, "
    "growth, valuation, leverage, and cash-flow metrics."
)


# ---------------------------------------------------------
# Load screener data
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def load_screener_data():
    return build_screener_dataframe()


df = load_screener_data()

if df.empty:
    st.error("No screener data is available.")
    st.stop()


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.header("Screener Filters")


# ---------------------------------------------------------
# Preset buttons
# ---------------------------------------------------------

st.sidebar.subheader("Presets")

preset_names = [
    "Quality Compounder",
    "Value Pick",
    "Growth Accelerator",
    "Dividend Champion",
    "Debt-Free Blue Chip",
    "Turnaround Watch",
]


selected_preset = st.session_state.get(
    "selected_preset",
    None,
)


preset_cols = st.sidebar.columns(2)


for i, preset_name in enumerate(preset_names):

    with preset_cols[i % 2]:

        if st.button(
            preset_name,
            key=f"preset_{i}",
            use_container_width=True,
        ):
            st.session_state["selected_preset"] = preset_name
            st.rerun()


selected_preset = st.session_state.get(
    "selected_preset",
    None,
)


# ---------------------------------------------------------
# Default filter values
# ---------------------------------------------------------

def preset_value(
    preset_name,
    key,
    default,
):
    if preset_name is None:
        return default

    preset = PRESETS.get(
        preset_name,
        {},
    )

    return preset.get(
        key,
        default,
    )


# ---------------------------------------------------------
# Slider ranges
# ---------------------------------------------------------

def numeric_range(
    column,
    default_min,
    default_max,
):

    if column not in df.columns:
        return default_min, default_max

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return default_min, default_max

    return (
        float(values.min()),
        float(values.max()),
    )


roe_min_data, roe_max_data = numeric_range(
    "roe",
    0,
    100,
)

de_min_data, de_max_data = numeric_range(
    "debt_to_equity",
    0,
    10,
)

fcf_min_data, fcf_max_data = numeric_range(
    "free_cash_flow_cr",
    -10000,
    10000,
)

rev_min_data, rev_max_data = numeric_range(
    "revenue_cagr_5yr",
    -50,
    100,
)

pat_min_data, pat_max_data = numeric_range(
    "pat_cagr_5yr",
    -50,
    100,
)

opm_min_data, opm_max_data = numeric_range(
    "operating_profit_margin_pct",
    -50,
    100,
)

pe_min_data, pe_max_data = numeric_range(
    "pe_ratio",
    0,
    200,
)

pb_min_data, pb_max_data = numeric_range(
    "pb_ratio",
    0,
    50,
)

div_min_data, div_max_data = numeric_range(
    "dividend_yield_pct",
    0,
    20,
)

icr_min_data, icr_max_data = numeric_range(
    "interest_coverage",
    0,
    100,
)


# ---------------------------------------------------------
# Sliders
# ---------------------------------------------------------

roe_default = preset_value(
    selected_preset,
    "roe_min",
    0,
)

de_default = preset_value(
    selected_preset,
    "de_max",
    de_max_data,
)

fcf_default = preset_value(
    selected_preset,
    "fcf_min",
    fcf_min_data,
)

rev_default = preset_value(
    selected_preset,
    "revenue_cagr_5yr_min",
    rev_min_data,
)

pat_default = preset_value(
    selected_preset,
    "pat_cagr_5yr_min",
    pat_min_data,
)

opm_default = preset_value(
    selected_preset,
    "opm_min",
    opm_min_data,
)

pe_default = preset_value(
    selected_preset,
    "pe_max",
    pe_max_data,
)

pb_default = preset_value(
    selected_preset,
    "pb_max",
    pb_max_data,
)

div_default = preset_value(
    selected_preset,
    "dividend_yield_min",
    div_min_data,
)

icr_default = preset_value(
    selected_preset,
    "icr_min",
    icr_min_data,
)


roe_min = st.sidebar.slider(
    "ROE minimum",
    min_value=float(roe_min_data),
    max_value=float(roe_max_data),
    value=float(
        min(
            max(roe_default, roe_min_data),
            roe_max_data,
        )
    ),
)


de_max = st.sidebar.slider(
    "D/E maximum",
    min_value=float(de_min_data),
    max_value=float(de_max_data),
    value=float(
        min(
            max(de_default, de_min_data),
            de_max_data,
        )
    ),
)


fcf_min = st.sidebar.slider(
    "FCF minimum",
    min_value=float(fcf_min_data),
    max_value=float(fcf_max_data),
    value=float(
        min(
            max(fcf_default, fcf_min_data),
            fcf_max_data,
        )
    ),
)


rev_min = st.sidebar.slider(
    "Revenue CAGR minimum",
    min_value=float(rev_min_data),
    max_value=float(rev_max_data),
    value=float(
        min(
            max(rev_default, rev_min_data),
            rev_max_data,
        )
    ),
)


pat_min = st.sidebar.slider(
    "PAT CAGR minimum",
    min_value=float(pat_min_data),
    max_value=float(pat_max_data),
    value=float(
        min(
            max(pat_default, pat_min_data),
            pat_max_data,
        )
    ),
)


opm_min = st.sidebar.slider(
    "OPM minimum",
    min_value=float(opm_min_data),
    max_value=float(opm_max_data),
    value=float(
        min(
            max(opm_default, opm_min_data),
            opm_max_data,
        )
    ),
)


pe_max = st.sidebar.slider(
    "P/E maximum",
    min_value=float(pe_min_data),
    max_value=float(pe_max_data),
    value=float(
        min(
            max(pe_default, pe_min_data),
            pe_max_data,
        )
    ),
)


pb_max = st.sidebar.slider(
    "P/B maximum",
    min_value=float(pb_min_data),
    max_value=float(pb_max_data),
    value=float(
        min(
            max(pb_default, pb_min_data),
            pb_max_data,
        )
    ),
)


div_min = st.sidebar.slider(
    "Dividend Yield minimum",
    min_value=float(div_min_data),
    max_value=float(div_max_data),
    value=float(
        min(
            max(div_default, div_min_data),
            div_max_data,
        )
    ),
)


icr_min = st.sidebar.slider(
    "ICR minimum",
    min_value=float(icr_min_data),
    max_value=float(icr_max_data),
    value=float(
        min(
            max(icr_default, icr_min_data),
            icr_max_data,
        )
    ),
)


# ---------------------------------------------------------
# Apply filters
# ---------------------------------------------------------

filters = {
    "roe_min": roe_min,
    "de_max": de_max,
    "fcf_min": fcf_min,
    "revenue_cagr_5yr_min": rev_min,
    "pat_cagr_5yr_min": pat_min,
    "opm_min": opm_min,
    "pe_max": pe_max,
    "pb_max": pb_max,
    "dividend_yield_min": div_min,
    "icr_min": icr_min,
}


try:

    results = apply_filters(
        df,
        filters,
        skip_financials_for_de=True,
    )

except TypeError:

    results = apply_filters(
        df,
        filters,
    )


# ---------------------------------------------------------
# Sort by composite score
# ---------------------------------------------------------

if "composite_quality_score" in results.columns:

    results = results.sort_values(
        "composite_quality_score",
        ascending=False,
    )


# ---------------------------------------------------------
# Result count
# ---------------------------------------------------------

st.subheader(
    f"{len(results)} companies match your filters"
)


# ---------------------------------------------------------
# Display columns
# ---------------------------------------------------------

preferred_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "composite_quality_score",
    "roe",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
]


visible_columns = [
    column
    for column in preferred_columns
    if column in results.columns
]


if not visible_columns:
    visible_columns = list(
        results.columns
    )


display_df = results[
    visible_columns
].copy()


# ---------------------------------------------------------
# Numeric formatting
# ---------------------------------------------------------

for column in display_df.columns:

    if column not in [
        "company_id",
        "company_name",
        "broad_sector",
    ]:

        display_df[column] = pd.to_numeric(
            display_df[column],
            errors="coerce",
        ).round(2)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# CSV download
# ---------------------------------------------------------

csv_buffer = io.StringIO()

display_df.to_csv(
    csv_buffer,
    index=False,
)

st.download_button(
    label="Download CSV",
    data=csv_buffer.getvalue(),
    file_name="screener_results.csv",
    mime="text/csv",
)