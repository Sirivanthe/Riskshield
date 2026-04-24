# PDF Report Generator Service
# Generates professional PDF reports for risk assessments

import io
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """
    Generate professional PDF reports for risk assessments.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Check if styles already exist before adding
        if 'CustomTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1e3a5f')
            ))
        
        if 'SectionHeader' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=colors.HexColor('#1e3a5f'),
                borderColor=colors.HexColor('#1e3a5f'),
                borderWidth=1,
                borderPadding=5
            ))
        
        if 'SubHeader' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='SubHeader',
                parent=self.styles['Heading3'],
                fontSize=12,
                spaceBefore=15,
                spaceAfter=8,
                textColor=colors.HexColor('#2c5282')
            ))
        
        if 'BodyText' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=8,
                alignment=TA_JUSTIFY
            ))
        
        if 'RiskCritical' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='RiskCritical',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.white,
                backColor=colors.HexColor('#dc2626'),
                borderPadding=4
            ))
        
        if 'RiskHigh' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='RiskHigh',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.white,
                backColor=colors.HexColor('#ea580c'),
                borderPadding=4
            ))
        
        if 'RiskMedium' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='RiskMedium',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                backColor=colors.HexColor('#fbbf24'),
                borderPadding=4
            ))
        
        if 'RiskLow' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='RiskLow',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.white,
                backColor=colors.HexColor('#16a34a'),
                borderPadding=4
            ))
    
    def _get_risk_color(self, rating: str) -> colors.Color:
        """Get color for risk rating."""
        color_map = {
            'CRITICAL': colors.HexColor('#dc2626'),
            'HIGH': colors.HexColor('#ea580c'),
            'MEDIUM': colors.HexColor('#fbbf24'),
            'LOW': colors.HexColor('#16a34a')
        }
        return color_map.get(rating, colors.grey)
    
    def _get_risk_text_color(self, rating: str) -> colors.Color:
        """Get text color for risk rating."""
        if rating in ['CRITICAL', 'HIGH', 'LOW']:
            return colors.white
        return colors.black
    
    def generate_risk_assessment_report(
        self,
        assessment: Dict[str, Any],
        include_recommendations: bool = True,
        include_questionnaire: bool = False
    ) -> bytes:
        """
        Generate a PDF report for a tech risk assessment.
        
        Args:
            assessment: The assessment data
            include_recommendations: Include control recommendations
            include_questionnaire: Include questionnaire responses
            
        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Title Page
        story.extend(self._create_title_page(assessment))
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary(assessment))
        story.append(Spacer(1, 20))
        
        # Risk Summary Table
        story.extend(self._create_risk_summary(assessment))
        story.append(PageBreak())
        
        # Detailed Risks
        story.extend(self._create_detailed_risks(assessment))
        
        # Recommendations
        if include_recommendations:
            story.append(PageBreak())
            story.extend(self._create_recommendations(assessment))
        
        # Questionnaire Responses
        if include_questionnaire and assessment.get('questionnaire_responses'):
            story.append(PageBreak())
            story.extend(self._create_questionnaire_section(assessment))
        
        # Appendix
        story.append(PageBreak())
        story.extend(self._create_appendix(assessment))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_title_page(self, assessment: Dict[str, Any]) -> List:
        """Create the title page."""
        elements = []
        
        elements.append(Spacer(1, 2*inch))
        
        # Title
        elements.append(Paragraph(
            "Technology Risk Assessment Report",
            self.styles['CustomTitle']
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Application Name
        elements.append(Paragraph(
            f"<b>{assessment.get('app_name', 'Unknown Application')}</b>",
            ParagraphStyle(
                'AppName',
                parent=self.styles['Normal'],
                fontSize=18,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2c5282')
            )
        ))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Assessment ID
        elements.append(Paragraph(
            f"Assessment ID: {assessment.get('assessment_id', 'N/A')}",
            ParagraphStyle(
                'AssessmentID',
                parent=self.styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER
            )
        ))
        
        elements.append(Spacer(1, 1*inch))
        
        # Overall Risk Rating Box
        rating = assessment.get('overall_risk_rating', 'N/A')
        rating_color = self._get_risk_color(rating)
        
        rating_table = Table(
            [[Paragraph(f"<b>Overall Risk Rating: {rating}</b>", 
                       ParagraphStyle('RatingText', fontSize=14, textColor=self._get_risk_text_color(rating), alignment=TA_CENTER))]],
            colWidths=[3*inch]
        )
        rating_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), rating_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ]))
        
        elements.append(rating_table)
        
        elements.append(Spacer(1, 1.5*inch))
        
        # Metadata
        meta_data = [
            ['Assessor:', assessment.get('assessor_name', 'N/A')],
            ['Assessment Date:', assessment.get('created_at', 'N/A')[:10] if assessment.get('created_at') else 'N/A'],
            ['Status:', assessment.get('status', 'N/A')],
            ['Reviewed By:', assessment.get('reviewed_by', 'Pending Review')],
        ]
        
        meta_table = Table(meta_data, colWidths=[1.5*inch, 3*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(meta_table)
        
        return elements
    
    def _create_executive_summary(self, assessment: Dict[str, Any]) -> List:
        """Create executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        risks = assessment.get('identified_risks', [])
        recommendations = assessment.get('recommended_controls', [])
        context = assessment.get('context', {})
        
        # Count risks by severity
        risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for risk in risks:
            rating = risk.get('inherent_rating', 'LOW')
            risk_counts[rating] = risk_counts.get(rating, 0) + 1
        
        summary_text = f"""
        This technology risk assessment was conducted for <b>{assessment.get('app_name', 'the application')}</b> 
        to identify and evaluate potential risks to the organization's technology infrastructure, data, and operations.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • Total risks identified: {len(risks)}<br/>
        • Critical risks: {risk_counts['CRITICAL']}<br/>
        • High risks: {risk_counts['HIGH']}<br/>
        • Medium risks: {risk_counts['MEDIUM']}<br/>
        • Low risks: {risk_counts['LOW']}<br/>
        <br/>
        <b>Recommendations:</b><br/>
        • Total control recommendations: {len(recommendations)}<br/>
        • From existing control library: {len([r for r in recommendations if r.get('source') == 'EXISTING_LIBRARY'])}<br/>
        • New recommendations: {len([r for r in recommendations if r.get('source') == 'NEW_RECOMMENDATION'])}<br/>
        """
        
        elements.append(Paragraph(summary_text, self.styles['BodyText']))
        
        # Application Context Summary
        if context:
            elements.append(Paragraph("Application Context", self.styles['SubHeader']))
            
            context_items = []
            if context.get('description'):
                context_items.append(f"• Description: {context.get('description')}")
            if context.get('business_unit'):
                context_items.append(f"• Business Unit: {context.get('business_unit')}")
            if context.get('criticality'):
                context_items.append(f"• Criticality: {context.get('criticality')}")
            if context.get('data_classification'):
                context_items.append(f"• Data Classification: {context.get('data_classification')}")
            if context.get('deployment_type'):
                context_items.append(f"• Deployment: {context.get('deployment_type')}")
            
            elements.append(Paragraph("<br/>".join(context_items), self.styles['BodyText']))
        
        return elements
    
    def _create_risk_summary(self, assessment: Dict[str, Any]) -> List:
        """Create risk summary table."""
        elements = []
        
        elements.append(Paragraph("Risk Summary", self.styles['SectionHeader']))
        
        risks = assessment.get('identified_risks', [])
        
        if not risks:
            elements.append(Paragraph("No risks identified.", self.styles['BodyText']))
            return elements
        
        # Create risk summary table
        table_data = [['Risk ID', 'Title', 'Category', 'Likelihood', 'Impact', 'Rating']]
        
        for risk in risks:
            table_data.append([
                risk.get('risk_id', 'N/A'),
                Paragraph(risk.get('title', 'N/A')[:40], self.styles['Normal']),
                risk.get('category', 'N/A'),
                risk.get('likelihood', 'N/A'),
                risk.get('impact', 'N/A'),
                risk.get('inherent_rating', 'N/A')
            ])
        
        table = Table(table_data, colWidths=[0.8*inch, 2.2*inch, 1*inch, 0.9*inch, 0.8*inch, 0.8*inch])
        
        # Style the table
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        
        # Color code risk ratings
        for i, risk in enumerate(risks, start=1):
            rating = risk.get('inherent_rating', 'LOW')
            style.append(('BACKGROUND', (5, i), (5, i), self._get_risk_color(rating)))
            style.append(('TEXTCOLOR', (5, i), (5, i), self._get_risk_text_color(rating)))
        
        table.setStyle(TableStyle(style))
        elements.append(table)
        
        return elements
    
    def _create_detailed_risks(self, assessment: Dict[str, Any]) -> List:
        """Create detailed risk descriptions."""
        elements = []
        
        elements.append(Paragraph("Detailed Risk Analysis", self.styles['SectionHeader']))
        
        risks = assessment.get('identified_risks', [])
        
        for i, risk in enumerate(risks, start=1):
            # Risk header with rating badge
            rating = risk.get('inherent_rating', 'LOW')
            
            elements.append(Paragraph(
                f"{i}. {risk.get('title', 'Unknown Risk')}",
                self.styles['SubHeader']
            ))
            
            # Risk details table
            details = [
                ['Risk ID:', risk.get('risk_id', 'N/A')],
                ['Category:', risk.get('category', 'N/A')],
                ['Likelihood:', risk.get('likelihood', 'N/A')],
                ['Impact:', risk.get('impact', 'N/A')],
                ['Inherent Rating:', rating],
                ['Risk Response:', risk.get('risk_response', 'MITIGATE')],
            ]
            
            details_table = Table(details, colWidths=[1.2*inch, 2.5*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (1, 4), (1, 4), self._get_risk_color(rating)),
                ('TEXTCOLOR', (1, 4), (1, 4), self._get_risk_text_color(rating)),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            elements.append(details_table)
            elements.append(Spacer(1, 10))
            
            # Description
            elements.append(Paragraph("<b>Description:</b>", self.styles['Normal']))
            elements.append(Paragraph(risk.get('description', 'No description provided.'), self.styles['BodyText']))
            
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_recommendations(self, assessment: Dict[str, Any]) -> List:
        """Create recommendations section."""
        elements = []
        
        elements.append(Paragraph("Control Recommendations", self.styles['SectionHeader']))
        
        recommendations = assessment.get('recommended_controls', [])
        
        if not recommendations:
            elements.append(Paragraph("No specific control recommendations at this time.", self.styles['BodyText']))
            return elements
        
        # Group by priority
        critical = [r for r in recommendations if r.get('priority') == 'CRITICAL']
        high = [r for r in recommendations if r.get('priority') == 'HIGH']
        medium = [r for r in recommendations if r.get('priority') == 'MEDIUM']
        low = [r for r in recommendations if r.get('priority') == 'LOW']
        
        for priority, recs, color in [
            ('Critical Priority', critical, colors.HexColor('#dc2626')),
            ('High Priority', high, colors.HexColor('#ea580c')),
            ('Medium Priority', medium, colors.HexColor('#fbbf24')),
            ('Low Priority', low, colors.HexColor('#16a34a'))
        ]:
            if recs:
                elements.append(Paragraph(f"<b>{priority}</b>", ParagraphStyle(
                    'Priority', parent=self.styles['Normal'], fontSize=11, 
                    textColor=color, spaceBefore=15, spaceAfter=5
                )))
                
                for rec in recs:
                    elements.append(Paragraph(
                        f"• <b>{rec.get('name', 'N/A')}</b>: {rec.get('description', 'N/A')} "
                        f"[Source: {rec.get('source', 'N/A')}]",
                        self.styles['BodyText']
                    ))
        
        return elements
    
    def _create_questionnaire_section(self, assessment: Dict[str, Any]) -> List:
        """Create questionnaire responses section."""
        elements = []
        
        elements.append(Paragraph("Assessment Questionnaire Responses", self.styles['SectionHeader']))
        
        responses = assessment.get('questionnaire_responses', {})
        
        for key, value in responses.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elements.append(Paragraph(f"<b>{key}:</b> {value}", self.styles['BodyText']))
        
        return elements
    
    def _create_appendix(self, assessment: Dict[str, Any]) -> List:
        """Create appendix section."""
        elements = []
        
        elements.append(Paragraph("Appendix", self.styles['SectionHeader']))
        
        # Risk Rating Definitions
        elements.append(Paragraph("Risk Rating Definitions", self.styles['SubHeader']))
        
        definitions = [
            ['Rating', 'Definition'],
            ['CRITICAL', 'Immediate action required. Risk could result in severe financial, operational, or reputational damage.'],
            ['HIGH', 'Urgent attention needed. Risk could cause significant impact to the organization.'],
            ['MEDIUM', 'Action needed within defined timeframe. Risk could cause moderate impact.'],
            ['LOW', 'Monitor and address as resources permit. Risk has minimal impact potential.'],
        ]
        
        def_table = Table(definitions, colWidths=[1*inch, 5.5*inch])
        def_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(def_table)
        
        elements.append(Spacer(1, 20))
        
        # Report Generation Info
        elements.append(Paragraph("Report Information", self.styles['SubHeader']))
        elements.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>"
            f"Report Version: 1.0<br/>"
            f"Platform: RiskShield Technology Risk Management",
            self.styles['BodyText']
        ))
        
        return elements
