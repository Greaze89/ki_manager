"""
Konfigurationsverwaltung für KI Manager
"""

import json
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

@dataclass
class AppConfig:
    """Anwendungs-Konfiguration"""
    # Fenster-Einstellungen
    window_width: int = 1600
    window_height: int = 1000
    window_title: str = "KI Use Case & Unternehmenssteckbrief Manager"
    
    # Verzeichnisse
    docs_folder: str = "Dokumente"
    templates_folder: str = "Templates"
    logs_folder: str = "Logs"
    
    # PDF-Einstellungen
    pdf_page_size: str = "A4"
    pdf_font_size: int = 10
    pdf_title_font_size: int = 18
    
    # UI-Einstellungen
    sidebar_width: int = 250
    pdf_viewer_width: int = 400
    
    # Logo-Einstellungen
    logo_path: str = "assets/logo.png"
    logo_width: int = 200
    logo_height: int = 60

@dataclass
class UseCase:
    """Struktur für KI Use Cases"""
    # Metadaten
    type: str = "use_case"
    created: str = ""
    modified: str = ""
    version: str = "1.0"
    
    # Grundinformationen
    verantwortlich: str = ""
    bereich: str = ""
    status: str = ""
    
    # Beschreibung
    beschreibung: str = ""
    problemstellung: str = ""
    zielstellung: str = ""
    
    # KI-Spezifisch
    ki_faehigkeiten: Dict[str, bool] = None
    ki_vision: str = ""
    
    # Bewertung
    strategische_vorteile: Dict[str, bool] = None
    geschaeftswert: str = ""
    bewertung: Dict[str, int] = None
    entwicklungszeit: str = ""
    
    def __post_init__(self):
        if self.ki_faehigkeiten is None:
            self.ki_faehigkeiten = {}
        if self.strategische_vorteile is None:
            self.strategische_vorteile = {}
        if self.bewertung is None:
            self.bewertung = {}

@dataclass
class CompanyProfile:
    """Struktur für Unternehmenssteckbrief"""
    # Metadaten
    type: str = "company_profile"
    created: str = ""
    modified: str = ""
    version: str = "1.0"
    
    # Unternehmensdaten
    unternehmensname: str = ""
    gruendungsjahr: str = ""
    adresse: str = ""
    branche: str = ""
    mitarbeiter: str = ""
    auszubildende: str = ""
    umsatzklasse: str = ""
    
    # Kontakt
    kontaktperson: str = ""
    position: str = ""
    telefon: str = ""
    email: str = ""
    website: str = ""
    
    # Geschäftstätigkeit
    hauptleistungen: str = ""
    kundengruppen: Dict[str, bool] = None
    geschaeftsradius: str = ""
    auftraege_monat: str = ""
    
    # Digitalisierung
    digitale_systeme: Dict[str, bool] = None
    digitalisierungsgrad: str = ""
    herausforderungen: Dict[str, bool] = None
    digitalisierungspotenzial: str = ""
    
    # KI-Readiness
    ki_verstaendnis: str = ""
    ki_anwendungen: str = ""
    
    def __post_init__(self):
        if self.kundengruppen is None:
            self.kundengruppen = {}
        if self.digitale_systeme is None:
            self.digitale_systeme = {}
        if self.herausforderungen is None:
            self.herausforderungen = {}

# ========================================
# KI-ANALYSE FEATURES - NEUE KLASSEN
# ========================================

@dataclass
class LMStudioSettings:
    """Konfiguration für LM Studio Integration"""
    base_url: str = "http://localhost:1234"
    model_path: str = "C:/Users/ykreppein/.lmstudio/models/lmstudio-community/Qwen2.5-7B-Instruct-GGUF"
    model_name: str = "qwen2.5-7b-instruct"
    timeout_seconds: int = 120
    max_retries: int = 3
    
    # Generierungs-Parameter
    temperature: float = 0.7
    max_tokens: int = 3000
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    
    # Features
    streaming_enabled: bool = True
    auto_retry_enabled: bool = True
    response_validation: bool = True

