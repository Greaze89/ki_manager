"""
KI-Analyse Engine - Hauptlogik für KI-basierte Handlungsempfehlungen
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from ai.lm_studio_client import LMStudioClient, LMStudioConfig, LMStudioError
from ai.prompt_templates import PromptTemplateManager
from ai.response_parser import ResponseParser
from utils.config import ExtendedConfig, AIAnalysis, create_analysis_id
from utils.logger import log_function_call, log_performance

class AnalysisEngineError(Exception):
    """Custom Exception für Analysis Engine"""
    pass

class AnalysisEngine:
    """Hauptklasse für KI-basierte Use Case Analyse"""
    
    def __init__(self, config: ExtendedConfig):
        self.config = config
        self.logger = logging.getLogger("ki_manager.analysis_engine")
        
        # LM Studio Client initialisieren
        lm_config = LMStudioConfig(
            base_url=config.app_config.lm_studio_settings.base_url,
            model_name=config.app_config.lm_studio_settings.model_name,
            timeout=config.app_config.lm_studio_settings.timeout_seconds,
            max_retries=config.app_config.lm_studio_settings.max_retries,
            temperature=config.app_config.lm_studio_settings.temperature,
            max_tokens=config.app_config.lm_studio_settings.max_tokens,
            top_p=config.app_config.lm_studio_settings.top_p
        )
        
        self.lm_client = LMStudioClient(lm_config)
        self.prompt_manager = PromptTemplateManager()
        self.response_parser = ResponseParser()
        
        self.logger.info("Analysis Engine initialisiert")
    
    @log_function_call
    def check_prerequisites(self) -> Dict[str, Any]:
        """
        Prüft ob alle Voraussetzungen für Analyse erfüllt sind
        
        Returns:
            Status-Dictionary mit Prüfungsergebnissen
        """
        
        status = {
            "ready": True,
            "lm_studio_connection": False,
            "model_available": False,
            "config_valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            # LM Studio Verbindung prüfen
            if self.lm_client.check_connection():
                status["lm_studio_connection"] = True
                status["model_available"] = True
                self.logger.info("✅ LM Studio Verbindung erfolgreich")
            else:
                status["ready"] = False
                status["errors"].append("LM Studio ist nicht erreichbar")
                self.logger.error("❌ LM Studio Verbindung fehlgeschlagen")
            
            # Konfiguration validieren
            config_validation = self.config.validate_lm_studio_config()
            if config_validation["valid"]:
                status["config_valid"] = True
            else:
                status["ready"] = False
                status["errors"].extend(config_validation["errors"])
                status["warnings"].extend(config_validation.get("warnings", []))
            
            # Verzeichnisse prüfen
            if not self.config.analyses_folder.exists():
                status["warnings"].append("Analyse-Ordner existiert nicht")
            
        except Exception as e:
            status["ready"] = False
            status["errors"].append(f"Unerwarteter Fehler: {e}")
            self.logger.error(f"Fehler bei Voraussetzungsprüfung: {e}")
        
        return status
    
    @log_performance
    def analyze_use_case(self, 
                        company_profile: Dict,
                        use_case: Dict,
                        template_name: str = "use_case_analysis",
                        **kwargs) -> AIAnalysis:
        """
        Führt eine vollständige KI-Analyse des Use Cases durch
        
        Args:
            company_profile: Unternehmenssteckbrief Daten
            use_case: Use Case Daten
            template_name: Name des zu verwendenden Prompt-Templates
            **kwargs: Zusätzliche Parameter für die Analyse
            
        Returns:
            AIAnalysis Objekt mit strukturierten Ergebnissen
            
        Raises:
            AnalysisEngineError: Bei Analyse-Fehlern
        """
        
        start_time = time.time()
        analysis_id = create_analysis_id()
        
        self.logger.info(f"Starte Analyse {analysis_id} mit Template '{template_name}'")
        
        try:
            # Daten validieren
            validation = self.prompt_manager.validate_template_data(
                template_name, company_profile, use_case
            )
            
            if not validation["valid"]:
                raise AnalysisEngineError(f"Datenvalidierung fehlgeschlagen: {validation['error']}")
            
            # Prompt generieren
            messages = self.prompt_manager.format_prompt(
                template_name, company_profile, use_case, **kwargs
            )
            
            # Template-Informationen holen
            template = self.prompt_manager.get_template(template_name)
            if not template:
                raise AnalysisEngineError(f"Template '{template_name}' nicht gefunden")
            
            # KI-Generation durchführen
            self.logger.debug(f"Sende Request an LM Studio (Template: {template_name})")
            
            response = self.lm_client.generate_completion(
                messages,
                temperature=template.temperature,
                max_tokens=template.max_tokens
            )
            
            # Response-Text extrahieren
            raw_response = self.lm_client.extract_response_text(response)
            
            # Response parsen und strukturieren
            parsed_response = self.response_parser.parse_response(
                raw_response, template.expected_format
            )
            
            # Token-Usage extrahieren
            token_usage = response.get('usage', {})
            
            # Verarbeitungszeit berechnen
            processing_time = time.time() - start_time
            
            # AIAnalysis Objekt erstellen
            analysis = AIAnalysis(
                id=analysis_id,
                created=datetime.now().isoformat(),
                modified=datetime.now().isoformat(),
                company_profile_id=company_profile.get('id'),
                use_case_id=use_case.get('id'),
                template_used=template_name,
                prompt_messages=messages,
                raw_response=raw_response,
                processing_time_seconds=processing_time,
                token_usage=token_usage
            )
            
            # Strukturierte Daten hinzufügen
            self._populate_analysis_fields(analysis, parsed_response)
            
            # Confidence Score berechnen
            analysis.confidence_score = self._calculate_confidence_score(
                parsed_response, raw_response, template_name
            )
            
            self.logger.info(
                f"Analyse {analysis_id} abgeschlossen in {processing_time:.2f}s "
                f"(Confidence: {analysis.confidence_score:.2f})"
            )
            
            return analysis
            
        except LMStudioError as e:
            raise AnalysisEngineError(f"LM Studio Fehler: {e}")
        except Exception as e:
            self.logger.error(f"Analyse {analysis_id} fehlgeschlagen: {e}")
            raise AnalysisEngineError(f"Analyse fehlgeschlagen: {e}")
    
    def _populate_analysis_fields(self, analysis: AIAnalysis, parsed_data: Dict):
        """Füllt AIAnalysis Felder aus geparsten Daten"""
        
        # Zusammenfassung
        analysis.analysis_summary = parsed_data.get('zusammenfassung', '')
        
        # Handlungsschritte
        analysis.implementation_steps = parsed_data.get('handlungsschritte', [])
        
        # Technische Lösungen  
        analysis.technical_solutions = parsed_data.get('technische_loesungen', [])
        
        # Risiken
        analysis.risks = parsed_data.get('risiken', [])
        
        # Chancen
        analysis.opportunities = parsed_data.get('chancen', [])
        
        # Erfolgsmessung
        analysis.success_metrics = parsed_data.get('erfolgsmessung', [])
        
        # Nächste Schritte
        analysis.next_steps = parsed_data.get('naechste_schritte', [])
        
        # Generelle Empfehlungen (falls vorhanden)
        analysis.recommendations = parsed_data.get('empfehlungen', [])
    
    def _calculate_confidence_score(self, 
                                  parsed_data: Dict, 
                                  raw_response: str,
                                  template_name: str) -> float:
        """
        Berechnet Confidence Score basierend auf verschiedenen Faktoren
        
        Args:
            parsed_data: Geparste Antwort-Daten
            raw_response: Original-Response Text
            template_name: Verwendetes Template
            
        Returns:
            Confidence Score zwischen 0.0 und 1.0
        """
        
        confidence_factors = []
        
        # Faktor 1: Vollständigkeit der strukturierten Antwort
        expected_fields = {
            'use_case_analysis': ['zusammenfassung', 'handlungsschritte', 'technische_loesungen'],
            'quick_feasibility': ['machbarkeit', 'aufwand', 'empfehlung'],
            'roi_analysis': ['investition', 'einsparungen', 'roi'],
            'implementation_plan': ['projektphasen', 'timeline']
        }
        
        required_fields = expected_fields.get(template_name, [])
        if required_fields:
            present_fields = len([f for f in required_fields if f in parsed_data])
            completeness_score = present_fields / len(required_fields)
            confidence_factors.append(completeness_score)
        
        # Faktor 2: Länge und Detailgrad der Antwort
        response_length = len(raw_response)
        if response_length > 2000:
            length_score = 1.0
        elif response_length > 1000:
            length_score = 0.8
        elif response_length > 500:
            length_score = 0.6
        else:
            length_score = 0.4
        confidence_factors.append(length_score)
        
        # Faktor 3: Strukturiertheit (JSON-Parsing erfolgreich)
        if parsed_data and isinstance(parsed_data, dict):
            structure_score = 1.0
        else:
            structure_score = 0.3
        confidence_factors.append(structure_score)
        
        # Faktor 4: Anzahl konkreter Empfehlungen
        total_recommendations = 0
        for field in ['handlungsschritte', 'technische_loesungen', 'naechste_schritte']:
            if field in parsed_data:
                total_recommendations += len(parsed_data[field])
        
        if total_recommendations >= 5:
            detail_score = 1.0
        elif total_recommendations >= 3:
            detail_score = 0.8
        elif total_recommendations >= 1:
            detail_score = 0.6
        else:
            detail_score = 0.2
        confidence_factors.append(detail_score)
        
        # Gewichteter Durchschnitt
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5  # Neutral bei fehlenden Faktoren
    
    @log_function_call
    def analyze_multiple_scenarios(self,
                                 company_profile: Dict,
                                 use_cases: List[Dict],
                                 template_name: str = "use_case_analysis") -> List[AIAnalysis]:
        """
        Analysiert mehrere Use Cases für ein Unternehmen
        
        Args:
            company_profile: Unternehmenssteckbrief
            use_cases: Liste von Use Cases
            template_name: Template für Analyse
            
        Returns:
            Liste von AIAnalysis Objekten
        """
        
        analyses = []
        
        for i, use_case in enumerate(use_cases):
            self.logger.info(f"Analysiere Use Case {i+1}/{len(use_cases)}")
            
            try:
                analysis = self.analyze_use_case(
                    company_profile, use_case, template_name
                )
                analyses.append(analysis)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Use Case {i+1}: {e}")
                # Weitermachen mit nächstem Use Case
                continue
        
        return analyses
    
    @log_function_call
    def quick_feasibility_check(self,
                              company_profile: Dict,
                              use_case: Dict) -> Dict[str, Any]:
        """
        Führt eine schnelle Machbarkeitsanalyse durch
        
        Args:
            company_profile: Unternehmenssteckbrief
            use_case: Use Case Daten
            
        Returns:
            Machbarkeits-Assessment
        """
        
        try:
            analysis = self.analyze_use_case(
                company_profile, 
                use_case, 
                template_name="quick_feasibility"
            )
            
            # Extrahiere Machbarkeits-Informationen
            parsed_data = self.response_parser.parse_response(
                analysis.raw_response, "quick_json"
            )
            
            return {
                "analysis_id": analysis.id,
                "feasible": parsed_data.get("empfehlung", "überdenken") == "go",
                "feasibility_level": parsed_data.get("machbarkeit", "mittel"),
                "effort": parsed_data.get("aufwand", "mittel"),
                "cost_estimate": parsed_data.get("kosten", "unbekannt"),
                "timeframe": parsed_data.get("zeitrahmen", "unbekannt"),
                "main_obstacles": parsed_data.get("haupthindernisse", []),
                "confidence": analysis.confidence_score,
                "full_analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Quick feasibility check fehlgeschlagen: {e}")
            return {
                "feasible": False,
                "error": str(e),
                "confidence": 0.0
            }
    
    @log_function_call
    def generate_implementation_roadmap(self,
                                      company_profile: Dict,
                                      use_case: Dict) -> Dict[str, Any]:
        """
        Generiert einen detaillierten Implementierungsplan
        
        Args:
            company_profile: Unternehmenssteckbrief
            use_case: Use Case Daten
            
        Returns:
            Implementierungs-Roadmap
        """
        
        try:
            analysis = self.analyze_use_case(
                company_profile,
                use_case,
                template_name="implementation_plan"
            )
            
            parsed_data = self.response_parser.parse_response(
                analysis.raw_response, "implementation_json"
            )
            
            return {
                "analysis_id": analysis.id,
                "project_phases": parsed_data.get("projektphasen", []),
                "resources": parsed_data.get("ressourcen", {}),
                "timeline": parsed_data.get("timeline", {}),
                "success_criteria": parsed_data.get("erfolgskriterien", []),
                "total_duration_weeks": self._calculate_total_duration(
                    parsed_data.get("projektphasen", [])
                ),
                "confidence": analysis.confidence_score,
                "full_analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Implementation roadmap generation fehlgeschlagen: {e}")
            return {
                "error": str(e),
                "confidence": 0.0
            }
    
    def _calculate_total_duration(self, phases: List[Dict]) -> int:
        """Berechnet Gesamtdauer aus Projektphasen"""
        total_weeks = 0
        
        for phase in phases:
            weeks = phase.get("dauer_wochen", 0)
            if isinstance(weeks, (int, float)):
                total_weeks += weeks
            elif isinstance(weeks, str):
                try:
                    total_weeks += float(weeks)
                except ValueError:
                    pass
        
        return int(total_weeks)
    
    @log_function_call
    def compare_use_cases(self,
                         company_profile: Dict,
                         use_cases: List[Dict]) -> Dict[str, Any]:
        """
        Vergleicht mehrere Use Cases miteinander
        
        Args:
            company_profile: Unternehmenssteckbrief
            use_cases: Liste von Use Cases zum Vergleich
            
        Returns:
            Vergleichs-Analyse
        """
        
        if len(use_cases) < 2:
            raise AnalysisEngineError("Mindestens 2 Use Cases für Vergleich erforderlich")
        
        # Schnelle Machbarkeitsanalyse für alle Use Cases
        feasibility_results = []
        
        for i, use_case in enumerate(use_cases):
            self.logger.info(f"Prüfe Machbarkeit für Use Case {i+1}")
            result = self.quick_feasibility_check(company_profile, use_case)
            result["use_case_index"] = i
            result["use_case_title"] = use_case.get("beschreibung", f"Use Case {i+1}")[:50]
            feasibility_results.append(result)
        
        # Ranking erstellen
        ranked_results = sorted(
            feasibility_results,
            key=lambda x: (
                x.get("feasible", False),
                x.get("confidence", 0.0),
                self._effort_to_score(x.get("effort", "hoch"))
            ),
            reverse=True
        )
        
        return {
            "total_use_cases": len(use_cases),
            "feasible_count": len([r for r in feasibility_results if r.get("feasible", False)]),
            "ranked_results": ranked_results,
            "recommendation": ranked_results[0] if ranked_results else None,
            "comparison_summary": self._generate_comparison_summary(ranked_results)
        }
    
    def _effort_to_score(self, effort_str: str) -> float:
        """Konvertiert Aufwands-String zu numerischem Score"""
        effort_mapping = {
            "gering": 4.0,
            "mittel": 3.0, 
            "hoch": 2.0,
            "sehr hoch": 1.0
        }
        return effort_mapping.get(effort_str.lower(), 2.5)
    
    def _generate_comparison_summary(self, ranked_results: List[Dict]) -> str:
        """Generiert Zusammenfassung des Use Case Vergleichs"""
        if not ranked_results:
            return "Keine Use Cases zum Vergleichen verfügbar."
        
        feasible_count = len([r for r in ranked_results if r.get("feasible", False)])
        total_count = len(ranked_results)
        
        best_case = ranked_results[0]
        
        summary = f"Von {total_count} analysierten Use Cases sind {feasible_count} als machbar eingestuft. "
        
        if feasible_count > 0:
            summary += f"Der vielversprechendste Use Case ist '{best_case.get('use_case_title', 'Unbekannt')}' "
            summary += f"mit einem Aufwand von '{best_case.get('effort', 'unbekannt')}' "
            summary += f"und einer Confidence von {best_case.get('confidence', 0.0):.1%}."
        else:
            summary += "Alle Use Cases erfordern weitere Überlegungen vor der Umsetzung."
        
        return summary
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über durchgeführte Analysen zurück"""
        
        try:
            analyses_folder = self.config.analyses_folder
            analysis_files = list(analyses_folder.glob("analysis_*.json"))
            
            total_analyses = len(analysis_files)
            
            if total_analyses == 0:
                return {
                    "total_analyses": 0,
                    "average_confidence": 0.0,
                    "templates_used": {},
                    "success_rate": 0.0
                }
            
            # Lade alle Analysen für Statistiken
            confidence_scores = []
            templates_used = {}
            successful_analyses = 0
            
            for file_path in analysis_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                    
                    confidence = analysis_data.get("confidence_score", 0.0)
                    confidence_scores.append(confidence)
                    
                    template = analysis_data.get("template_used", "unknown")
                    templates_used[template] = templates_used.get(template, 0) + 1
                    
                    if confidence > 0.6:  # Erfolgreiche Analyse
                        successful_analyses += 1
                        
                except Exception:
                    continue
            
            return {
                "total_analyses": total_analyses,
                "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                "templates_used": templates_used,
                "success_rate": successful_analyses / total_analyses if total_analyses > 0 else 0.0,
                "high_confidence_count": len([s for s in confidence_scores if s >= 0.8]),
                "medium_confidence_count": len([s for s in confidence_scores if 0.6 <= s < 0.8]),
                "low_confidence_count": len([s for s in confidence_scores if s < 0.6])
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Analyse-Statistiken: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Schließt Verbindungen und räumt auf"""
        try:
            self.lm_client.close()
            self.logger.info("Analysis Engine geschlossen")
        except Exception as e:
            self.logger.error(f"Fehler beim Schließen der Analysis Engine: {e}")

# Test- und Hilfsfunktionen

def test_analysis_engine():
    """Test-Funktion für Analysis Engine"""
    
    print("🔍 Teste Analysis Engine...")
    
    # Config laden
    try:
        from utils.config import ExtendedConfig
        config = ExtendedConfig()
    except ImportError:
        print("❌ Fehler: ExtendedConfig nicht verfügbar")
        return False
    
    # Engine initialisieren
    engine = AnalysisEngine(config)
    
    # Voraussetzungen prüfen
    prereq_status = engine.check_prerequisites()
    print(f"Prerequisites: {prereq_status}")
    
    if not prereq_status["ready"]:
        print("❌ Voraussetzungen nicht erfüllt!")
        for error in prereq_status["errors"]:
            print(f"   - {error}")
        return False
    
    # Test-Daten
    company = {
        "unternehmensname": "Test Handwerk GmbH",
        "branche": "Elektroinstallation", 
        "mitarbeiter": "12",
        "hauptleistungen": "Elektroinstallationen, Smart Home Systeme"
    }
    
    use_case = {
        "beschreibung": "KI-gestützte Angebotserstellung für Elektroinstallationen",
        "problemstellung": "Angebotserstellung dauert zu lange und ist fehleranfällig",
        "zielstellung": "Schnellere und genauere Angebote durch KI-Unterstützung"
    }
    
    try:
        print("\n🤖 Führe Test-Analyse durch...")
        
        # Quick Feasibility Check
        feasibility = engine.quick_feasibility_check(company, use_case)
        print(f"✅ Feasibility Check: {feasibility.get('feasible', False)}")
        print(f"   Confidence: {feasibility.get('confidence', 0.0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        return False
    
    finally:
        engine.close()

if __name__ == "__main__":
    test_analysis_engine()

            