# Workpaper Generator
# Produces detailed audit workpapers (PDF + Excel) from control-analysis data.

import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


EFFECTIVENESS_COLORS = {
    "EFFECTIVE": colors.HexColor("#16a34a"),
    "PARTIALLY_EFFECTIVE": colors.HexColor("#fbbf24"),
    "INEFFECTIVE": colors.HexColor("#dc2626"),
    "NOT_TESTED": colors.HexColor("#6b7280"),
}

STATUS_COLORS = {
    "PASS": colors.HexColor("#16a34a"),
    "PARTIAL": colors.HexColor("#fbbf24"),
    "FAIL": colors.HexColor("#dc2626"),
    "INSUFFICIENT": colors.HexColor("#6b7280"),
    "ERROR": colors.HexColor("#6b7280"),
}


class WorkpaperGenerator:
    """Generate audit workpapers for the Control Analysis module."""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self) -> None:
        if "WPTitle" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name="WPTitle",
                parent=self.styles["Heading1"],
                fontSize=22,
                alignment=TA_CENTER,
                spaceAfter=24,
                textColor=colors.HexColor("#1e3a5f"),
            ))
        if "WPSection" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name="WPSection",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceBefore=16,
                spaceAfter=8,
                textColor=colors.HexColor("#1e3a5f"),
            ))
        if "WPSub" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name="WPSub",
                parent=self.styles["Heading3"],
                fontSize=11,
                spaceBefore=10,
                spaceAfter=4,
                textColor=colors.HexColor("#2c5282"),
            ))
        if "WPBody" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name="WPBody",
                parent=self.styles["Normal"],
                fontSize=9,
                alignment=TA_JUSTIFY,
                spaceAfter=6,
            ))
        if "WPSmall" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name="WPSmall",
                parent=self.styles["Normal"],
                fontSize=8,
                alignment=TA_LEFT,
            ))

    # -------------------- PDF --------------------
    def generate_pdf(self, data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )

        story: List[Any] = []
        story.extend(self._cover(data))
        story.append(PageBreak())
        story.extend(self._quality_section(data))
        story.append(PageBreak())
        story.extend(self._register_section(data))
        story.append(PageBreak())
        story.extend(self._detailed_workpapers(data))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _cover(self, data: Dict[str, Any]) -> List[Any]:
        elements: List[Any] = []
        elements.append(Spacer(1, 1.5 * inch))
        elements.append(Paragraph("Control Analysis Audit Workpaper", self.styles["WPTitle"]))
        elements.append(Spacer(1, 0.3 * inch))

        meta = [
            ["Generated At:", data.get("generated_at", "")],
            ["Tenant:", data.get("tenant_id", "default")],
            ["Total Controls:", str(data.get("total_controls", 0))],
            ["Quality Score:", f"{data.get('quality', {}).get('quality_score', 0):.2f} / 100"],
        ]
        table = Table(meta, colWidths=[2 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 0.4 * inch))
        elements.append(Paragraph(
            "This workpaper consolidates control register quality metrics, evidence "
            "evaluations against test scripts, and 5W1H audit narratives. It is produced "
            "by RiskShield's Control Analysis module.",
            self.styles["WPBody"],
        ))
        return elements

    def _quality_section(self, data: Dict[str, Any]) -> List[Any]:
        q = data.get("quality", {}) or {}
        elements: List[Any] = []
        elements.append(Paragraph("1. Control Register Quality", self.styles["WPSection"]))

        rows = [
            ["Metric", "Value"],
            ["Total Controls", q.get("total_controls", 0)],
            ["Duplicates Found", q.get("duplicates_found", 0)],
            ["Missing Descriptions", q.get("missing_descriptions", 0)],
            ["Missing Owners", q.get("missing_owners", 0)],
            ["Missing Test Procedures", q.get("missing_test_procedures", 0)],
            ["Weak Controls", q.get("weak_controls", 0)],
            ["Strong Controls", q.get("strong_controls", 0)],
            ["Overall Quality Score", f"{q.get('quality_score', 0):.2f} / 100"],
        ]
        table = Table(rows, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)

        # Domain coverage
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("Domain Coverage", self.styles["WPSub"]))
        dom = q.get("domain_coverage", {}) or {}
        if dom:
            dom_rows = [["Domain", "# Controls"]] + [[d, c] for d, c in dom.items()]
            dtable = Table(dom_rows, colWidths=[3.5 * inch, 1.5 * inch])
            dtable.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(dtable)
        return elements

    def _register_section(self, data: Dict[str, Any]) -> List[Any]:
        elements: List[Any] = []
        elements.append(Paragraph("2. Control Register Summary", self.styles["WPSection"]))

        header = ["Control ID", "Name", "Domain", "Owner", "Effectiveness", "Last Tested"]
        rows = [header]
        for c in data.get("controls", []):
            rows.append([
                str(c.get("control_id", ""))[:18],
                Paragraph(str(c.get("name", ""))[:70], self.styles["WPSmall"]),
                str(c.get("domain", ""))[:18],
                str(c.get("owner", ""))[:22],
                str(c.get("effectiveness", "NOT_TESTED")),
                str(c.get("last_tested", ""))[:10],
            ])

        table = Table(rows, colWidths=[1.0 * inch, 2.2 * inch, 1.1 * inch, 1.3 * inch, 1.1 * inch, 0.9 * inch])
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for i, c in enumerate(data.get("controls", []), start=1):
            eff = c.get("effectiveness", "NOT_TESTED")
            color = EFFECTIVENESS_COLORS.get(eff, colors.grey)
            style.append(("BACKGROUND", (4, i), (4, i), color))
            style.append(("TEXTCOLOR", (4, i), (4, i), colors.white))
        table.setStyle(TableStyle(style))
        elements.append(table)
        return elements

    def _detailed_workpapers(self, data: Dict[str, Any]) -> List[Any]:
        elements: List[Any] = []
        elements.append(Paragraph("3. Detailed Workpapers (per control)", self.styles["WPSection"]))

        for idx, c in enumerate(data.get("controls", []), start=1):
            if idx > 1:
                elements.append(Spacer(1, 0.15 * inch))
            elements.append(Paragraph(
                f"{idx}. {c.get('control_id', '')} - {c.get('name', '')}",
                self.styles["WPSub"],
            ))

            meta_rows = [
                ["Domain", str(c.get("domain", ""))],
                ["Owner", str(c.get("owner", ""))],
                ["Type / Category", f"{c.get('type', '')} / {c.get('category', '')}"],
                ["Frameworks", ", ".join(c.get("frameworks", []) or [])],
                ["Effectiveness", str(c.get("effectiveness", "NOT_TESTED"))],
                ["Last Tested", str(c.get("last_tested", ""))[:19]],
            ]
            mtable = Table(meta_rows, colWidths=[1.4 * inch, 5.4 * inch])
            mtable.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(mtable)

            elements.append(Paragraph("<b>Description:</b>", self.styles["WPSmall"]))
            elements.append(Paragraph(str(c.get("description", "") or "N/A"), self.styles["WPBody"]))

            elements.append(Paragraph("<b>Test Procedure:</b>", self.styles["WPSmall"]))
            elements.append(Paragraph(str(c.get("test_procedure", "") or "N/A"), self.styles["WPBody"]))

            # Latest evaluation
            latest = c.get("latest_evaluation")
            if latest:
                ev = latest.get("evaluation", {}) or {}
                nar = latest.get("narrative_5w1h", {}) or {}

                elements.append(Paragraph("<b>Latest Evidence Evaluation</b>", self.styles["WPSmall"]))
                status = ev.get("status", "INSUFFICIENT")
                status_color = STATUS_COLORS.get(status, colors.grey)
                ev_rows = [
                    ["Status", status],
                    ["Confidence", f"{ev.get('confidence', 0)}%"],
                    ["Audit Opinion", ev.get("audit_opinion", "")],
                    ["Reasoning", ev.get("reasoning", "")],
                    ["Gaps", "; ".join(ev.get("gaps", []) or [])],
                    ["Recommendations", "; ".join(ev.get("recommendations", []) or [])],
                ]
                etable = Table(ev_rows, colWidths=[1.4 * inch, 5.4 * inch])
                etable.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                    ("BACKGROUND", (1, 0), (1, 0), status_color),
                    ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                elements.append(etable)

                if nar:
                    elements.append(Paragraph("<b>5W1H Narrative</b>", self.styles["WPSmall"]))
                    w_rows = [
                        ["Who", nar.get("who", "")],
                        ["What", nar.get("what", "")],
                        ["When", nar.get("when", "")],
                        ["Where", nar.get("where", "")],
                        ["Why", nar.get("why", "")],
                        ["How", nar.get("how", "")],
                        ["Summary", nar.get("summary", "")],
                        ["Conclusion", nar.get("audit_conclusion", "")],
                    ]
                    wtable = Table(w_rows, colWidths=[1.0 * inch, 5.8 * inch])
                    wtable.setStyle(TableStyle([
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]))
                    elements.append(wtable)
            else:
                elements.append(Paragraph(
                    "<i>No evidence evaluation has been performed for this control.</i>",
                    self.styles["WPSmall"],
                ))

        return elements

    # -------------------- Excel --------------------
    def generate_excel(self, data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        controls = data.get("controls", [])
        quality = data.get("quality", {}) or {}

        # Register sheet
        register_rows = []
        for c in controls:
            register_rows.append({
                "Control ID": c.get("control_id", ""),
                "Name": c.get("name", ""),
                "Description": c.get("description", ""),
                "Domain": c.get("domain", ""),
                "Owner": c.get("owner", ""),
                "Type": c.get("type", ""),
                "Category": c.get("category", ""),
                "Frameworks": ", ".join(c.get("frameworks", []) or []),
                "Test Procedure": c.get("test_procedure", ""),
                "Effectiveness": c.get("effectiveness", "NOT_TESTED"),
                "Last Tested": c.get("last_tested", ""),
                "Source": c.get("source", ""),
            })
        register_df = pd.DataFrame(register_rows) if register_rows else pd.DataFrame(
            columns=["Control ID", "Name"]
        )

        # Quality sheet
        quality_rows = [
            {"Metric": "Total Controls", "Value": quality.get("total_controls", 0)},
            {"Metric": "Duplicates Found", "Value": quality.get("duplicates_found", 0)},
            {"Metric": "Missing Descriptions", "Value": quality.get("missing_descriptions", 0)},
            {"Metric": "Missing Owners", "Value": quality.get("missing_owners", 0)},
            {"Metric": "Missing Test Procedures", "Value": quality.get("missing_test_procedures", 0)},
            {"Metric": "Weak Controls", "Value": quality.get("weak_controls", 0)},
            {"Metric": "Strong Controls", "Value": quality.get("strong_controls", 0)},
            {"Metric": "Overall Quality Score", "Value": quality.get("quality_score", 0)},
        ]
        quality_df = pd.DataFrame(quality_rows)

        # Domain coverage sheet
        domain_df = pd.DataFrame([
            {"Domain": k, "Controls": v}
            for k, v in (quality.get("domain_coverage") or {}).items()
        ])

        # Evaluations sheet
        eval_rows = []
        for c in controls:
            latest = c.get("latest_evaluation")
            if not latest:
                continue
            ev = latest.get("evaluation", {}) or {}
            nar = latest.get("narrative_5w1h", {}) or {}
            eval_rows.append({
                "Control ID": c.get("control_id", ""),
                "Name": c.get("name", ""),
                "Status": ev.get("status", ""),
                "Confidence": ev.get("confidence", 0),
                "Effectiveness": ev.get("effectiveness", ""),
                "Audit Opinion": ev.get("audit_opinion", ""),
                "Reasoning": ev.get("reasoning", ""),
                "Gaps": "; ".join(ev.get("gaps", []) or []),
                "Recommendations": "; ".join(ev.get("recommendations", []) or []),
                "Who": nar.get("who", ""),
                "What": nar.get("what", ""),
                "When": nar.get("when", ""),
                "Where": nar.get("where", ""),
                "Why": nar.get("why", ""),
                "How": nar.get("how", ""),
                "5W1H Summary": nar.get("summary", ""),
                "5W1H Conclusion": nar.get("audit_conclusion", ""),
                "Evaluated At": latest.get("created_at", ""),
                "Evidence File": latest.get("evidence_filename", ""),
            })
        eval_df = pd.DataFrame(eval_rows) if eval_rows else pd.DataFrame(
            columns=["Control ID", "Status"]
        )

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            register_df.to_excel(writer, sheet_name="Control Register", index=False)
            quality_df.to_excel(writer, sheet_name="Quality Summary", index=False)
            if not domain_df.empty:
                domain_df.to_excel(writer, sheet_name="Domain Coverage", index=False)
            eval_df.to_excel(writer, sheet_name="Evidence Evaluations", index=False)

            # Style headers
            header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            for sheet in writer.sheets.values():
                for cell in sheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                for column_cells in sheet.columns:
                    length = max(
                        (len(str(cell.value)) if cell.value is not None else 0)
                        for cell in column_cells
                    )
                    sheet.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 12), 60)

        buffer.seek(0)
        return buffer.getvalue()
