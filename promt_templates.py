"""
Prompt Engineering Templates für KI-Analyse
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class PromptTemplate:
    """Template für strukturierte Prompts"""
    name: str
    system_prompt: str
    user_template: str
    expected_format: str
    temperature: float = 0.7
    max_tokens: int = 2000

class PromptTemplateManager:
    """Verwaltet verschiedene Prompt-Templates für KI-Analyse"""
    
    def __init__(self):
        self.templates = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialisiert Standard-Templates"""
        
        # Haupt-Analyse Template
        self.templates['use_case_analysis'] = PromptTemplate(
            name="KI Use Case Analyse",
            system_prompt="""Du bist ein erfahrener Berater für KI-Implementierung im Handwerk und in kleinen bis mittelständischen Unternehmen. 

Deine Aufgabe ist es, basierend auf einem Unternehmenssteckbrief und einem konkreten KI Use Case eine detaillierte, praxisorientierte Handlungsempfehlung zu erstellen.

Analysiere die Informationen gründlich und erstelle eine strukturierte Antwort mit konkreten, umsetzbaren Empfehlungen.

Antworte IMMER im folgenden JSON-Format:
{
    "zusammenfassung": "Kurze Einschätzung der Situation",
    "handlungsschritte": [
        {
            "prioritaet": "hoch/mittel/niedrig",
            "phase": "Sofort/30 Tage/60 Tage/90+ Tage",
            "titel": "Kurzer Titel",
            "beschreibung": "Detaillierte Beschreibung",
            "aufwand": "gering/mittel/hoch",
            "kosten": "Geschätzte Kosten oder Kostenbereich"
        }
    ],
    "technische_loesungen": [
        {
            "kategorie": "Software/Hardware/Service/Schulung",
            "titel": "Name der Lösung",
            "beschreibung": "Was ist das und wie hilft es?",
            "anbieter": "Mögliche Anbieter/Alternativen",
            "kosten": "Geschätzte Kosten",
            "implementierung": "Wie lange dauert die Einführung?"
        }
    ],
    "risiken": [
        {
            "typ": "technisch/organisatorisch/finanziell",
            "beschreibung": "Was könnte schiefgehen?",
            "wahrscheinlichkeit": "gering/mittel/hoch",
            "auswirkung": "gering/mittel/hoch",
            "massnahmen": "Wie kann man das Risiko minimieren?"
        }
    ],
    "chancen": [
        {
            "bereich": "Effizienz/Qualität/Umsatz/Kosten/Wettbewerb",
            "beschreibung": "Welche Vorteile sind möglich?",
            "potenzial": "gering/mittel/hoch",
            "zeitrahmen": "Wann sind Ergebnisse sichtbar?"
        }
    ],
    "erfolgsmessung": [
        {
            "kpi": "Name der Kennzahl",
            "beschreibung": "Was wird gemessen?",
            "zielwert": "Angestrebter Wert",
            "messintervall": "Wie oft messen?"
        }
    ],
    "naechste_schritte": [
        "Konkrete nächste Schritte in chronologischer Reihenfolge"
    ]
}

Wichtig: 
- Sei konkret und praxisnah
- Berücksichtige die Größe und Branche des Unternehmens  
- Denke an typische Herausforderungen im Handwerk
- Gib realistische Kosten- und Zeitschätzungen
- Antworte ausschließlich in dem geforderten JSON-Format""",
            
            user_template="""Bitte analysiere folgenden KI Use Case für das Unternehmen:

## UNTERNEHMENSSTECKBRIEF:
{company_profile}

## KI USE CASE:
{use_case}

Erstelle eine detaillierte Handlungsempfehlung zur Umsetzung dieses Use Cases für dieses spezifische Unternehmen.""",
            
            expected_format="structured_json",
            temperature=0.7,
            max_tokens=3000
        )
        
        # Quick-Check Template
        self.templates['quick_feasibility'] = PromptTemplate(
            name="Schnelle Machbarkeitsanalyse",
            system_prompt="""Du bist ein KI-Experte und bewertest schnell die Machbarkeit von KI Use Cases.

Antworte im JSON-Format:
{
    "machbarkeit": "sehr gut/gut/mittel/schwierig/unrealistisch",
    "begruendung": "Kurze Begründung",
    "aufwand": "gering/mittel/hoch/sehr hoch", 
    "kosten": "< 1000€ / 1000-5000€ / 5000-20000€ / > 20000€",
    "zeitrahmen": "< 1 Monat / 1-3 Monate / 3-6 Monate / > 6 Monate",
    "haupthindernisse": ["Liste der größten Hürden"],
    "empfehlung": "go/no-go/überdenken"
}""",
            
            user_template="""Bewerte die Machbarkeit:

Unternehmen: {company_name} ({company_size} Mitarbeiter, {company_branch})
Use Case: {use_case_title}
Beschreibung: {use_case_description}""",
            
            expected_format="quick_json",
            temperature=0.3,
            max_tokens=500
        )
        
        # ROI-Analyse Template
        self.templates['roi_analysis'] = PromptTemplate(
            name="ROI und Business Case Analyse",
            system_prompt="""Du bist ein Business-Analyst mit Fokus auf KI-ROI im Mittelstand.

Antworte im JSON-Format:
{
    "investition": {
        "einmalig": "Einmalige Kosten in EUR",
        "laufend_monatlich": "Monatliche Kosten in EUR",
        "gesamt_jahr1": "Gesamtkosten Jahr 1"
    },
    "einsparungen": {
        "zeit_stunden_monat": "Gesparte Stunden pro Monat",
        "kosten_monatlich": "Kosteneinsparung pro Monat",
        "qualitaet": "Qualitätsverbesserungen"
    },
    "roi": {
        "breakeven_monate": "Monate bis Break-Even",
        "roi_jahr1": "ROI in % nach Jahr 1",
        "roi_jahr3": "ROI in % nach Jahr 3"
    },
    "risikofaktoren": ["Faktoren die ROI beeinflussen"],
    "empfehlung": "Investition empfohlen ja/nein"
}""",
            
            user_template="""Erstelle eine ROI-Analyse für:

{company_profile}

{use_case}

Berücksichtige typische Stundenlöhne im Handwerk und realistische Einsparpotenziale.""",
            
            expected_format="roi_json",
            temperature=0.3,
            max_tokens=1000
        )
        
        # Implementierungsplan Template
        self.templates['implementation_plan'] = PromptTemplate(
            name="Detaillierter Implementierungsplan",
            system_prompt="""Du bist ein Projektmanager für KI-Implementierungen.

Erstelle einen detaillierten Projektplan im JSON-Format:
{
    "projektphasen": [
        {
            "phase": "Name der Phase",
            "dauer_wochen": "Anzahl Wochen",
            "ziele": ["Ziele dieser Phase"],
            "aufgaben": [
                {
                    "aufgabe": "Aufgabenbeschreibung",
                    "verantwortlich": "Wer macht es?",
                    "dauer_tage": "Dauer in Tagen",
                    "abhaengigkeiten": ["Wovon hängt es ab?"]
                }
            ],
            "meilensteine": ["Wichtige Meilensteine"],
            "risiken": ["Phasen-spezifische Risiken"]
        }
    ],
    "ressourcen": {
        "personal_intern": ["Benötigte interne Rollen"],
        "personal_extern": ["Externe Berater/Dienstleister"],
        "technologie": ["Hardware/Software Requirements"],
        "budget_gesamt": "Gesamtbudget",
        "budget_phasen": ["Budget pro Phase"]
    },
    "timeline": {
        "start": "Empfohlener Starttermin",
        "meilensteine": [
            {
                "datum": "YYYY-MM-DD",
                "ereignis": "Was passiert?"
            }
        ],
        "go_live": "Geplanter Go-Live Termin"
    },
    "erfolgskriterien": [
        {
            "kriterium": "Messbares Erfolgskriterium",
            "zielwert": "Angestrebter Wert",
            "messzeit": "Wann wird gemessen?"
        }
    ]
}""",
            
            user_template="""Erstelle einen detaillierten Implementierungsplan:

{company_profile}

{use_case}

Plane realistisch und berücksichtige typische Herausforderungen in KMU.""",
            
            expected_format="implementation_json",
            temperature=0.5,
            max_tokens=2500
        )
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Holt ein Template"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """Listet verfügbare Templates"""
        return list(self.templates.keys())
    
    def format_prompt(self, 
                     template_name: str, 
                     company_profile: Dict, 
                     use_case: Dict, 
                     **kwargs) -> List[Dict[str, str]]:
        """
        Formatiert einen Prompt basierend auf Template und Daten
        
        Args:
            template_name: Name des Templates
            company_profile: Unternehmenssteckbrief Daten
            use_case: Use Case Daten
            **kwargs: Zusätzliche Template-Variablen
            
        Returns:
            Formatierte Messages für LM Studio
        """
        
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' nicht gefunden")
        
        # Formatiere Unternehmensdaten
        company_text = self._format_company_profile(company_profile)
        
        # Formatiere Use Case Daten
        use_case_text = self._format_use_case(use_case)
        
        # Template-Variablen vorbereiten
        template_vars = {
            'company_profile': company_text,
            'use_case': use_case_text,
            'company_name': company_profile.get('unternehmensname', 'Unbekannt'),
            'company_size': company_profile.get('mitarbeiter', 'Unbekannt'),
            'company_branch': company_profile.get('branche', 'Unbekannt'),
            'use_case_title': use_case.get('beschreibung', '')[:100] + '...',
            'use_case_description': use_case.get('beschreibung', ''),
            **kwargs
        }
        
        # User-Prompt formatieren
        user_content = template.user_template.format(**template_vars)
        
        # Messages zusammenstellen
        messages = [
            {
                "role": "system",
                "content": template.system_prompt
            },
            {
                "role": "user", 
                "content": user_content
            }
        ]
        
        return messages
    
    def _format_company_profile(self, profile: Dict) -> str:
        """Formatiert Unternehmenssteckbrief für Prompt"""
        
        sections = []
        
        # Grunddaten
        basic_info = f"""**Unternehmen:** {profile.get('unternehmensname', 'N/A')}