@dataclass
class AIAnalysis:
    """Struktur für KI-Analyse Ergebnisse"""
    # Metadaten
    id: str
    created: str
    modified: str
    version: str = "1.0"
    
    # Verknüpfungen
    company_profile_id: Optional[str] = None
    use_case_id: Optional[str] = None
    template_used: str = ""
    
    # Prompt und Response
    prompt_messages: List[Dict[str, str]] = None
    raw_response: str = ""
    
    # Strukturierte Ergebnisse
    analysis_summary: str = ""
    recommendations: List[Dict[str, Any]] = None
    implementation_steps: List[Dict[str, Any]] = None
    technical_solutions: List[Dict[str, Any]] = None
    risks: List[Dict[str, Any]] = None
    opportunities: List[Dict[str, Any]] = None
    success_metrics: List[Dict[str, Any]] = None
    next_steps: List[str] = None
    
    # Metrik-Daten
    confidence_score: float = 0.0
    processing_time_seconds: float = 0.0
    token_usage: Dict[str, int] = None
    
    def __post_init__(self):
        if self.prompt_messages is None:
            self.prompt_messages = []
        if self.recommendations is None:
            self.recommendations = []
        if self.implementation_steps is None:
            self.implementation_steps = []
        if self.technical_solutions is None:
            self.technical_solutions = []
        if self.risks is None:
            self.risks = []
        if self.opportunities is None:
            self.opportunities = []
        if self.success_metrics is None:
            self.success_metrics = []
        if self.next_steps is None:
            self.next_steps = []
        if self.token_usage is None:
            self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

@dataclass
class ExtendedAppConfig:
    """Erweiterte App-Konfiguration mit KI-Features"""
    
    # Basis-Einstellungen (kopiert von AppConfig)
    window_width: int = 1600
    window_height: int = 1000
    window_title: str = "KI Use Case & Unternehmenssteckbrief Manager"
    
    # Verzeichnisse
    docs_folder: str = "Dokumente"
    templates_folder: str = "Templates"
    logs_folder: str = "Logs"
    
    # PDF-Einstellungen
    pdf_page_size: str = "A4"
    pdf_font_size: int = 10
    pdf_title_font_size: int = 18
    
    # UI-Einstellungen
    sidebar_width: int = 250
    pdf_viewer_width: int = 400
    
    # Logo-Einstellungen
    logo_path: str = "assets/logo.png"
    logo_width: int = 200
    logo_height: int = 60
    
    # KI-Analyse Einstellungen
    ai_analysis_enabled: bool = True
    lm_studio_settings: LMStudioSettings = None
    
    # UI-Einstellungen für KI-Features
    ai_analysis_panel_width: int = 500
    show_confidence_scores: bool = True
    auto_save_analyses: bool = True
    max_analyses_per_document: int = 10
    
    # Performance-Einstellungen
    analysis_cache_enabled: bool = True
    cache_duration_hours: int = 24
    background_processing: bool = False
    
    def __post_init__(self):
        if self.lm_studio_settings is None:
            self.lm_studio_settings = LMStudioSettings()

# ========================================
# KONFIGURATIONSKLASSEN
# ========================================

