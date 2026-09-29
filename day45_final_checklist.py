from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
OUTPUT = ROOT / "output"

DOCS.mkdir(exist_ok=True)

PDF_PATH = DOCS / "acceptance_checklist.pdf"


styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=18,
    leading=22,
    spaceAfter=12,
)

subtitle_style = ParagraphStyle(
    "SubtitleCustom",
    parent=styles["Normal"],
    alignment=TA_CENTER,
    fontSize=10,
    leading=14,
    spaceAfter=16,
)

heading_style = ParagraphStyle(
    "HeadingCustom",
    parent=styles["Heading2"],
    fontSize=12,
    leading=15,
    spaceBefore=10,
    spaceAfter=6,
)

body_style = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontSize=9,
    leading=12,
    spaceAfter=5,
)

small_style = ParagraphStyle(
    "SmallCustom",
    parent=styles["BodyText"],
    fontSize=7.5,
    leading=10,
)

gates = [
    ("AC-01", "FAIL",
     "Companies count = 100; literal criterion requires 92. "
     "Actual project universe contains 100 companies and was preserved."),
    ("AC-02", "PASS",
     "90/100 companies (90.0%) have >=10 years in P&L, BS and CF."),
    ("AC-03", "PASS",
     "Foreign-key check returned 0 rows."),
    ("AC-04", "PASS",
     "financial_ratios contains 1,148 rows; requirement >=1,100."),
    ("AC-05", "PASS",
     "CAGR regression tests passed. Manual Excel spot-check remains a human review item."),
    ("AC-06", "FAIL",
     "Five FYMar 2024 ROE comparisons exceed the specified 5% difference threshold."),
    ("AC-07", "PASS",
     "Quality Compounder screener preset returns 23 rows; requirement 10-50."),
    ("AC-08", "PASS",
     "Company-profile/dashboard performance regression is below 3 seconds."),
    ("AC-09", "PASS",
     "Screener CSV export covered by regression testing."),
    ("AC-10", "PASS",
     "100 tearsheet PDFs exist and all are >=30 KB. Visual review remains a human sign-off item."),
    ("AC-11", "PASS",
     "API health endpoint verified HTTP 200 with status=ok."),
    ("AC-12", "PASS",
     "TCS financial ratios contain 12 distinct years."),
    ("AC-13", "PASS",
     "API screener regression passed and screener_output.xlsx exists."),
    ("AC-14", "PASS",
     "peer_percentiles contains all 11 peer groups."),
    ("AC-15", "PASS",
     "100 cluster-label rows cover all 100 actual companies with no missing cluster_id."),
    ("AC-16", "PASS",
     "956 Pros/Cons rows cover 100 companies; all 100 have both pro and con."),
    ("AC-17", "FAIL",
     "100 tearsheet PDFs exist, all >=30 KB; literal criterion requires 92 PDFs."),
    ("AC-18", "PASS",
     "Final regression: 172 passed, 0 failures, 1 warning."),
    ("AC-19", "PASS",
     "validation_failures.csv exists with the project's actual validation schema; 451 rows."),
    ("AC-20", "PASS",
     "analyst_guide.pdf contains 11 pages; requirement >=10."),
]


deliverables = [
    ("01", "Processed company/data universe", "data/db/n100.db"),
    ("02", "ETL source and loader code", "src/etl/ and src/db_loader.py"),
    ("03", "KPI analytics modules", "src/analytics/"),
    ("04", "Data quality validation", "src/etl/validator.py"),
    ("05", "FastAPI application", "src/api/main.py"),
    ("06", "Dashboard application", "src/dashboard/"),
    ("07", "API OpenAPI specification", "docs/openapi.json"),
    ("08", "Analyst guide Markdown", "docs/analyst_guide.md"),
    ("09", "Analyst guide PDF", "docs/analyst_guide.pdf"),
    ("10", "Screener workbook", "output/screener_output.xlsx"),
    ("11", "Valuation workbook", "output/valuation_summary.xlsx"),
    ("12", "Peer comparison workbook", "output/peer_comparison.xlsx"),
    ("13", "Cash-flow intelligence workbook", "output/cashflow_intelligence.xlsx"),
    ("14", "Cluster labels", "output/cluster_labels.csv"),
    ("15", "Cluster profiles", "output/cluster_profiles.csv"),
    ("16", "Pros/Cons generated output", "output/pros_cons_generated.csv"),
    ("17", "Validation failures", "output/validation_failures.csv"),
    ("18", "Outlier report", "output/outlier_report.csv"),
    ("19", "Portfolio statistics", "output/portfolio_stats.csv"),
    ("20", "Tearsheet PDFs", "reports/tearsheets/"),
    ("21", "Pytest HTML report", "reports/pytest_report.html"),
    ("22", "Day 45 acceptance report", "output/day45_acceptance_report.md"),
    ("23", "Final acceptance checklist", "docs/acceptance_checklist.pdf"),
]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.drawString(
        15 * mm,
        10 * mm,
        "N100 Financial Intelligence Platform — Day 45 Final Sign-Off",
    )
    canvas.drawRightString(
        195 * mm,
        10 * mm,
        f"Page {doc.page}",
    )
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(PDF_PATH),
    pagesize=A4,
    rightMargin=15 * mm,
    leftMargin=15 * mm,
    topMargin=15 * mm,
    bottomMargin=18 * mm,
)

