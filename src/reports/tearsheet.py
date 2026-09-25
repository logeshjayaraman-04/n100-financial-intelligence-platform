"""Module providing N100 financial intelligence functionality."""

import math
import sqlite3
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "n100.db"

OUTPUT_DIR = ROOT / "reports" / "tearsheets"
RADAR_DIR = ROOT / "reports" / "radar_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================


def get_connection():
    """Retrieve connection."""
    return sqlite3.connect(DB_PATH)


def safe_float(value):
    """Handle safe float."""
    try:
        if value is None:
            return None
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except (TypeError, ValueError):
        return None


def fmt_number(value, decimals=2):
    """Handle fmt number."""
    value = safe_float(value)
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_pct(value, decimals=1):
    """Handle fmt pct."""
    value = safe_float(value)
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def latest_rows(rows, count=5):
    """Handle latest rows."""
    return rows[-count:] if rows else []


def row_value(row, key):
    """Handle row value."""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


# ============================================================
# DATA LOADING
# ============================================================


def load_company(company_id):
    """Retrieve company."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    company = conn.execute(
        """
        SELECT *
        FROM companies
        WHERE id = ?
        """,
        (company_id,),
    ).fetchone()

    if company is None:
        conn.close()
        return None

    sector = conn.execute(
        """
        SELECT broad_sector, sub_sector, market_cap_category
        FROM sectors
        WHERE company_id = ?
        LIMIT 1
        """,
        (company_id,),
    ).fetchone()

    ratios = conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY
            CASE
                WHEN CAST(year AS TEXT) GLOB '[0-9]*'
                THEN CAST(year AS INTEGER)
                ELSE 9999
            END,
            year
        """,
        (company_id,),
    ).fetchall()

    pl = conn.execute(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY
            CASE
                WHEN CAST(year AS TEXT) GLOB '[0-9]*'
                THEN CAST(year AS INTEGER)
                ELSE 9999
            END,
            year
        """,
        (company_id,),
    ).fetchall()

    cf = conn.execute(
        """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY
            CASE
                WHEN CAST(year AS TEXT) GLOB '[0-9]*'
                THEN CAST(year AS INTEGER)
                ELSE 9999
            END,
            year
        """,
        (company_id,),
    ).fetchall()

    market = conn.execute(
        """
        SELECT *
        FROM market_cap
        WHERE company_id = ?
        ORDER BY
            CASE
                WHEN CAST(year AS TEXT) GLOB '[0-9]*'
                THEN CAST(year AS INTEGER)
                ELSE 9999
            END,
            year
        """,
        (company_id,),
    ).fetchall()

    pros_cons = conn.execute(
        """
        SELECT pros, cons
        FROM prosandcons
        WHERE company_id = ?
        LIMIT 1
        """,
        (company_id,),
    ).fetchone()

    conn.close()

    return {
        "company": company,
        "sector": sector,
        "ratios": ratios,
        "pl": pl,
        "cf": cf,
        "market": market,
        "pros_cons": pros_cons,
    }


def load_capital_allocation(company_id):
    """Retrieve capital allocation."""
    path = ROOT / "output" / "capital_allocation.csv"

    if not path.exists():
        return []

    import csv

    rows = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if str(row.get("company_id", "")).strip() == str(company_id):
                rows.append(row)

    return rows


def load_cashflow_intelligence(company_id):
    """Retrieve cashflow intelligence."""
    path = ROOT / "output" / "cashflow_intelligence.xlsx"

    if not path.exists():
        return None

    try:
        import openpyxl

        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active

        headers = [cell.value for cell in ws[1]]

        for values in ws.iter_rows(min_row=2, values_only=True):
            row = dict(zip(headers, values))

            if str(row.get("company_id", "")).strip() == str(company_id):
                return row

    except Exception:
        return None

    return None


def load_generated_pros_cons(company_id):
    """Retrieve generated pros cons."""
    path = ROOT / "output" / "pros_cons_generated.csv"

    if not path.exists():
        return [], []

    import csv

    pros = []
    cons = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if str(row.get("company_id", "")).strip() != str(company_id):
                continue

            confidence = safe_float(row.get("confidence_pct"))

            if confidence is not None and confidence <= 60:
                continue

            item = {
                "text": row.get("text", ""),
                "confidence": confidence,
                "rule_id": row.get("rule_id", ""),
            }

            if str(row.get("type", "")).lower() == "pro":
                pros.append(item)
            elif str(row.get("type", "")).lower() == "con":
                cons.append(item)

    pros.sort(key=lambda x: x["confidence"] or 0, reverse=True)
    cons.sort(key=lambda x: x["confidence"] or 0, reverse=True)

    return pros, cons


# ============================================================
# DRAWING HELPERS
# ============================================================

PAGE_W, PAGE_H = A4

MARGIN = 14 * mm
CONTENT_W = PAGE_W - (2 * MARGIN)


def draw_header(c, title, subtitle=None):
    """Render header."""
    c.setFillColor(colors.HexColor("#17365D"))
    c.rect(0, PAGE_H - 18 * mm, PAGE_W, 18 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, PAGE_H - 11 * mm, title)

    if subtitle:
        c.setFont("Helvetica", 8)
        c.drawRightString(
            PAGE_W - MARGIN,
            PAGE_H - 11 * mm,
            subtitle[:90],
        )


def draw_footer(c, company_id, page_no):
    """Render footer."""
    c.setStrokeColor(colors.HexColor("#B7C9D6"))
    c.line(MARGIN, 10 * mm, PAGE_W - MARGIN, 10 * mm)

    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 7)

    c.drawString(
        MARGIN,
        6.5 * mm,
        f"N100 Financial Intelligence Platform | {company_id}",
    )

    c.drawRightString(
        PAGE_W - MARGIN,
        6.5 * mm,
        f"Page {page_no} of 2",
    )


def draw_section_title(c, x, y, title, width=CONTENT_W):
    """Render section title."""
    c.setFillColor(colors.HexColor("#EAF0F5"))
    c.roundRect(x, y - 5 * mm, width, 8 * mm, 2 * mm, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#17365D"))
    c.setFont("Helvetica-Bold", 9)

    c.drawString(x + 3 * mm, y - 2 * mm, title)

    return y - 10 * mm


def draw_kpi_card(c, x, y, w, h, label, value):
    """Render kpi card."""
    c.setStrokeColor(colors.HexColor("#D0D7DE"))
    c.setFillColor(colors.white)
    c.roundRect(x, y - h, w, h, 2 * mm, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#666666"))
    c.setFont("Helvetica", 7)
    c.drawString(x + 3 * mm, y - 5 * mm, label[:26])

    c.setFillColor(colors.HexColor("#17365D"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 3 * mm, y - 11 * mm, str(value)[:22])


def draw_table(c, x, y, widths, rows, row_h=7 * mm, font_size=7):
    """Render table."""
    if not rows:
        return y

    total_w = sum(widths)

    for r, row in enumerate(rows):
        current_x = x

        if r == 0:
            c.setFillColor(colors.HexColor("#17365D"))
            c.setStrokeColor(colors.HexColor("#17365D"))
            text_color = colors.white
            font_name = "Helvetica-Bold"
        else:
            c.setFillColor(colors.HexColor("#F7F9FB") if r % 2 == 0 else colors.white)
            c.setStrokeColor(colors.HexColor("#D9E0E6"))
            text_color = colors.HexColor("#222222")
            font_name = "Helvetica"

        c.rect(
            x,
            y - row_h,
            total_w,
            row_h,
            fill=1,
            stroke=1,
        )

        for i, cell in enumerate(row):
            width = widths[i]

            c.setFillColor(text_color)
            c.setFont(font_name, font_size)

            text = "" if cell is None else str(cell)
            text = text[:42]

            c.drawString(
                current_x + 2 * mm,
                y - row_h + 2.3 * mm,
                text,
            )

            current_x += width

        y -= row_h

    return y


def draw_bullets(c, x, y, items, max_items=5, width=CONTENT_W):
    """Render bullets."""
    c.setFillColor(colors.HexColor("#222222"))
    c.setFont("Helvetica", 7.5)

    used = 0

    for item in items[:max_items]:
        text = str(item.get("text", "")).strip()

        if not text:
            continue

        confidence = item.get("confidence")

        if confidence is not None:
            suffix = f"  [{confidence:.0f}%]"
        else:
            suffix = ""

        text = text[:105] + ("..." if len(text) > 105 else "")
        text = "• " + text + suffix

        c.drawString(x, y, text)
        y -= 5.5 * mm
        used += 1

    if used == 0:
        c.setFillColor(colors.HexColor("#777777"))
        c.drawString(x, y, "No generated items available.")

    return y


def trend_arrow(current, previous):
    """Handle trend arrow."""
    current = safe_float(current)
    previous = safe_float(previous)

    if current is None or previous is None:
        return "→"

    if current > previous:
        return "↑"

    if current < previous:
        return "↓"

    return "→"


# ============================================================
# TEARSHEET GENERATOR
# ============================================================


def generate_tearsheet(company_id):
    """Build or generate tearsheet."""
    data = load_company(company_id)

    if data is None:
        raise ValueError(f"Company ID not found: {company_id}")

    company = data["company"]
    sector = data["sector"]
    ratios = data["ratios"]
    pl = data["pl"]
    cf = data["cf"]
    market = data["market"]

    company_name = company["company_name"]
    sector_name = sector["broad_sector"] if sector and sector["broad_sector"] else "N/A"

    pdf_path = OUTPUT_DIR / f"{company_id}_tearsheet.pdf"

    c = canvas.Canvas(
        str(pdf_path),
        pagesize=A4,
        pageCompression=1,
    )

    c.setTitle(f"{company_name} - N100 Financial Intelligence")
    c.setAuthor("N100 Financial Intelligence Platform")

    # --------------------------------------------------------
    # PAGE 1
    # --------------------------------------------------------

    draw_header(
        c,
        company_name,
        f"{company_id} | {sector_name}",
    )

    y = PAGE_H - 28 * mm

    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 8)

    subtitle = (
        f"Sector: {sector_name}    |    "
        f"Sub-sector: {sector['sub_sector'] if sector and sector['sub_sector'] else 'N/A'}"
    )

    c.drawString(MARGIN, y, subtitle)

    y -= 8 * mm

    # Latest rows
    latest_ratio = ratios[-1] if ratios else None
    prev_ratio = ratios[-2] if len(ratios) >= 2 else None

    latest_pl = pl[-1] if pl else None
    pl[-2] if len(pl) >= 2 else None

    latest_cf = cf[-1] if cf else None
    cf[-2] if len(cf) >= 2 else None

    # KPI cards
    card_gap = 3 * mm
    card_w = (CONTENT_W - 3 * card_gap) / 4
    card_h = 19 * mm

    kpis = [
        (
            "Revenue",
            fmt_number(row_value(latest_pl, "sales") if latest_pl else None),
        ),
        (
            "Net Profit",
            fmt_number(row_value(latest_pl, "net_profit") if latest_pl else None),
        ),
        (
            "CFO",
            fmt_number(
                row_value(latest_cf, "operating_activity") if latest_cf else None
            ),
        ),
        (
            "FCF",
            fmt_number(
                row_value(latest_ratio, "free_cash_flow_cr") if latest_ratio else None
            ),
        ),
    ]

    x = MARGIN

    for label, value in kpis:
        draw_kpi_card(
            c,
            x,
            y,
            card_w,
            card_h,
            label,
            value,
        )
        x += card_w + card_gap

    y -= 25 * mm

    # Quality metrics
    y = draw_section_title(
        c,
        MARGIN,
        y,
        "QUALITY & BALANCE SHEET",
    )

    quality_rows = [
        [
            "Metric",
            "Latest",
            "Previous",
            "Trend",
        ],
        [
            "ROE",
            fmt_pct(
                row_value(latest_ratio, "return_on_equity_pct")
                if latest_ratio
                else None
            ),
            fmt_pct(
                row_value(prev_ratio, "return_on_equity_pct") if prev_ratio else None
            ),
            trend_arrow(
                (
                    row_value(latest_ratio, "return_on_equity_pct")
                    if latest_ratio
                    else None
                ),
                row_value(prev_ratio, "return_on_equity_pct") if prev_ratio else None,
            ),
        ],
        [
            "Debt / Equity",
            fmt_number(
                row_value(latest_ratio, "debt_to_equity") if latest_ratio else None
            ),
            fmt_number(row_value(prev_ratio, "debt_to_equity") if prev_ratio else None),
            trend_arrow(
                row_value(prev_ratio, "debt_to_equity") if prev_ratio else None,
                row_value(latest_ratio, "debt_to_equity") if latest_ratio else None,
            ),
        ],
        [
            "Interest Coverage",
            fmt_number(
                row_value(latest_ratio, "interest_coverage") if latest_ratio else None
            ),
            fmt_number(
                row_value(prev_ratio, "interest_coverage") if prev_ratio else None
            ),
            trend_arrow(
                row_value(latest_ratio, "interest_coverage") if latest_ratio else None,
                row_value(prev_ratio, "interest_coverage") if prev_ratio else None,
            ),
        ],
        [
            "Net Profit Margin",
            fmt_pct(
                row_value(latest_ratio, "net_profit_margin_pct")
                if latest_ratio
                else None
            ),
            fmt_pct(
                row_value(prev_ratio, "net_profit_margin_pct") if prev_ratio else None
            ),
            trend_arrow(
                (
                    row_value(latest_ratio, "net_profit_margin_pct")
                    if latest_ratio
                    else None
                ),
                row_value(prev_ratio, "net_profit_margin_pct") if prev_ratio else None,
            ),
        ],
        [
            "Operating Margin",
            fmt_pct(
                row_value(latest_ratio, "operating_profit_margin_pct")
                if latest_ratio
                else None
            ),
            fmt_pct(
                row_value(prev_ratio, "operating_profit_margin_pct")
                if prev_ratio
                else None
            ),
            trend_arrow(
                (
                    row_value(latest_ratio, "operating_profit_margin_pct")
                    if latest_ratio
                    else None
                ),
                (
                    row_value(prev_ratio, "operating_profit_margin_pct")
                    if prev_ratio
                    else None
                ),
            ),
        ],
    ]

    y = draw_table(
        c,
        MARGIN,
        y,
        [58 * mm, 34 * mm, 34 * mm, 22 * mm],
        quality_rows,
        row_h=7 * mm,
    )

    y -= 7 * mm

    # Growth
    y = draw_section_title(
        c,
        MARGIN,
        y,
        "GROWTH ENGINE",
    )

    growth_rows = [
        [
            "Metric",
            "5Y CAGR",
            "Quality Score",
        ],
        [
            "Revenue CAGR",
            fmt_pct(
                row_value(latest_ratio, "revenue_cagr_5yr") if latest_ratio else None
            ),
            fmt_number(
                row_value(latest_ratio, "composite_quality_score")
                if latest_ratio
                else None
            ),
        ],
        [
            "PAT CAGR",
            fmt_pct(row_value(latest_ratio, "pat_cagr_5yr") if latest_ratio else None),
            "—",
        ],
        [
            "EPS CAGR",
            fmt_pct(row_value(latest_ratio, "eps_cagr_5yr") if latest_ratio else None),
            "—",
        ],
    ]

    y = draw_table(
        c,
        MARGIN,
        y,
        [70 * mm, 40 * mm, 38 * mm],
        growth_rows,
        row_h=7 * mm,
    )

    y -= 7 * mm

    # Capital allocation + distress
    intelligence = load_cashflow_intelligence(company_id)
    allocations = load_capital_allocation(company_id)

    latest_allocation = (
        allocations[-1].get("pattern_label", "N/A") if allocations else "N/A"
    )

    distress = intelligence.get("distress_level", "N/A") if intelligence else "N/A"

    cfo_quality = intelligence.get("cfo_pat_quality", "N/A") if intelligence else "N/A"

    capex_intensity_value = (
        intelligence.get("capex_intensity", "N/A") if intelligence else "N/A"
    )

    y = draw_section_title(
        c,
        MARGIN,
        y,
        "CASH FLOW INTELLIGENCE",
    )

    intelligence_rows = [
        ["Signal", "Current assessment"],
        ["CFO / PAT Quality", str(cfo_quality)[:38]],
        ["CapEx Intensity", str(capex_intensity_value)[:38]],
        ["Distress Level", str(distress)[:38]],
        ["Capital Allocation", str(latest_allocation)[:38]],
    ]

    y = draw_table(
        c,
        MARGIN,
        y,
        [58 * mm, 90 * mm],
        intelligence_rows,
        row_h=7 * mm,
    )

    draw_footer(c, company_id, 1)

    c.showPage()

    # --------------------------------------------------------
    # PAGE 2
    # --------------------------------------------------------

    draw_header(
        c,
        f"{company_name} — Financial Trends",
        f"{company_id}",
    )

    y = PAGE_H - 28 * mm

    # Historical trend table
    y = draw_section_title(
        c,
        MARGIN,
        y,
        "HISTORICAL FINANCIALS",
    )

    pl_rows = latest_rows(pl, 6)

    trend_rows = [
        [
            "Year",
            "Sales",
            "PAT",
            "CFO",
            "FCF",
            "ROE",
        ]
    ]

    for i in range(len(pl_rows)):
        pl_row = pl_rows[i]

        year = row_value(pl_row, "year")

        ratio_row = None
        cf_row = None

        for rr in ratios:
            if str(row_value(rr, "year")) == str(year):
                ratio_row = rr

        for cr in cf:
            if str(row_value(cr, "year")) == str(year):
                cf_row = cr

        trend_rows.append(
            [
                str(year),
                fmt_number(row_value(pl_row, "sales")),
                fmt_number(row_value(pl_row, "net_profit")),
                fmt_number(row_value(cf_row, "operating_activity") if cf_row else None),
                fmt_number(
                    row_value(ratio_row, "free_cash_flow_cr") if ratio_row else None
                ),
                fmt_pct(
                    row_value(ratio_row, "return_on_equity_pct") if ratio_row else None
                ),
            ]
        )

    y = draw_table(
        c,
        MARGIN,
        y,
        [24 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 25 * mm],
        trend_rows,
        row_h=7 * mm,
        font_size=6.5,
    )

    y -= 8 * mm

    # Pros and cons
    pros, cons = load_generated_pros_cons(company_id)

    y = draw_section_title(
        c,
        MARGIN,
        y,
        "NLP INVESTMENT SIGNALS",
    )

    col_gap = 6 * mm
    col_w = (CONTENT_W - col_gap) / 2

    c.setFillColor(colors.HexColor("#17365D"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y, "PROS")

    c.drawString(
        MARGIN + col_w + col_gap,
        y,
        "CONS",
    )

    bullet_y = y - 6 * mm

    # Pros
    draw_bullets(
        c,
        MARGIN,
        bullet_y,
        pros,
        max_items=5,
        width=col_w,
    )

    # Cons
    draw_bullets(
        c,
        MARGIN + col_w + col_gap,
        bullet_y,
        cons,
        max_items=5,
        width=col_w,
    )

    y -= 36 * mm

    # Valuation
    y = draw_section_title(
        c,
        MARGIN,
        y,
        "VALUATION SNAPSHOT",
    )

    latest_market = market[-1] if market else None

    valuation_rows = [
        ["Metric", "Latest"],
        [
            "Market Cap",
            fmt_number(
                row_value(latest_market, "market_cap_crore") if latest_market else None
            ),
        ],
        [
            "Enterprise Value",
            fmt_number(
                row_value(latest_market, "enterprise_value_crore")
                if latest_market
                else None
            ),
        ],
        [
            "P / E",
            fmt_number(row_value(latest_market, "pe_ratio") if latest_market else None),
        ],
        [
            "P / B",
            fmt_number(row_value(latest_market, "pb_ratio") if latest_market else None),
        ],
        [
            "EV / EBITDA",
            fmt_number(
                row_value(latest_market, "ev_ebitda") if latest_market else None
            ),
        ],
    ]

    y = draw_table(
        c,
        MARGIN,
        y,
        [65 * mm, 80 * mm],
        valuation_rows,
        row_h=7 * mm,
    )

    y -= 7 * mm

    # Existing radar chart
    radar_path = RADAR_DIR / f"{company_id}_radar.png"

    if radar_path.exists():
        try:
            c.drawImage(
                str(radar_path),
                PAGE_W - MARGIN - 55 * mm,
                25 * mm,
                width=48 * mm,
                height=48 * mm,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
        except Exception:
            pass

    # Report notes
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 6.5)

    notes = [
        "Source: N100 financial database and generated Sprint 5 analytics.",
        "Values are presented as stored in the project database; N/A indicates unavailable data.",
        "Trend arrows compare the latest available observation with the preceding observation.",
    ]

    note_y = 42 * mm

    for note in notes:
        c.drawString(MARGIN, note_y, note)
        note_y -= 4 * mm

    draw_footer(c, company_id, 2)

    c.showPage()
    c.save()

    return pdf_path


# ============================================================
# TEST / COMMAND LINE
# ============================================================


def get_sample_companies(limit=5):
    """Retrieve sample companies."""
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, company_name
        FROM companies
        ORDER BY id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return rows


def main():
    """Run the module's main workflow."""
    print("=== DAY 33 TEARSHEET GENERATOR ===")

    samples = get_sample_companies(5)

    if not samples:
        print("No companies found.")
        return

    generated = []

    for company_id, company_name in samples:
        try:
            path = generate_tearsheet(company_id)

            generated.append(path)

            print(f"Generated: {company_id} | " f"{company_name} | " f"{path}")

        except Exception as exc:
            print(f"FAILED: {company_id} | " f"{company_name} | " f"{exc}")

    print()
    print(f"Generated PDFs: {len(generated)}")
    print("Output folder:", OUTPUT_DIR)
    print("=== DAY 33 GENERATION COMPLETE ===")


if __name__ == "__main__":
    main()