**Branche:** {profile.get('branche', 'N/A')}
**Mitarbeiter:** {profile.get('mitarbeiter', 'N/A')}
**Umsatzklasse:** {profile.get('umsatzklasse', 'N/A')}
**Geschäftsradius:** {profile.get('geschaeftsradius', 'N/A')}"""
        sections.append(basic_info)
        
        # Geschäftstätigkeit
        if profile.get('hauptleistungen'):
            sections.append(f"**Hauptleistungen:**\n{profile['hauptleistungen']}")
        
        # Digitalisierungsstand
        digital_systems = self._format_selected_items(profile.get('digitale_systeme', {}))
        if digital_systems:
            sections.append(f"**Digitale Systeme:**\n{digital_systems}")
        
        sections.append(f"**Digitalisierungsgrad:** {profile.get('digitalisierungsgrad', 'N/A')}")
        
        # Herausforderungen
        challenges = self._format_selected_items(profile.get('herausforderungen', {}))
        if challenges:
            sections.append(f"**Aktuelle Herausforderungen:**\n{challenges}")
        
        # KI-Readiness
        sections.append(f"**KI-Verständnis:** {profile.get('ki_verstaendnis', 'N/A')}")
        
        if profile.get('ki_anwendungen'):
            sections.append(f"**Bereits genutzte KI:**\n{profile['ki_anwendungen']}")
        
        return "\n\n".join(sections)
    
    def _format_use_case(self, use_case: Dict) -> str:
        """Formatiert Use Case für Prompt"""
        
        sections = []
        
        # Grunddaten
        basic_info = f"""**Verantwortlich:** {use_case.get('verantwortlich', 'N/A')}