story = []

story.append(Paragraph(
    "N100 FINANCIAL INTELLIGENCE PLATFORM",
    title_style,
))

story.append(Paragraph(
    "Day 45 — Final Acceptance Checklist & Sign-Off",
    subtitle_style,
))

story.append(Paragraph(
    "<b>Final automated result:</b> 17 PASS / 3 FAIL",
    heading_style,
))

story.append(Paragraph(
    "Final regression: <b>172 tests passed, 0 failures, 1 warning</b>. "
    "The warning is an existing Starlette/AnyIO deprecation warning.",
    body_style,
))

story.append(Paragraph(
    "Important dataset note: the Day 45 specification contains a legacy "
    "92-company criterion. The actual project universe contains 100 companies. "
    "The additional companies were preserved rather than deleted solely to "
    "force compliance with the 92-company criterion.",
    body_style,
))

story.append(Paragraph(
    "Acceptance Gates",
    heading_style,
))

gate_data = [
    [
        Paragraph("<b>Gate</b>", small_style),
        Paragraph("<b>Status</b>", small_style),
        Paragraph("<b>Evidence / Result</b>", small_style),
    ]
]

for gate, status, evidence in gates:
    gate_data.append([
        Paragraph(gate, small_style),
        Paragraph(f"<b>{status}</b>", small_style),
        Paragraph(evidence, small_style),
    ])

table = Table(
    gate_data,
    colWidths=[22 * mm, 22 * mm, 136 * mm],
    repeatRows=1,
)

table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))

story.append(table)

story.append(PageBreak())

story.append(Paragraph(
    "23 Final Deliverables",
    heading_style,
))

deliverable_data = [
    [
        Paragraph("<b>#</b>", small_style),
        Paragraph("<b>Deliverable</b>", small_style),
        Paragraph("<b>Path</b>", small_style),
    ]
]

for number, name, path in deliverables:
    deliverable_data.append([
        Paragraph(number, small_style),
        Paragraph(name, small_style),
        Paragraph(path, small_style),
    ])

deliverable_table = Table(
    deliverable_data,
    colWidths=[12 * mm, 72 * mm, 96 * mm],
    repeatRows=1,
)

deliverable_table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))

story.append(deliverable_table)

story.append(Spacer(1, 10))

story.append(Paragraph(
    "Outstanding Review / Exception Items",
    heading_style,
))

story.append(Paragraph(
    "<b>AC-01 / AC-17:</b> The acceptance specification states a 92-company "
    "universe, while the actual controlled project universe contains 100 companies. "
    "The project retains all 100 companies. These gates remain FAIL against the "
    "literal legacy criterion.",
    body_style,
))

story.append(Paragraph(
    "<b>AC-06:</b> Five FYMar 2024 ROE spot checks exceed the specified 5% "
    "difference threshold. The values are documented in the Day 45 acceptance "
    "report. No values were altered merely to force a PASS.",
    body_style,
))

story.append(Paragraph(
    "<b>AC-05 / AC-10:</b> Manual review is required for the Excel CAGR spot-check "
    "and visual text-overflow inspection of five tearsheets.",
    body_style,
))

story.append(Spacer(1, 14))

story.append(Paragraph(
    "Team Lead Sign-Off",
    heading_style,
))

signoff_data = [
    ["Decision / Disposition", "_______________________________"],
    ["Team Lead Name", "_______________________________"],
    ["Signature", "_______________________________"],
    ["Date", "_______________________________"],
    ["Comments / Exceptions Accepted", "_______________________________"],
]

signoff_table = Table(
    signoff_data,
    colWidths=[65 * mm, 105 * mm],
    rowHeights=[12 * mm, 12 * mm, 12 * mm, 12 * mm, 28 * mm],
)

signoff_table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
]))

story.append(signoff_table)

story.append(Spacer(1, 12))

story.append(Paragraph(
    "This checklist records the state of the project at Day 45 final sign-off. "
    "It does not modify or conceal any acceptance exception.",
    body_style,
))

doc.build(story, onFirstPage=footer, onLaterPages=footer)

print(f"Created: {PDF_PATH}")
print("Acceptance checklist generated successfully.")