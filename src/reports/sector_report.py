from pathlib import Path
import sqlite3
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "n100.db"
OUTPUT_DIR = ROOT / "reports" / "sector"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


def safe_float(value):
    try:
        if value is None:
            return None
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except (TypeError, ValueError):
        return None


def fmt(value, decimals=2):
    value = safe_float(value)
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_pct(value):
    value = safe_float(value)
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def draw_header(c, title, subtitle):
    c.setFillColor(colors.HexColor("#17365D"))
    c.rect(0, PAGE_H - 19 * mm, PAGE_W, 19 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, PAGE_H - 11.5 * mm, title[:70])

    c.setFont("Helvetica", 7.5)
    c.drawRightString(
        PAGE_W - MARGIN,
        PAGE_H - 11.5 * mm,
        subtitle[:70],
    )


def draw_footer(c, sector, page_no):
    c.setStrokeColor(colors.HexColor("#C8D2DC"))
    c.line(MARGIN, 10 * mm, PAGE_W - MARGIN, 10 * mm)

    c.setFillColor(colors.HexColor("#666666"))
    c.setFont("Helvetica", 7)

    c.drawString(
        MARGIN,
        6.5 * mm,
        f"N100 Financial Intelligence | {sector[:50]}",
    )

    c.drawRightString(
        PAGE_W - MARGIN,
        6.5 * mm,
        f"Page {page_no} of 1",
    )