class Config:
    """Zentrale Konfigurationsverwaltung (Original)"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.app_config = AppConfig()
        self.load_config()
        self.ensure_directories()
    
    def load_config(self):
        """Lädt Konfiguration aus Datei"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Konfiguration aktualisieren
                    for key, value in data.items():
                        if hasattr(self.app_config, key):
                            setattr(self.app_config, key, value)
            except Exception as e:
                print(f"Warnung: Konfiguration konnte nicht geladen werden: {e}")
    
    def save_config(self):
        """Speichert aktuelle Konfiguration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.app_config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warnung: Konfiguration konnte nicht gespeichert werden: {e}")
    
    def ensure_directories(self):
        """Erstellt notwendige Verzeichnisse"""
        directories = [
            self.app_config.docs_folder,
            self.app_config.templates_folder,
            self.app_config.logs_folder,
            "assets"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def get_ki_capabilities(self) -> List[str]:
        """Gibt verfügbare KI-Fähigkeiten zurück"""
        return [
            'Computer Vision (Bildverarbeitung)',
            'Computer-Audition (Audioverarbeitung)',
            'Computer-Linguistik (Textverständnis)',
            'Robotik (Advanced Robotics)',
            'Prognose (Forecasting)',
            'Entdecken (Discovery)',
            'Planen (Planning)',
            'Erstellung neuer Inhalte (Creation)'
        ]
    
    def get_strategic_advantages(self) -> List[str]:
        """Gibt strategische Vorteile zurück"""
        return [
            'Neues Kundenerlebnis',
            'Umsatzwachstum',
            'Höhere Geschwindigkeit',
            'Reduzierte Komplexität/Risiko',
            'Effizienzsteigerung'
        ]
    
    def get_evaluation_criteria(self) -> List[str]:
        """Gibt Bewertungskriterien zurück"""
        return [
            'Technologie verfügbar',
            'Know-how vorhanden',
            'Daten verfügbar',
            'Geringe Prozessänderungen',
            'Lösungsansatz bekannt'
        ]
    
    def get_customer_groups(self) -> List[str]:
        """Gibt Kundengruppen zurück"""
        return [
            'Privatkunden',
            'Gewerbliche Kunden',
            'Öffentliche Auftraggeber',
            'Andere Handwerksbetriebe'
        ]
    
    def get_digital_systems(self) -> List[str]:
        """Gibt digitale Systeme zurück"""
        return [
            'Digitale Kundenkartei/CRM',
            'Digitale Zeiterfassung',
            'Digitale Rechnungsstellung',
            'Warenwirtschaftssystem',
            'Digitale Projektplanung',
            'Online-Terminvereinbarung',
            'Digitale Baustellendokumentation',
            'CAD-Software',
            'Buchhaltungssoftware',
            'Digitales Materiallager',
            'Online-Marketing/Social Media',
            'Eigene Website',
            'Online-Shop'
        ]
    
    def get_challenges(self) -> List[str]:
        """Gibt betriebliche Herausforderungen zurück"""
        return [
            'Fachkräftemangel',
            'Ineffiziente Prozesse/Arbeitsabläufe',
            'Zeit-/Ressourcenmangel für administrative Aufgaben',
            'Materialbeschaffung/Lieferengpässe',
            'Auftragsakquise/Kundengewinnung',
            'Auftragsverwaltung',
            'Terminplanung/Koordination',
            'Angebotserstellung und Kalkulation',
            'Bürokratie/gesetzliche Anforderungen',
            'Dokumentation',
            'Wissensmanagement/Informationsaustausch'
        ]
    
    def get_status_options(self) -> List[str]:
        """Gibt Status-Optionen zurück"""
        return ['neu', 'in Vorbereitung', 'umgesetzt/laufend']
    
    def get_development_time_options(self) -> List[str]:
        """Gibt Entwicklungszeit-Optionen zurück"""
        return ['< 3 Monate', '4-6 Monate', '7-9 Monate', '10-12 Monate', '> 12 Monate']
    
    def get_revenue_classes(self) -> List[str]:
        """Gibt Umsatzklassen zurück"""
        return ['unter 250.000 €', '250.000-500.000 €', '500.000-1 Mio. €', 'über 1 Mio. €']
    
    def get_business_radius_options(self) -> List[str]:
        """Gibt Geschäftsradius-Optionen zurück"""
        return ['Lokal (Stadt/Kreis)', 'Regional', 'Überregional', 'International']
    
    def get_digitalization_levels(self) -> List[str]:
        """Gibt Digitalisierungsgrade zurück"""
        return ['Weit überdurchschnittlich', 'Überdurchschnittlich', 'Durchschnittlich', 'Unterdurchschnittlich']
    
    def get_ai_understanding_levels(self) -> List[str]:
        """Gibt KI-Verständnisgrade zurück"""
        return ['Sehr gut', 'Gut', 'Grundlegend', 'Gering', 'Keine Kenntnisse']

class ExtendedConfig:
    """Erweiterte Konfiguration mit KI-Features"""
    
    def __init__(self, config_file: str = "config.json"):
        # Basic config setup
        self.config_file = Path(config_file) if isinstance(config_file, str) else config_file
        self.app_config = ExtendedAppConfig()
        
        # KI-spezifische Verzeichnisse
        self.analyses_folder = Path("Analysen")
        self.templates_folder = Path("Templates") 
        self.cache_folder = Path("Cache")
        
        self.load_config()
        self.ensure_ai_directories()
    
    def load_config(self):
        """Lädt Konfiguration aus Datei"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Konfiguration aktualisieren
                    for key, value in data.items():
                        if hasattr(self.app_config, key):
                            setattr(self.app_config, key, value)
            except Exception as e:
                print(f"Warnung: Konfiguration konnte nicht geladen werden: {e}")
    
    def save_config(self):
        """Speichert aktuelle Konfiguration"""
        try:
            # Konvertiere zu Dictionary, behandle LMStudioSettings separat
            config_dict = {}
            for key, value in self.app_config.__dict__.items():
                if isinstance(value, LMStudioSettings):
                    config_dict[key] = value.__dict__
                else:
                    config_dict[key] = value
                    
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warnung: Konfiguration konnte nicht gespeichert werden: {e}")
    
    def ensure_ai_directories(self):
        """Erstellt KI-spezifische Verzeichnisse"""
        directories = [
            self.analyses_folder,
            self.templates_folder,
            self.cache_folder,
            Path(self.app_config.docs_folder),
            Path("assets")
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    # ========================================
    # KI-SPEZIFISCHE METHODEN
    # ========================================
    
    def get_analysis_templates(self) -> List[str]:
        """Gibt verfügbare Analyse-Templates zurück"""
        return [
            "use_case_analysis",
            "quick_feasibility", 
            "roi_analysis",
            "implementation_plan"
        ]
    
    def get_ai_model_options(self) -> List[str]:
        """Gibt verfügbare KI-Modell-Optionen zurück"""
        return [
            "qwen2.5-7b-instruct",
            "llama-3.1-8b-instruct", 
            "mistral-7b-instruct",
            "phi-3-medium",
            "custom"
        ]
    
    def get_confidence_thresholds(self) -> Dict[str, float]:
        """Gibt Confidence-Schwellenwerte zurück"""
        return {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
    
    def get_analysis_categories(self) -> List[str]:
        """Gibt Analyse-Kategorien zurück"""
        return [
            "Handlungsschritte",
            "Technische Lösungen", 
            "Risiken",
            "Chancen",
            "Erfolgsmessung",
            "ROI-Analyse",
            "Implementierungsplan"
        ]
    
    def get_priority_levels(self) -> List[str]:
        """Gibt Prioritätsstufen zurück"""
        return ["hoch", "mittel", "niedrig"]
    
    def get_effort_levels(self) -> List[str]:
        """Gibt Aufwandsstufen zurück"""
        return ["gering", "mittel", "hoch", "sehr hoch"]
    
    def get_cost_ranges(self) -> List[str]:
        """Gibt Kostenbereiche zurück"""
        return [
            "< 1.000 €",
            "1.000 - 5.000 €", 
            "5.000 - 20.000 €",
            "20.000 - 50.000 €",
            "> 50.000 €"
        ]
    
    def get_timeframes(self) -> List[str]:
        """Gibt Zeitrahmen zurück"""
        return [
            "Sofort",
            "< 1 Monat",
            "1-3 Monate", 
            "3-6 Monate",
            "6-12 Monate",
            "> 12 Monate"
        ]
    
    def get_implementation_phases(self) -> List[str]:
        """Gibt Implementierungsphasen zurück"""
        return [
            "Vorbereitung",
            "Konzeption", 
            "Entwicklung",
            "Test",
            "Rollout",
            "Optimierung"
        ]
    
    def validate_lm_studio_config(self) -> Dict[str, Any]:
        """Validiert LM Studio Konfiguration"""
        settings = self.app_config.lm_studio_settings
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # URL validieren
        if not settings.base_url.startswith(("http://", "https://")):
            validation["errors"].append("Ungültige base_url: Muss mit http:// oder https:// beginnen")
            validation["valid"] = False
        
        # Model Path validieren
        model_path = Path(settings.model_path)
        if not model_path.exists():
            validation["warnings"].append(f"Model-Pfad existiert nicht: {model_path}")
        
        # Parameter validieren
        if not 0.0 <= settings.temperature <= 2.0:
            validation["errors"].append("Temperature muss zwischen 0.0 und 2.0 liegen")
            validation["valid"] = False
            
        if settings.max_tokens < 100:
            validation["errors"].append("max_tokens sollte mindestens 100 sein")
            validation["valid"] = False
            
        if not 0.0 <= settings.top_p <= 1.0:
            validation["errors"].append("top_p muss zwischen 0.0 und 1.0 liegen")
            validation["valid"] = False
        
        return validation
    
    def update_lm_studio_settings(self, **kwargs):
        """Aktualisiert LM Studio Einstellungen"""
        settings = self.app_config.lm_studio_settings
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        # Konfiguration speichern
        self.save_config()
    
    def get_analysis_file_path(self, analysis_id: str) -> Path:
        """Gibt Dateipfad für Analyse zurück"""
        return self.analyses_folder / f"analysis_{analysis_id}.json"
    
    def get_cache_file_path(self, cache_key: str) -> Path:
        """Gibt Cache-Dateipfad zurück"""
        return self.cache_folder / f"cache_{cache_key}.json"
    
    # ========================================
    # ALLE ORIGINAL-METHODEN ÜBERNEHMEN
    # ========================================
    
    def get_ki_capabilities(self) -> List[str]:
        """Gibt verfügbare KI-Fähigkeiten zurück"""
        return [
            'Computer Vision (Bildverarbeitung)',
            'Computer-Audition (Audioverarbeitung)',
            'Computer-Linguistik (Textverständnis)',
            'Robotik (Advanced Robotics)',
            'Prognose (Forecasting)',
            'Entdecken (Discovery)',
            'Planen (Planning)',
            'Erstellung neuer Inhalte (Creation)'
        ]
    
    def get_strategic_advantages(self) -> List[str]:
        """Gibt strategische Vorteile zurück"""
        return [
            'Neues Kundenerlebnis',
            'Umsatzwachstum',
            'Höhere Geschwindigkeit',
            'Reduzierte Komplexität/Risiko',
            'Effizienzsteigerung'
        ]
    
    def get_evaluation_criteria(self) -> List[str]:
        """Gibt Bewertungskriterien zurück"""
        return [
            'Technologie verfügbar',
            'Know-how vorhanden',
            'Daten verfügbar',
            'Geringe Prozessänderungen',
            'Lösungsansatz bekannt'
        ]
    
    def get_customer_groups(self) -> List[str]:
        """Gibt Kundengruppen zurück"""
        return [
            'Privatkunden',
            'Gewerbliche Kunden',
            'Öffentliche Auftraggeber',
            'Andere Handwerksbetriebe'
        ]
    
    def get_digital_systems(self) -> List[str]:
        """Gibt digitale Systeme zurück"""
        return [
            'Digitale Kundenkartei/CRM',
            'Digitale Zeiterfassung',
            'Digitale Rechnungsstellung',
            'Warenwirtschaftssystem',
            'Digitale Projektplanung',
            'Online-Terminvereinbarung',
            'Digitale Baustellendokumentation',
            'CAD-Software',
            'Buchhaltungssoftware',
            'Digitales Materiallager',
            'Online-Marketing/Social Media',
            'Eigene Website',
            'Online-Shop'
        ]
    
    def get_challenges(self) -> List[str]:
        """Gibt betriebliche Herausforderungen zurück"""
        return [
            'Fachkräftemangel',
            'Ineffiziente Prozesse/Arbeitsabläufe',
            'Zeit-/Ressourcenmangel für administrative Aufgaben',
            'Materialbeschaffung/Lieferengpässe',
            'Auftragsakquise/Kundengewinnung',
            'Auftragsverwaltung',
            'Terminplanung/Koordination',
            'Angebotserstellung und Kalkulation',
            'Bürokratie/gesetzliche Anforderungen',
            'Dokumentation',
            'Wissensmanagement/Informationsaustausch'
        ]
    
    def get_status_options(self) -> List[str]:
        """Gibt Status-Optionen zurück"""
        return ['neu', 'in Vorbereitung', 'umgesetzt/laufend']
    
    def get_development_time_options(self) -> List[str]:
        """Gibt Entwicklungszeit-Optionen zurück"""
        return ['< 3 Monate', '4-6 Monate', '7-9 Monate', '10-12 Monate', '> 12 Monate']
    
    def get_revenue_classes(self) -> List[str]:
        """Gibt Umsatzklassen zurück"""
        return ['unter 250.000 €', '250.000-500.000 €', '500.000-1 Mio. €', 'über 1 Mio. €']
    
    def get_business_radius_options(self) -> List[str]:
        """Gibt Geschäftsradius-Optionen zurück"""
        return ['Lokal (Stadt/Kreis)', 'Regional', 'Überregional', 'International']
    
    def get_digitalization_levels(self) -> List[str]:
        """Gibt Digitalisierungsgrade zurück"""
        return ['Weit überdurchschnittlich', 'Überdurchschnittlich', 'Durchschnittlich', 'Unterdurchschnittlich']
    
    def get_ai_understanding_levels(self) -> List[str]:
        """Gibt KI-Verständnisgrade zurück"""
        return ['Sehr gut', 'Gut', 'Grundlegend', 'Gering', 'Keine Kenntnisse']

# ========================================
# UTILITY-FUNKTIONEN
# ========================================

def create_analysis_id() -> str:
    """Erstellt eine eindeutige Analyse-ID"""
    return str(uuid.uuid4())[:8]

def format_confidence_score(score: float) -> str:
    """Formatiert Confidence-Score für Anzeige"""
    if score >= 0.8:
        return f"Hoch ({score:.1%})"
    elif score >= 0.6:
        return f"Mittel ({score:.1%})"
    elif score >= 0.4:
        return f"Niedrig ({score:.1%})"
    else:
        return f"Sehr niedrig ({score:.1%})"

def estimate_implementation_effort(steps: List[Dict]) -> str:
    """Schätzt Gesamtaufwand basierend auf Implementierungsschritten"""
    if not steps:
        return "Unbekannt"
    
    effort_mapping = {"gering": 1, "mittel": 2, "hoch": 3, "sehr hoch": 4}
    total_effort = 0
    count = 0
    
    for step in steps:
        effort = step.get("aufwand", "mittel").lower()
        if effort in effort_mapping:
            total_effort += effort_mapping[effort]
            count += 1
    
    if count == 0:
        return "Unbekannt"
    
    avg_effort = total_effort / count
    
    if avg_effort <= 1.5:
        return "Gering"
    elif avg_effort <= 2.5:
        return "Mittel" 
    elif avg_effort <= 3.5:
        return "Hoch"
    else:
        return "Sehr hoch"

def calculate_priority_score(risk_level: str, opportunity_level: str, effort: str) -> int:
    """Berechnet Prioritätsscore für Empfehlungen"""
    
    level_mapping = {"gering": 1, "mittel": 2, "hoch": 3, "sehr hoch": 4}
    
    risk_score = level_mapping.get(risk_level.lower(), 2)
    opportunity_score = level_mapping.get(opportunity_level.lower(), 2) 
    effort_score = level_mapping.get(effort.lower(), 2)
    
    # Höhere Chancen, niedrigere Risiken und geringerer Aufwand = höhere Priorität
    priority_score = (opportunity_score * 2) - risk_score - effort_score
    
    return max(1, min(10, priority_score + 5))  # Normalisiert auf 1-10

# ========================================
# EXPORTS
# ========================================

__all__ = [
    # Original Config Klassen (für Backward-Compatibility)
    'Config', 
    'AppConfig',
    'UseCase', 
    'CompanyProfile',
    
    # Extended Config mit KI-Features
    'ExtendedConfig', 
    'ExtendedAppConfig', 
    'AIAnalysis', 
    'LMStudioSettings',
    
    # Utility Functions
    'create_analysis_id', 
    'format_confidence_score', 
    'estimate_implementation_effort', 
    'calculate_priority_score'
]