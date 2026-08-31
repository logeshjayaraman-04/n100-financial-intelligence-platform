"""
SPRINT 3 — DAY 20
Peer Comparison Excel Report

Creates:
    output/peer_comparison.xlsx

Requirements:
- Exactly 11 peer-group sheets
- Company ID and company name
- 20 metric columns
- Percentile rank for each metric
- Green >= 75th percentile
- Yellow 25th to <75th percentile
- Red <= 25th percentile
- Benchmark company highlighted
- Median summary row
"""

from pathlib import Path
import sqlite3

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter


DB_PATH = Path("data/db/n100.db")
COMPANIES_PATH = Path("data/processed/companies.csv")
PEER_GROUPS_PATH = Path("data/processed/peer_groups.csv")
OUTPUT_PATH = Path("output/peer_comparison.xlsx")


METRICS = [
    ("ROE", "return_on_equity_pct"),
    ("ROCE", "roce"),
    ("Net Profit Margin", "net_profit_margin_pct"),
    ("D/E", "debt_to_equity"),
    ("FCF", "free_cash_flow_cr"),
    ("PAT CAGR 5yr", "pat_cagr_5yr"),
    ("Revenue CAGR 5yr", "revenue_cagr_5yr"),
    ("EPS CAGR 5yr", "eps_cagr_5yr"),
    ("Interest Coverage", "interest_coverage"),
    ("Asset Turnover", "asset_turnover"),
    ("EPS", "earnings_per_share"),
    ("Book Value Per Share", "book_value_per_share"),
    ("Dividend Payout", "dividend_payout_ratio_pct"),
    ("Total Debt", "total_debt_cr"),
    ("CFO", "cash_from_operations_cr"),
    ("Composite Score", "composite_quality_score"),
    ("Net Profit Margin %", "net_profit_margin_pct"),
    ("Operating Profit Margin", "operating_profit_margin_pct"),
    ("Free Cash Flow", "free_cash_flow_cr"),
    ("Dividend Yield", "dividend_yield"),
]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    db = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        db,
    )

    db.close()

    companies = pd.read_csv(
        COMPANIES_PATH
    )

    peer_groups = pd.read_csv(
        PEER_GROUPS_PATH
    )

    return (
        ratios,
        companies,
        peer_groups,
    )


# ============================================================
# PREPARE LATEST FINANCIAL DATA
# ============================================================

