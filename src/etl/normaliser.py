"""
N100 Financial Intelligence Platform
Excel data normalisation utilities.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


TITLE_ROW_FILES = {
    "analysis.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "companies.xlsx",
    "documents.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
}


def normalize_columns(columns: list[str]) -> list[str]:
    """Convert column names into clean snake_case names."""
    cleaned = []

    for column in columns:
        column = str(column).strip()
        column = re.sub(r"[^A-Za-z0-9]+", "_", column)
        column = column.strip("_").lower()
        cleaned.append(column)

    return cleaned


def normalize_ticker(value: object) -> str | None:
    """Normalize a company ticker/company identifier."""
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if not value:
        return None

    return value


def normalize_year(value: object) -> int | str | None:
    """
    Normalize financial-period values.

    Examples:
        Dec 2012 -> 2012
        Mar 2014 -> 2014
        Mar-15   -> 2015
        FY2021   -> 2021
        FY 2021  -> 2021
        2024     -> 2024
        TTM      -> TTM
    """
    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    if text.upper() == "TTM":
        return "TTM"

    # Four-digit year, including FY2021 and Year 2022.
    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group(0))

    # Two-digit year, for example Mar-15.
    match = re.search(r"[-/ ](\d{2})\b", text)

    if match:
        year = int(match.group(1))

        if year <= 49:
            return 2000 + year

        return 1900 + year

    # Numeric values such as 2024.0.
    try:
        number = float(text)

        if 1900 <= number <= 2100:
            return int(number)

    except ValueError:
        pass

    return None
    # Preserve Trailing Twelve Months as a separate period.
    if text.upper() == "TTM":
        return "TTM"

    # Four-digit year, including FY2021 and Year 2022.
    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group(0))

    # Two-digit year, for example Mar-15.
    match = re.search(r"[-/ ](\d{2})\b", text)

    if match:
        year = int(match.group(1))

        if year <= 49:
            return 2000 + year

        return 1900 + year

    # Numeric values such as 2024.0.
    try:
        number = float(text)

        if 1900 <= number <= 2100:
            return int(number)

    except ValueError:
        pass

    return None

def read_excel_normalized(
    file_path: str | Path,
    *,
    header_row: int | None = None,
) -> pd.DataFrame:
    """Read an Excel file and return a cleaned DataFrame."""
    file_path = Path(file_path)

    if header_row is None:
        if file_path.name.lower() in TITLE_ROW_FILES:
            header_row = 1
        else:
            header_row = 0

    df = pd.read_excel(file_path, header=header_row)

    df.columns = normalize_columns(list(df.columns))

    df = df.dropna(how="all").reset_index(drop=True)

    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)

    if file_path.name.lower() == "companies.xlsx" and "id" in df.columns:
        df["id"] = df["id"].apply(normalize_ticker)

    return df


def main() -> None:
    """Run a normalisation smoke test across all raw Excel files."""
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"

    print("N100 normalisation smoke test")

    for file_path in sorted(raw_dir.glob("*.xlsx")):
        df = read_excel_normalized(file_path)

        print(
            f"{file_path.name}: "
            f"{len(df)} rows, "
            f"{len(df.columns)} columns"
        )


if __name__ == "__main__":
    main()
    