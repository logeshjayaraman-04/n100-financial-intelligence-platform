from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


# =========================================================
# PROJECT PATHS
# =========================================================

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parents[1]
SRC_DIR = ROOT_DIR / "src"

for path in (ROOT_DIR, SRC_DIR):
    path_string = str(path)

    if path_string not in sys.path:
        sys.path.insert(0, path_string)


# =========================================================
# STREAMLIT CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DASHBOARD PAGES
# =========================================================

PAGES = {
    "Home": "01_home.py",
    "Company Profile": "02_profile.py",
    "Screener": "03_screener.py",
    "Peer Comparison": "04_peers.py",
    "Trend Analysis": "05_trends.py",
    "Sector Analysis": "06_sectors.py",
    "Capital Allocation": "07_capital.py",
    "Annual Reports": "08_reports.py",
}


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

selected_page = st.sidebar.radio(
    "Navigation",
    list(PAGES.keys()),
)


# =========================================================
# PAGE LOADER
# =========================================================

def run_page(page_name: str) -> None:
    page_file = APP_DIR / "pages" / PAGES[page_name]

    if not page_file.exists():
        st.error(
            f"Page file not found:\n\n{page_file}"
        )
        return

    code = page_file.read_text(
        encoding="utf-8"
    )

    exec(
        compile(
            code,
            str(page_file),
            "exec",
        ),
        globals(),
    )


# =========================================================
# RUN SELECTED PAGE
# =========================================================

run_page(selected_page)