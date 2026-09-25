"""
N100 Financial Intelligence Platform Streamlit dashboard.

Loads the dashboard pages from the pages directory and provides the
application-level Streamlit configuration.
"""

from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = Path(__file__).resolve().parent / "pages"

PAGES = [
    ("Home", "01_home.py"),
    ("Company Profile", "02_profile.py"),
    ("Screener", "03_screener.py"),
    ("Peer Comparison", "04_peers.py"),
    ("Trend Analysis", "05_trends.py"),
    ("Sector Analysis", "06_sectors.py"),
    ("Capital Allocation", "07_capital.py"),
    ("Annual Reports", "08_reports.py"),
]


def load_page(page_file: str) -> None:
    """Execute a dashboard page from the pages directory."""
    page_path = PAGES_DIR / page_file

    if not page_path.exists():
        st.error(f"Dashboard page not found: {page_path}")
        return

    page_code = page_path.read_text(encoding="utf-8")
    exec(compile(page_code, str(page_path), "exec"), globals())  # noqa: S102


def configure_page() -> None:
    """Configure the Streamlit application page settings."""
    st.set_page_config(
        page_title="N100 Financial Intelligence Platform",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_sidebar() -> str:
    """Render dashboard navigation and return the selected page."""
    st.sidebar.title("N100 Financial Intelligence")
    st.sidebar.caption("Financial Intelligence Platform")

    page_names = [name for name, _ in PAGES]

    selected_page = st.sidebar.radio(
        "Navigation",
        page_names,
        index=0,
    )

    st.sidebar.divider()
    st.sidebar.caption(
        "N100 covers the current 100-company universe "
        "represented in the project database."
    )

    return selected_page


def main() -> None:
    """Run the Streamlit dashboard application."""
    configure_page()

    selected_page = render_sidebar()

    page_lookup = dict(PAGES)
    load_page(page_lookup[selected_page])


if __name__ == "__main__":
    main()
