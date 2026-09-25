from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "docs" / "analyst_guide.md"
OUTPUT = ROOT / "docs" / "analyst_guide.pdf"


def markdown_to_pdf():
    """Convert the analyst guide Markdown document into a multi-page PDF."""
    text = SOURCE.read_text(encoding="utf-8")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "GuideTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=18,
    )

    h1_style = ParagraphStyle(
        "GuideH1",
        parent=styles["Heading1"],
        fontSize=17,
        leading=22,
        spaceBefore=8,
        spaceAfter=10,
    )

    h2_style = ParagraphStyle(
        "GuideH2",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        spaceBefore=8,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "GuideBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        spaceAfter=7,
    )

    bullet_style = ParagraphStyle(
        "GuideBullet",
        parent=body_style,
        leftIndent=16,
        firstLineIndent=-8,
        spaceAfter=5,
    )

    code_style = ParagraphStyle(
        "GuideCode",
        parent=body_style,
        fontName="Courier",
        fontSize=8.5,
        leading=12,
        leftIndent=12,
        rightIndent=12,
        spaceBefore=5,
        spaceAfter=8,
    )

    story = []
    lines = text.splitlines()

    in_code = False
    code_lines = []
    content_lines = 0

    def escape(value):
        """Escape Markdown text for ReportLab Paragraph markup."""
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def flush_code():
        """Add the current code block to the PDF."""
        nonlocal code_lines

        if not code_lines:
            return

        code_text = "<br/>".join(escape(line) for line in code_lines)
        story.append(Paragraph(code_text, code_style))
        code_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line:
            story.append(Spacer(1, 4))
            continue

        if content_lines > 0 and content_lines % 6 == 0:
            story.append(PageBreak())

        if line.startswith("# "):
            story.append(
                Paragraph(
                    escape(line[2:]),
                    title_style,
                )
            )
        elif line.startswith("## "):
            story.append(
                Paragraph(
                    escape(line[3:]),
                    h1_style,
                )
            )
        elif line.startswith("### "):
            story.append(
                Paragraph(
                    escape(line[4:]),
                    h2_style,
                )
            )
        elif line.startswith("- "):
            story.append(
                Paragraph(
                    "• " + escape(line[2:]),
                    bullet_style,
                )
            )
        elif line.startswith("> "):
            story.append(
                Paragraph(
                    escape(line[2:]),
                    body_style,
                )
            )
        elif line.startswith("|"):
            story.append(
                Paragraph(
                    escape(line),
                    body_style,
                )
            )
        else:
            story.append(
                Paragraph(
                    escape(line),
                    body_style,
                )
            )

        content_lines += 1

    if in_code:
        flush_code()

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="N100 Financial Intelligence Platform - Analyst Guide",
        author="N100 Financial Intelligence Platform",
    )

    doc.build(story)

    print(f"Created: {OUTPUT}")
    print(f"Source: {SOURCE}")
    print(f"Content lines processed: {content_lines}")


if __name__ == "__main__":
    markdown_to_pdf()