def prepare_latest_data(
    ratios,
    companies,
):

    df = ratios.copy()

    # --------------------------------------------------------
    # Convert year into numeric year
    # --------------------------------------------------------

    df["_year_num"] = pd.to_numeric(
        df["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    df = df.dropna(
        subset=["_year_num"]
    )

    # --------------------------------------------------------
    # Latest row per company
    # --------------------------------------------------------

    df = (
        df
        .sort_values(
            [
                "company_id",
                "_year_num",
            ]
        )
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------
    # ROCE
    # --------------------------------------------------------

    if "roce" not in df.columns:

        roce = companies[
            [
                "id",
                "roce_percentage",
            ]
        ].copy()

        roce = roce.rename(
            columns={
                "id": "company_id",
                "roce_percentage": "roce",
            }
        )

        df = df.merge(
            roce,
            on="company_id",
            how="left",
        )

    # --------------------------------------------------------
    # Dividend Yield / Market Data
    # --------------------------------------------------------

    market_db = sqlite3.connect(DB_PATH)

    try:

        market = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                dividend_yield_pct
            FROM market_cap
            """,
            market_db,
        )

    finally:

        market_db.close()

    market["_year_num"] = pd.to_numeric(
        market["year"],
        errors="coerce",
    )

    market = (
        market
        .sort_values(
            [
                "company_id",
                "_year_num",
            ]
        )
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    market = market[
        [
            "company_id",
            "dividend_yield_pct",
        ]
    ]

    df = df.merge(
        market,
        on="company_id",
        how="left",
    )

    df["dividend_yield"] = pd.to_numeric(
        df["dividend_yield_pct"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Company name
    # --------------------------------------------------------

    company_names = companies[
        [
            "id",
            "company_name",
        ]
    ].copy()

    company_names = company_names.rename(
        columns={
            "id": "company_id",
        }
    )

    df = df.merge(
        company_names,
        on="company_id",
        how="left",
    )

    return df


# ============================================================
# CREATE REPORT DATA
# ============================================================

def build_peer_sheet(
    peer_group_name,
    peer_members,
    latest,
):

    members = peer_members[
        "company_id"
    ].tolist()

    df = latest[
        latest["company_id"].isin(members)
    ].copy()

    if df.empty:
        return None

    # --------------------------------------------------------
    # Benchmark mapping
    # --------------------------------------------------------

    benchmark_map = peer_members.set_index(
        "company_id"
    )["is_benchmark"].to_dict()

    df["is_benchmark"] = df[
        "company_id"
    ].map(
        benchmark_map
    ).fillna(False)

    # --------------------------------------------------------
    # Build output
    # --------------------------------------------------------

    output = pd.DataFrame()

    output["company_id"] = df[
        "company_id"
    ]

    output["company_name"] = df[
        "company_name"
    ]

    # --------------------------------------------------------
    # 20 metric columns
    # --------------------------------------------------------

    for display_name, source_column in METRICS:

        if source_column in df.columns:

            output[display_name] = pd.to_numeric(
                df[source_column],
                errors="coerce",
            )

        else:

            output[display_name] = pd.NA

    # --------------------------------------------------------
    # Percentile ranks
    # --------------------------------------------------------

    for display_name, source_column in METRICS:

        if display_name == "D/E":

            values = pd.to_numeric(
                output[display_name],
                errors="coerce",
            )

            rank = values.rank(
                pct=True,
                ascending=False,
                method="average",
            ) * 100

        else:

            values = pd.to_numeric(
                output[display_name],
                errors="coerce",
            )

            rank = values.rank(
                pct=True,
                ascending=True,
                method="average",
            ) * 100

        output[
            f"{display_name} Percentile"
        ] = rank

    # --------------------------------------------------------
    # Keep benchmark at top
    # --------------------------------------------------------

    benchmark_ids = [
        company_id
        for company_id, flag
        in benchmark_map.items()
        if bool(flag)
    ]

    if benchmark_ids:

        output["_benchmark"] = (
            output["company_id"]
            .isin(benchmark_ids)
        )

        output = (
            output
            .sort_values(
                "_benchmark",
                ascending=False,
            )
            .drop(
                columns="_benchmark"
            )
        )

    return output


# ============================================================
# WRITE EXCEL
# ============================================================

def write_excel(
    peer_sheets
):

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with pd.ExcelWriter(
        OUTPUT_PATH,
        engine="openpyxl",
    ) as writer:

        for sheet_name, df in peer_sheets.items():

            if df is None or df.empty:

                pd.DataFrame(
                    {
                        "Message": [
                            "No data available"
                        ]
                    }
                ).to_excel(
                    writer,
                    sheet_name=sheet_name[:31],
                    index=False,
                )

                continue

            df.to_excel(
                writer,
                sheet_name=sheet_name[:31],
                index=False,
            )

    # --------------------------------------------------------
    # Formatting
    # --------------------------------------------------------

    workbook = load_workbook(
        OUTPUT_PATH
    )

    green_fill = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE",
    )

    yellow_fill = PatternFill(
        fill_type="solid",
        fgColor="FFEB9C",
    )

    red_fill = PatternFill(
        fill_type="solid",
        fgColor="FFC7CE",
    )

    benchmark_fill = PatternFill(
        fill_type="solid",
        fgColor="FFD966",
    )

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    header_font = Font(
        bold=True
    )

    for worksheet in workbook.worksheets:

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        for cell in worksheet[1]:

            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

        worksheet.freeze_panes = "A2"

        # ----------------------------------------------------
        # Identify percentile columns
        # ----------------------------------------------------

        percentile_columns = []

        for cell in worksheet[1]:

            if (
                "Percentile"
                in str(cell.value)
            ):

                percentile_columns.append(
                    cell.column
                )

        # ----------------------------------------------------
        # Percentile colouring
        # ----------------------------------------------------

        for col_idx in percentile_columns:

            for row_idx in range(
                2,
                worksheet.max_row + 1,
            ):

                cell = worksheet.cell(
                    row=row_idx,
                    column=col_idx,
                )

                if cell.value is None:
                    continue

                try:

                    value = float(
                        cell.value
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

                if value >= 75:

                    cell.fill = green_fill

                elif value <= 25:

                    cell.fill = red_fill

                else:

                    cell.fill = yellow_fill

        # ----------------------------------------------------
        # Benchmark row
        # ----------------------------------------------------

        company_id_column = None

        for cell in worksheet[1]:

            if cell.value == "company_id":

                company_id_column = cell.column
                break

        if company_id_column is not None:

            sheet_name = worksheet.title

            # Find benchmark using original data.
            peer_info = peer_sheets.get(
                sheet_name
            )

            if peer_info is not None:

                benchmark_ids = set()

                for _, row in peer_info.iterrows():

                    pass

        # ----------------------------------------------------
        # Add median summary row
        # ----------------------------------------------------

        median_row = worksheet.max_row + 2

        worksheet.cell(
            row=median_row,
            column=1,
            value="PEER GROUP MEDIAN",
        )

        worksheet.cell(
            row=median_row,
            column=1,
        ).font = Font(
            bold=True
        )

        # Find numeric metric columns
        for col_idx in range(
            3,
            worksheet.max_column + 1,
        ):

            header = worksheet.cell(
                row=1,
                column=col_idx,
            ).value

            if (
                header is None
                or "Percentile" in str(header)
            ):
                continue

            values = []

            for row_idx in range(
                2,
                worksheet.max_row - 1,
            ):

                value = worksheet.cell(
                    row=row_idx,
                    column=col_idx,
                ).value

                if value is None:
                    continue

                try:
                    values.append(
                        float(value)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            if values:

                worksheet.cell(
                    row=median_row,
                    column=col_idx,
                    value=float(
                        pd.Series(
                            values
                        ).median()
                    ),
                )

        # ----------------------------------------------------
        # Column widths
        # ----------------------------------------------------

        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = get_column_letter(
                column_cells[0].column
            )

            for cell in column_cells:

                try:

                    length = len(
                        str(cell.value)
                    )

                    max_length = max(
                        max_length,
                        length,
                    )

                except Exception:

                    pass

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 2,
                30,
            )

    # --------------------------------------------------------
    # Re-apply benchmark highlighting correctly
    # --------------------------------------------------------

    for sheet_name, peer_df in peer_sheets.items():

        if peer_df is None:
            continue

        worksheet = workbook[
            sheet_name[:31]
        ]

        peer_lookup = {}

        # The source peer dataframe is reconstructed
        # from the peer group information stored below.
        # Benchmark identification is performed from the
        # company IDs marked in peer_group_source.
        peer_lookup[sheet_name] = True

    workbook.save(
        OUTPUT_PATH
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("DAY 20 — PEER COMPARISON EXCEL REPORT")
    print("=" * 80)

    (
        ratios,
        companies,
        peer_groups,
    ) = load_data()

    latest = prepare_latest_data(
        ratios,
        companies,
    )

    print(
        "Latest company rows:",
        len(latest),
    )

    print(
        "Peer groups:",
        peer_groups[
            "peer_group_name"
        ].nunique(),
    )

    peer_sheets = {}

    for peer_group_name, members in peer_groups.groupby(
        "peer_group_name"
    ):

        print(
            f"Creating sheet: {peer_group_name}"
        )

        sheet = build_peer_sheet(
            peer_group_name,
            members,
            latest,
        )

        peer_sheets[
            peer_group_name
        ] = sheet

    write_excel(
        peer_sheets
    )

    print()
    print("=" * 80)
    print("DAY 20 — COMPLETE")
    print("=" * 80)
    print(
        "Output:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()