**Bereich:** {use_case.get('bereich', 'N/A')}
**Status:** {use_case.get('status', 'N/A')}"""
        sections.append(basic_info)
        
        # Beschreibung
        if use_case.get('beschreibung'):
            sections.append(f"**Beschreibung:**\n{use_case['beschreibung']}")
        
        if use_case.get('problemstellung'):
            sections.append(f"**Problemstellung:**\n{use_case['problemstellung']}")
        
        if use_case.get('zielstellung'):
            sections.append(f"**Zielstellung:**\n{use_case['zielstellung']}")
        
        # KI-Fähigkeiten
        ki_capabilities = self._format_selected_items(use_case.get('ki_faehigkeiten', {}))
        if ki_capabilities:
            sections.append(f"**Benötigte KI-Fähigkeiten:**\n{ki_capabilities}")
        
        # Strategische Vorteile
        advantages = self._format_selected_items(use_case.get('strategische_vorteile', {}))
        if advantages:
            sections.append(f"**Erwartete strategische Vorteile:**\n{advantages}")
        
        # Bewertung
        if use_case.get('bewertung'):
            bewertung_text = "\n".join([
                f"- {k}: {v}/5" for k, v in use_case['bewertung'].items()
            ])
            sections.append(f"**Technische Bewertung:**\n{bewertung_text}")
        
        # Zeitschätzung
        if use_case.get('entwicklungszeit'):
            sections.append(f"**Geschätzte Entwicklungszeit:** {use_case['entwicklungszeit']}")
        
        return "\n\n".join(sections)
    
    def _format_selected_items(self, items_dict: Dict[str, bool]) -> str:
        """Formatiert ausgewählte Items aus Checkbox-Gruppen"""
        selected = [key for key, value in items_dict.items() if value]
        if selected:
            return "\n".join([f"- {item}" for item in selected])
        return ""
    
    def create_custom_template(self, 
                             name: str,
                             system_prompt: str, 
                             user_template: str,
                             **kwargs) -> PromptTemplate:
        """
        Erstellt ein benutzerdefiniertes Template
        
        Args:
            name: Template-Name
            system_prompt: System-Prompt
            user_template: User-Prompt Template
            **kwargs: Zusätzliche Template-Parameter
            
        Returns:
            Neues PromptTemplate
        """
        
        template = PromptTemplate(
            name=name,
            system_prompt=system_prompt,
            user_template=user_template,
            expected_format=kwargs.get('expected_format', 'text'),
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 2000)
        )
        
        self.templates[name] = template
        return template
    
    def get_template_info(self, template_name: str) -> Dict:
        """Gibt Informationen über ein Template zurück"""
        template = self.get_template(template_name)
        if not template:
            return {}
        
        return {
            'name': template.name,
            'expected_format': template.expected_format,
            'temperature': template.temperature,
            'max_tokens': template.max_tokens,
            'system_prompt_length': len(template.system_prompt),
            'user_template_vars': self._extract_template_vars(template.user_template)
        }
    
    def _extract_template_vars(self, template_str: str) -> List[str]:
        """Extrahiert Template-Variablen aus String"""
        import re
        return re.findall(r'\{(\w+)\}', template_str)
    
    def validate_template_data(self, 
                             template_name: str,
                             company_profile: Dict,
                             use_case: Dict) -> Dict:
        """
        Validiert ob alle Template-Daten verfügbar sind
        
        Returns:
            Validation-Ergebnis mit missing_fields
        """
        
        template = self.get_template(template_name)
        if not template:
            return {'valid': False, 'error': f"Template '{template_name}' nicht gefunden"}
        
        # Erforderliche Felder prüfen
        required_company_fields = ['unternehmensname', 'branche']
        required_use_case_fields = ['beschreibung']
        
        missing_fields = []
        
        for field in required_company_fields:
            if not company_profile.get(field, '').strip():
                missing_fields.append(f"Unternehmen.{field}")
        
        for field in required_use_case_fields:
            if not use_case.get(field, '').strip():
                missing_fields.append(f"UseCase.{field}")
        
        if missing_fields:
            return {
                'valid': False,
                'missing_fields': missing_fields,
                'error': f"Fehlende Pflichtfelder: {', '.join(missing_fields)}"
            }
        
        return {'valid': True}

# Vordefinierte Template-Instanz für einfachen Import
default_prompt_manager = PromptTemplateManager()

def get_analysis_prompt(company_profile: Dict, use_case: Dict) -> List[Dict[str, str]]:
    """
    Convenience-Funktion für Standard-Analyse-Prompt
    
    Args:
        company_profile: Unternehmenssteckbrief
        use_case: KI Use Case
        
    Returns:
        Formatierte Messages
    """
    return default_prompt_manager.format_prompt(
        'use_case_analysis',
        company_profile,
        use_case
    )

def get_quick_check_prompt(company_profile: Dict, use_case: Dict) -> List[Dict[str, str]]:
    """
    Convenience-Funktion für Quick-Check-Prompt
    
    Args:
        company_profile: Unternehmenssteckbrief
        use_case: KI Use Case
        
    Returns:
        Formatierte Messages
    """
    return default_prompt_manager.format_prompt(
        'quick_feasibility',
        company_profile,
        use_case
    )

# Test-Funktionen
def test_prompt_formatting():
    """Test für Prompt-Formatierung"""
    
    # Dummy-Daten
    company = {
        'unternehmensname': 'Muster Handwerk GmbH',
        'branche': 'Elektroinstallation',
        'mitarbeiter': '15',
        'hauptleistungen': 'Elektroinstallationen, Smart Home',
        'digitale_systeme': {
            'Digitale Zeiterfassung': True,
            'CAD-Software': True,
            'Buchhaltungssoftware': False
        },
        'herausforderungen': {
            'Fachkräftemangel': True,
            'Ineffiziente Prozesse/Arbeitsabläufe': True
        }
    }
    
    use_case = {
        'beschreibung': 'KI-gestützte Angebotserstellung',
        'problemstellung': 'Angebotserstellung dauert zu lange',
        'zielstellung': 'Schnellere und genauere Angebote',
        'ki_faehigkeiten': {
            'Computer-Linguistik (Textverständnis)': True,
            'Prognose (Forecasting)': True
        }
    }
    
    manager = PromptTemplateManager()
    
    # Test verschiedene Templates
    for template_name in manager.list_templates():
        print(f"\n=== Testing Template: {template_name} ===")
        
        try:
            messages = manager.format_prompt(template_name, company, use_case)
            print(f"✅ Template formatiert: {len(messages)} messages")
            print(f"System prompt length: {len(messages[0]['content'])}")
            print(f"User prompt length: {len(messages[1]['content'])}")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_prompt_formatting()