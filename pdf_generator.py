"""
PDF-Generator für KI Manager Dokumente
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError as e:
    print(f"ReportLab nicht installiert: {e}")
    print("Installiere mit: pip install reportlab")

from utils.logger import log_function_call, log_performance

class PDFGenerator:
    """Generator für PDF-Dokumente"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("ki_manager")
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Richtet benutzerdefinierte Styles ein"""
        # Titel-Style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=self.config.app_config.pdf_title_font_size,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Untertitel-Style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#34495e')
        )
        
        # Standard Text-Style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=self.config.app_config.pdf_font_size,
            spaceAfter=8
        )
        
        # Tabellen-Stil für Grunddaten
        self.basic_table_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), self.config.app_config.pdf_font_size),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
        
        # Tabellen-Stil für Bewertungen
        self.evaluation_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), self.config.app_config.pdf_font_size),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
    
    @log_performance
    def create_use_case_pdf(self, data: Dict, filepath: Path):
        """
        Erstellt PDF für KI Use Case
        
        Args:
            data: Use Case Daten
            filepath: Ziel-Pfad für PDF
        """
        doc = SimpleDocTemplate(str(filepath), pagesize=A4, topMargin=2*cm)
        story = []
        
        # Header mit Logo (falls vorhanden)
        self._add_header(story)
        
        # Titel
        story.append(Paragraph("KI Use Case Canvas", self.title_style))
        story.append(Spacer(1, 20))
        
        # Grundinformationen
        story.append(Paragraph("Grundinformationen", self.heading_style))
        basic_data = [
            ['Verantwortlich:', self._safe_get(data, 'verantwortlich')],
            ['Bereich/Abteilung:', self._safe_get(data, 'bereich')],
            ['Status:', self._safe_get(data, 'status')],
            ['Erstellt am:', self._format_datetime(data.get('created'))],
            ['Geändert am:', self._format_datetime(data.get('modified'))]
        ]
        
        basic_table = Table(basic_data, colWidths=[4*cm, 12*cm])
        basic_table.setStyle(self.basic_table_style)
        story.append(basic_table)
        story.append(Spacer(1, 20))
        
        # Beschreibung
        story.append(Paragraph("Beschreibung", self.heading_style))
        story.append(Paragraph(f"<b>Use-Case Beschreibung:</b><br/>{self._safe_get(data, 'beschreibung')}", 
                              self.normal_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Problemstellung:</b><br/>{self._safe_get(data, 'problemstellung')}", 
                              self.normal_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Zielstellung/Nutzen:</b><br/>{self._safe_get(data, 'zielstellung')}", 
                              self.normal_style))
        story.append(Spacer(1, 20))
        
        # KI-Fähigkeiten
        story.append(Paragraph("Relevante KI-Fähigkeiten", self.heading_style))
        selected_capabilities = self._get_selected_items(data, 'ki_faehigkeiten')
        if selected_capabilities:
            for capability in selected_capabilities:
                story.append(Paragraph(f"• {capability}", self.normal_style))
        else:
            story.append(Paragraph("Keine KI-Fähigkeiten ausgewählt", self.normal_style))
        story.append(Spacer(1, 20))
        
        # Mehrwert
        story.append(Paragraph("Mehrwert", self.heading_style))
        story.append(Paragraph(f"<b>Passung zur KI-Vision:</b><br/>{self._safe_get(data, 'ki_vision')}", 
                              self.normal_style))
        story.append(Spacer(1, 10))
        
        selected_advantages = self._get_selected_items(data, 'strategische_vorteile')
        if selected_advantages:
            story.append(Paragraph("<b>Strategische Vorteile:</b>", self.normal_style))
            for advantage in selected_advantages:
                story.append(Paragraph(f"• {advantage}", self.normal_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Geschäftswert:</b> {self._safe_get(data, 'geschaeftswert')}", 
                              self.normal_style))
        story.append(Spacer(1, 20))
        
        # Bewertung
        story.append(Paragraph("Bewertung", self.heading_style))
        bewertung_data = [['Kriterium', 'Bewertung (0-5)']]
        
        for criterion, score in data.get('bewertung', {}).items():
            bewertung_data.append([criterion, str(score)])
        
        if len(bewertung_data) > 1:
            bewertung_table = Table(bewertung_data, colWidths=[10*cm, 4*cm])
            bewertung_table.setStyle(self.evaluation_table_style)
            story.append(bewertung_table)
        story.append(Spacer(1, 20))
        
        # Zeitschätzung
        story.append(Paragraph("Zeitschätzung", self.heading_style))
        story.append(Paragraph(f"<b>Entwicklungszeit bis Proof of Concept:</b> {self._safe_get(data, 'entwicklungszeit')}", 
                              self.normal_style))
        
        # Footer
        self._add_footer(story)
        
        doc.build(story)
        self.logger.info(f"Use Case PDF erstellt: {filepath}")
    
    @log_performance
    def create_company_profile_pdf(self, data: Dict, filepath: Path):
        """
        Erstellt PDF für Unternehmenssteckbrief
        
        Args:
            data: Company Profile Daten
            filepath: Ziel-Pfad für PDF
        """
        doc = SimpleDocTemplate(str(filepath), pagesize=A4, topMargin=2*cm)
        story = []
        
        # Header
        self._add_header(story)
        
        # Titel
        story.append(Paragraph("Fragebogen Digitalisierung & KI-Potenzial im Handwerk", self.title_style))
        story.append(Spacer(1, 20))
        
        # Unternehmensdaten
        story.append(Paragraph("Unternehmensdaten", self.heading_style))
        company_data = [
            ['Name des Unternehmens:', self._safe_get(data, 'unternehmensname')],
            ['Gründungsjahr:', self._safe_get(data, 'gruendungsjahr')],
            ['Adresse:', self._safe_get(data, 'adresse')],
            ['Branche/Gewerk:', self._safe_get(data, 'branche')],
            ['Anzahl Mitarbeiter:', self._safe_get(data, 'mitarbeiter')],
            ['Davon Auszubildende:', self._safe_get(data, 'auszubildende')],
            ['Umsatzklasse:', self._safe_get(data, 'umsatzklasse')],
            ['Kontaktperson:', self._safe_get(data, 'kontaktperson')],
            ['Position im Betrieb:', self._safe_get(data, 'position')],
            ['Telefon:', self._safe_get(data, 'telefon')],
            ['E-Mail:', self._safe_get(data, 'email')],
            ['Website:', self._safe_get(data, 'website')],
            ['Erstellt am:', self._format_datetime(data.get('created'))],
            ['Geändert am:', self._format_datetime(data.get('modified'))]
        ]
        
        company_table = Table(company_data, colWidths=[5*cm, 11*cm])
        company_table.setStyle(self.basic_table_style)
        story.append(company_table)
        story.append(Spacer(1, 20))
        
        # Geschäftstätigkeit
        story.append(Paragraph("Aktuelle Geschäftstätigkeit", self.heading_style))
        story.append(Paragraph(f"<b>Hauptleistungen/Produkte:</b><br/>{self._safe_get(data, 'hauptleistungen')}", 
                              self.normal_style))
        story.append(Spacer(1, 10))
        
        # Kundengruppen
        selected_customers = self._get_selected_items(data, 'kundengruppen')
        if selected_customers:
            story.append(Paragraph("<b>Typische Kundengruppen:</b>", self.normal_style))
            for customer in selected_customers:
                story.append(Paragraph(f"• {customer}", self.normal_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Geschäftsradius:</b> {self._safe_get(data, 'geschaeftsradius')}", 
                              self.normal_style))
        story.append(Paragraph(f"<b>Aufträge pro Monat:</b> {self._safe_get(data, 'auftraege_monat')}", 
                              self.normal_style))
        story.append(Spacer(1, 20))
        
        # Digitalisierungsstand
        story.append(Paragraph("Digitalisierungsstand", self.heading_style))
        selected_systems = self._get_selected_items(data, 'digitale_systeme')
        if selected_systems:
            story.append(Paragraph("<b>Genutzte digitale Systeme:</b>", self.normal_style))
            for system in selected_systems:
                story.append(Paragraph(f"• {system}", self.normal_style))
        else:
            story.append(Paragraph("Keine digitalen Systeme ausgewählt", self.normal_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Digitalisierungsgrad im Branchenvergleich:</b> {self._safe_get(data, 'digitalisierungsgrad')}", 
                              self.normal_style))
        story.append(Spacer(1, 20))
        
        # Herausforderungen
        story.append(Paragraph("Herausforderungen & Potenziale", self.heading_style))
        selected_challenges = self._get_selected_items(data, 'herausforderungen')
        if selected_challenges:
            story.append(Paragraph("<b>Größte betriebliche Herausforderungen:</b>", self.normal_style))
            for challenge in selected_challenges:
                story.append(Paragraph(f"• {challenge}", self.normal_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Potenzial für Digitalisierung/KI:</b><br/>{self._safe_get(data, 'digitalisierungspotenzial')}", 
                              self.normal_style))
        story.append(Spacer(1, 20))
        
        # KI-Readiness
        story.append(Paragraph("KI-Readiness", self.heading_style))
        story.append(Paragraph(f"<b>Verständnis von KI-Technologien:</b> {self._safe_get(data, 'ki_verstaendnis')}", 
                              self.normal_style))
        story.append(Paragraph(f"<b>Bereits genutzte KI-Anwendungen:</b> {self._safe_get(data, 'ki_anwendungen')}", 
                              self.normal_style))
        
        # Footer
        self._add_footer(story)
        
        doc.build(story)
        self.logger.info(f"Company Profile PDF erstellt: {filepath}")
    
    def _add_header(self, story):
        """Fügt Header mit Logo hinzu (falls vorhanden)"""
        logo_path = Path(self.config.app_config.logo_path)
        if logo_path.exists():
            try:
                # Logo würde hier eingefügt werden
                # Für jetzt nur Platzhalter
                pass
            except Exception as e:
                self.logger.warning(f"Logo konnte nicht eingefügt werden: {e}")
    
    def _add_footer(self, story):
        """Fügt Footer hinzu"""
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=1,  # Center
            textColor=colors.HexColor('#7f8c8d')
        )
        
        footer_text = f"Erstellt mit KI Manager - {datetime.now().strftime('%d.%m.%Y')}"
        story.append(Paragraph(footer_text, footer_style))
    
    def _safe_get(self, data: Dict, key: str, default: str = "") -> str:
        """Sicherer Zugriff auf Dictionary-Werte"""
        value = data.get(key, default)
        return str(value) if value is not None else default
    
    def _get_selected_items(self, data: Dict, key: str) -> List[str]:
        """Gibt ausgewählte Items aus einem Boolean-Dictionary zurück"""
        items_dict = data.get(key, {})
        return [k for k, v in items_dict.items() if v]
    
    def _format_datetime(self, datetime_str: str) -> str:
        """Formatiert Datetime-String für Anzeige"""
        if not datetime_str:
            return "Nicht verfügbar"
        
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y %H:%M')
        except Exception:
            return datetime_str