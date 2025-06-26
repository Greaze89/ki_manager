"""
AI-Modul für KI-Analyse und Handlungsempfehlungen

Dieses Modul integriert LM Studio (Qwen2.5-7B-Instruct) für KI-basierte 
Handlungsempfehlungen zur Umsetzung von Use Cases.
"""

from .lm_studio_client import LMStudioClient, LMStudioConfig, LMStudioError
from .prompt_templates import (
    PromptTemplateManager, 
    PromptTemplate,
    default_prompt_manager,
    get_analysis_prompt,
    get_quick_check_prompt
)
from .response_parser import ResponseParser, ParseResult
from .analysis_engine import AnalysisEngine, AnalysisEngineError

__version__ = "1.0.0"

__all__ = [
    # Client & Config
    'LMStudioClient',
    'LMStudioConfig', 
    'LMStudioError',
    
    # Prompt Management
    'PromptTemplateManager',
    'PromptTemplate',
    'default_prompt_manager',
    'get_analysis_prompt',
    'get_quick_check_prompt',
    
    # Response Processing
    'ResponseParser',
    'ParseResult',
    
    # Main Engine
    'AnalysisEngine',
    'AnalysisEngineError'
]

# Convenience-Funktionen

def create_analysis_engine(config):
    """
    Erstellt eine konfigurierte AnalysisEngine
    
    Args:
        config: ExtendedConfig Instanz
        
    Returns:
        AnalysisEngine Instanz
    """
    return AnalysisEngine(config)

def test_lm_studio_connection():
    """
    Testet die Verbindung zu LM Studio
    
    Returns:
        bool: True wenn Verbindung erfolgreich
    """
    try:
        from .lm_studio_client import test_lm_studio_connection
        return test_lm_studio_connection()
    except ImportError:
        return False

def get_available_templates():
    """
    Gibt verfügbare Analyse-Templates zurück
    
    Returns:
        List[str]: Template-Namen
    """
    return default_prompt_manager.list_templates()

def validate_ai_prerequisites():
    """
    Prüft ob alle AI-Voraussetzungen erfüllt sind
    
    Returns:
        Dict: Status-Informationen
    """
    status = {
        "lm_studio_available": False,
        "templates_loaded": False,
        "ready": False,
        "errors": []
    }
    
    try:
        # LM Studio testen
        client = LMStudioClient()
        status["lm_studio_available"] = client.check_connection()
        client.close()
        
        # Templates prüfen
        templates = get_available_templates()
        status["templates_loaded"] = len(templates) > 0
        
        # Overall ready status
        status["ready"] = (
            status["lm_studio_available"] and 
            status["templates_loaded"]
        )
        
        if not status["lm_studio_available"]:
            status["errors"].append("LM Studio nicht erreichbar")
        
        if not status["templates_loaded"]:
            status["errors"].append("Keine Templates verfügbar")
            
    except Exception as e:
        status["errors"].append(f"Unerwarteter Fehler: {e}")
    
    return status

# Modul-Level Konfiguration

DEFAULT_MODEL_CONFIG = {
    "base_url": "http://localhost:1234",
    "model_name": "qwen2.5-7b-instruct",
    "temperature": 0.7,
    "max_tokens": 3000
}

SUPPORTED_FORMATS = [
    "structured_json",
    "quick_json", 
    "roi_json",
    "implementation_json"
]

ANALYSIS_TYPES = [
    "use_case_analysis",
    "quick_feasibility",
    "roi_analysis", 
    "implementation_plan"
]

# Version Info
def get_version_info():
    """Gibt Versions-Informationen zurück"""
    return {
        "ai_module_version": __version__,
        "supported_models": ["qwen2.5-7b-instruct", "llama-3.1-8b", "mistral-7b"],
        "supported_formats": SUPPORTED_FORMATS,
        "analysis_types": ANALYSIS_TYPES
    }