def section_title(c, x, y, title, width=CONTENT_W):
    c.setFillColor(colors.HexColor("#EAF0F5"))
    c.roundRect(
        x,
        y - 5 * mm,
        width,
        8 * mm,
        2 * mm,
        fill=1,
        stroke=0,
    )

    c.setFillColor(colors.HexColor("#17365D"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 3 * mm, y - 2 * mm, title)

    return y - 10 * mm


def draw_table(c, x, y, widths, rows, row_h=7 * mm, font_size=6.5):
    if not rows:
        return y

    total_width = sum(widths)

    for row_index, row in enumerate(rows):
        current_x = x

        if row_index == 0:
            fill = colors.HexColor("#17365D")
            text_color = colors.white
            font = "Helvetica-Bold"
        else:
            fill = (
                colors.HexColor("#F7F9FB")
                if row_index % 2 == 0
                else colors.white
            )
            text_color = colors.HexColor("#222222")
            font = "Helvetica"

        c.setFillColor(fill)
        c.setStrokeColor(colors.HexColor("#D5DDE4"))

        c.rect(
            x,
            y - row_h,
            total_width,
            row_h,
            fill=1,
            stroke=1,
        )

        for i, cell in enumerate(row):
            text = "" if cell is None else str(cell)
            text = text.replace("\n", " ")[:32]

            c.setFillColor(text_color)
            c.setFont(font, font_size)

            c.drawString(
                current_x + 2 * mm,
                y - row_h + 2.3 * mm,
                text,
            )

            current_x += widths[i]

        y -= row_h

    return y


def load_sector_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    companies = conn.execute(
        """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector
        FROM companies c
        LEFT JOIN sectors s
            ON s.company_id = c.id
        ORDER BY s.broad_sector, c.company_name
        """
    ).fetchall()

    ratios = conn.execute(
        """
        SELECT *
        FROM financial_ratios
        ORDER BY company_id, year
        """
    ).fetchall()

    pl = conn.execute(
        """
        SELECT *
        FROM profitandloss
        ORDER BY company_id, year
        """
    ).fetchall()

    conn.close()

    return companies, ratios, pl


def latest_by_company(rows):
    result = {}

    for row in rows:
        company_id = row["company_id"]
        result[company_id] = row

    return result


def generate_sector_report(sector_name, company_rows, ratio_rows, pl_rows):
    path = OUTPUT_DIR / (
        sector_name.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        + ".pdf"
    )

    ratio_latest = latest_by_company(ratio_rows)
    pl_latest = latest_by_company(pl_rows)

    c = canvas.Canvas(
        str(path),
        pagesize=A4,
        pageCompression=1,
    )

    c.setTitle(f"{sector_name} - Sector Report")
    c.setAuthor("N100 Financial Intelligence Platform")

    draw_header(
        c,
        f"{sector_name} — Sector Intelligence",
        f"{len(company_rows)} companies",
    )

    y = PAGE_H - 29 * mm

    y = section_title(
        c,
        MARGIN,
        y,
        "SECTOR UNIVERSE",
    )

    rows = [
        [
            "Company",
            "Sub-sector",
            "Revenue CAGR",
            "PAT CAGR",
            "ROE",
            "D/E",
        ]
    ]

    for company in company_rows:
        company_id = company["company_id"]

        ratio = ratio_latest.get(company_id)

        rows.append(
            [
                str(company["company_name"])[:28],
                str(company["sub_sector"] or "N/A")[:20],
                fmt_pct(
                    ratio["revenue_cagr_5yr"]
                    if ratio
                    else None
                ),
                fmt_pct(
                    ratio["pat_cagr_5yr"]
                    if ratio
                    else None
                ),
                fmt_pct(
                    ratio["return_on_equity_pct"]
                    if ratio
                    else None
                ),
                fmt(
                    ratio["debt_to_equity"]
                    if ratio
                    else None
                ),
            ]
        )

    # Keep the sector PDF to one page by showing a compact table.
    # A maximum of 30 companies is displayed; larger sectors are
    # continued in a second table block on the same page only when space allows.
    max_rows = 28

    visible_rows = rows[: max_rows + 1]

    y = draw_table(
        c,
        MARGIN,
        y,
        [
            48 * mm,
            42 * mm,
            27 * mm,
            27 * mm,
            25 * mm,
            20 * mm,
        ],
        visible_rows,
        row_h=6 * mm,
        font_size=5.8,
    )

    if len(rows) - 1 > max_rows:
        c.setFillColor(colors.HexColor("#777777"))
        c.setFont("Helvetica", 6.5)
        c.drawString(
            MARGIN,
            y - 3 * mm,
            f"Showing first {max_rows} companies of {len(company_rows)} in this sector.",
        )

    y -= 8 * mm

    y = section_title(
        c,
        MARGIN,
        y,
        "SECTOR SUMMARY",
    )

    revenue_values = []
    pat_values = []
    roe_values = []

    for company in company_rows:
        company_id = company["company_id"]
        ratio = ratio_latest.get(company_id)

        if ratio:
            revenue = safe_float(ratio["revenue_cagr_5yr"])
            pat = safe_float(ratio["pat_cagr_5yr"])
            roe = safe_float(ratio["return_on_equity_pct"])

            if revenue is not None:
                revenue_values.append(revenue)

            if pat is not None:
                pat_values.append(pat)

            if roe is not None:
                roe_values.append(roe)

    def avg(values):
        if not values:
            return None
        return sum(values) / len(values)

    summary_rows = [
        ["Sector KPI", "Average", "Companies with data"],
        [
            "Revenue CAGR (5Y)",
            fmt_pct(avg(revenue_values)),
            str(len(revenue_values)),
        ],
        [
            "PAT CAGR (5Y)",
            fmt_pct(avg(pat_values)),
            str(len(pat_values)),
        ],
        [
            "ROE",
            fmt_pct(avg(roe_values)),
            str(len(roe_values)),
        ],
    ]

    y = draw_table(
        c,
        MARGIN,
        y,
        [62 * mm, 45 * mm, 45 * mm],
        summary_rows,
        row_h=7 * mm,
    )

    y -= 7 * mm

    y = section_title(
        c,
        MARGIN,
        y,
        "TOP COMPANIES BY REVENUE CAGR",
    )

    ranked = []

    for company in company_rows:
        ratio = ratio_latest.get(company["company_id"])

        if ratio:
            value = safe_float(ratio["revenue_cagr_5yr"])

            if value is not None:
                ranked.append(
                    (
                        value,
                        company["company_name"],
                        ratio,
                    )
                )

    ranked.sort(reverse=True, key=lambda item: item[0])

    ranking_rows = [
        [
            "Rank",
            "Company",
            "Revenue CAGR",
            "PAT CAGR",
            "ROE",
        ]
    ]

    for rank, (value, name, ratio) in enumerate(ranked[:5], start=1):
        ranking_rows.append(
            [
                rank,
                str(name)[:30],
                fmt_pct(value),
                fmt_pct(ratio["pat_cagr_5yr"]),
                fmt_pct(ratio["return_on_equity_pct"]),
            ]
        )

    y = draw_table(
        c,
        MARGIN,
        y,
        [18 * mm, 70 * mm, 30 * mm, 30 * mm, 25 * mm],
        ranking_rows,
        row_h=7 * mm,
    )

    c.setFillColor(colors.HexColor("#777777"))
    c.setFont("Helvetica", 6.5)

    c.drawString(
        MARGIN,
        17 * mm,
        "Source: N100 project database. Metrics use the latest available financial-ratio observation.",
    )

    draw_footer(c, sector_name, 1)

    c.showPage()
    c.save()

    return path


def main():
    print("=== DAY 34 SECTOR REPORT GENERATOR ===")

    companies, ratios, pl = load_sector_data()

    sectors = {}

    for company in companies:
        sector = company["broad_sector"] or "Unclassified"
        sectors.setdefault(sector, []).append(company)

    ratio_groups = {}
    for row in ratios:
        ratio_groups.setdefault(row["company_id"], []).append(row)

    pl_groups = {}
    for row in pl:
        pl_groups.setdefault(row["company_id"], []).append(row)

    print(f"Companies found: {len(companies)}")
    print(f"Sectors found: {len(sectors)}")
    print()

    generated = 0

    for sector_name in sorted(sectors):
        sector_companies = sectors[sector_name]

        sector_ratios = []
        sector_pl = []

        for company in sector_companies:
            company_id = company["company_id"]

            sector_ratios.extend(
                ratio_groups.get(company_id, [])
            )

            sector_pl.extend(
                pl_groups.get(company_id, [])
            )

        path = generate_sector_report(
            sector_name,
            sector_companies,
            sector_ratios,
            sector_pl,
        )

        generated += 1

        print(
            f"Generated: {sector_name} | "
            f"{len(sector_companies)} companies | "
            f"{path}"
        )

    print()
    print(f"Sector PDFs generated: {generated}")
    print(f"Output folder: {OUTPUT_DIR}")
    print("=== SECTOR REPORT GENERATION COMPLETE ===")


if __name__ == "__main__":
    main()