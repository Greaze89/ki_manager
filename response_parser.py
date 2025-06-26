"""
Response Parser - Strukturiert und validiert KI-Antworten
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from utils.logger import log_function_call

@dataclass
class ParseResult:
    """Ergebnis einer Response-Parsing Operation"""
    success: bool
    data: Dict[str, Any]
    format_detected: str
    confidence: float
    errors: List[str]
    warnings: List[str]

class ResponseParser:
    """Parser für KI-Antworten in verschiedenen Formaten"""
    
    def __init__(self):
        self.logger = logging.getLogger("ki_manager.response_parser")
        
        # JSON-Cleaning Patterns
        self.json_patterns = [
            r'```json\s*(.*?)\s*```',  # Markdown JSON blocks
            r'```\s*(.*?)\s*```',      # Generic code blocks
            r'\{.*\}',                 # JSON objects
            r'\[.*\]'                  # JSON arrays
        ]
        
        # Bekannte Feldnamen für Validierung
        self.expected_fields = {
            "structured_json": [
                "zusammenfassung", "handlungsschritte", "technische_loesungen", 
                "risiken", "chancen", "erfolgsmessung", "naechste_schritte"
            ],
            "quick_json": [
                "machbarkeit", "aufwand", "kosten", "zeitrahmen", "empfehlung"
            ],
            "roi_json": [
                "investition", "einsparungen", "roi", "empfehlung"
            ],
            "implementation_json": [
                "projektphasen", "ressourcen", "timeline", "erfolgskriterien"
            ]
        }
    
    @log_function_call
    def parse_response(self, 
                      raw_response: str, 
                      expected_format: str = "auto") -> Dict[str, Any]:
        """
        Parst KI-Response und strukturiert die Daten
        
        Args:
            raw_response: Rohe KI-Antwort
            expected_format: Erwartetes Format (auto, structured_json, quick_json, etc.)
            
        Returns:
            Strukturierte Daten als Dictionary
            
        Raises:
            ValueError: Bei kritischen Parsing-Fehlern
        """
        
        if not raw_response or not raw_response.strip():
            raise ValueError("Leere Response erhalten")
        
        self.logger.debug(f"Parse Response: {len(raw_response)} Zeichen, Format: {expected_format}")
        
        # Auto-Detect wenn kein Format vorgegeben
        if expected_format == "auto":
            expected_format = self._detect_format(raw_response)
        
        # Verschiedene Parsing-Strategien versuchen
        parse_strategies = [
            self._parse_clean_json,
            self._parse_markdown_json,
            self._parse_mixed_content,
            self._parse_fallback_text
        ]
        
        errors = []
        best_result = None
        
        for strategy in parse_strategies:
            try:
                result = strategy(raw_response, expected_format)
                
                if result.success:
                    self.logger.debug(f"Erfolgreich geparst mit {strategy.__name__}")
                    return result.data
                else:
                    errors.extend(result.errors)
                    
                    # Beste Partial-Result merken
                    if best_result is None or result.confidence > best_result.confidence:
                        best_result = result
                        
            except Exception as e:
                self.logger.warning(f"Parsing-Strategie {strategy.__name__} fehlgeschlagen: {e}")
                errors.append(f"{strategy.__name__}: {e}")
        
        # Wenn nichts funktioniert hat, beste verfügbare Result nehmen
        if best_result and best_result.data:
            self.logger.warning(f"Partial parsing mit Confidence {best_result.confidence:.2f}")
            return best_result.data
        
        # Als letzter Ausweg: Text-Fallback
        return self._create_text_fallback(raw_response, errors)
    
    def _detect_format(self, response: str) -> str:
        """Erkennt automatisch das Format der Response"""
        
        response_lower = response.lower()
        
        # JSON-Format erkennen
        if any(pattern in response for pattern in ['{', '}', '[', ']']):
            if 'projektphasen' in response_lower:
                return "implementation_json"
            elif 'machbarkeit' in response_lower:
                return "quick_json"  
            elif 'investition' in response_lower or 'roi' in response_lower:
                return "roi_json"
            else:
                return "structured_json"
        
        # Text-Format
        return "text"
    
    def _parse_clean_json(self, response: str, expected_format: str) -> ParseResult:
        """Versucht direktes JSON-Parsing"""
        
        try:
            # Entferne führende/nachfolgende Whitespace
            cleaned = response.strip()
            
            # Versuche direktes JSON-Parsing
            data = json.loads(cleaned)
            
            # Validiere Struktur
            validation = self._validate_structure(data, expected_format)
            
            return ParseResult(
                success=validation["valid"],
                data=data,
                format_detected="clean_json",
                confidence=validation["confidence"],
                errors=validation["errors"],
                warnings=validation["warnings"]
            )
            
        except json.JSONDecodeError as e:
            return ParseResult(
                success=False,
                data={},
                format_detected="none",
                confidence=0.0,
                errors=[f"JSON Decode Error: {e}"],
                warnings=[]
            )
    
    def _parse_markdown_json(self, response: str, expected_format: str) -> ParseResult:
        """Extrahiert JSON aus Markdown-Code-Blöcken"""
        
        for pattern in self.json_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
                    # Bereinige extrahierten JSON
                    cleaned_json = self._clean_json_string(match)
                    data = json.loads(cleaned_json)
                    
                    validation = self._validate_structure(data, expected_format)
                    
                    if validation["valid"] or validation["confidence"] > 0.5:
                        return ParseResult(
                            success=validation["valid"],
                            data=data,
                            format_detected="markdown_json",
                            confidence=validation["confidence"],
                            errors=validation["errors"],
                            warnings=validation["warnings"]
                        )
                        
                except json.JSONDecodeError:
                    continue
        
        return ParseResult(
            success=False,
            data={},
            format_detected="none", 
            confidence=0.0,
            errors=["Kein valides JSON in Markdown gefunden"],
            warnings=[]
        )
    
    def _parse_mixed_content(self, response: str, expected_format: str) -> ParseResult:
        """Parst gemischten Content (Text + strukturierte Daten)"""
        
        # Suche nach JSON-ähnlichen Strukturen im Text
        json_candidates = []
        
        # Finde potentielle JSON-Objekte
        brace_start = -1
        brace_count = 0
        
        for i, char in enumerate(response):
            if char == '{':
                if brace_count == 0:
                    brace_start = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and brace_start != -1:
                    json_candidate = response[brace_start:i+1]
                    json_candidates.append(json_candidate)
                    brace_start = -1
        
        # Versuche jeden Kandidaten zu parsen
        best_result = None
        
        for candidate in json_candidates:
            try:
                cleaned = self._clean_json_string(candidate)
                data = json.loads(cleaned)
                
                validation = self._validate_structure(data, expected_format)
                
                if not best_result or validation["confidence"] > best_result.confidence:
                    best_result = ParseResult(
                        success=validation["valid"],
                        data=data,
                        format_detected="mixed_content",
                        confidence=validation["confidence"],
                        errors=validation["errors"],
                        warnings=validation["warnings"]
                    )
                    
            except json.JSONDecodeError:
                continue
        
        if best_result:
            return best_result
        
        # Fallback: Versuche strukturierte Text-Extraktion
        return self._extract_structured_text(response, expected_format)
    
    def _parse_fallback_text(self, response: str, expected_format: str) -> ParseResult:
        """Fallback-Parser für unstrukturierten Text"""
        
        # Extrahiere Informationen aus Freitext
        extracted_data = {}
        confidence = 0.3  # Niedrige Confidence für Freitext
        
        # Suche nach Schlüsselwörtern und Mustern
        if expected_format == "quick_json":
            extracted_data = self._extract_feasibility_from_text(response)
        elif expected_format == "structured_json":
            extracted_data = self._extract_analysis_from_text(response)
        else:
            # Allgemeine Text-Extraktion
            extracted_data = {
                "zusammenfassung": self._extract_summary(response),
                "empfehlungen": self._extract_recommendations(response)
            }
        
        return ParseResult(
            success=bool(extracted_data),
            data=extracted_data,
            format_detected="fallback_text",
            confidence=confidence,
            errors=[],
            warnings=["Fallback Text-Parsing verwendet - Struktur möglicherweise unvollständig"]
        )
    
    def _clean_json_string(self, json_str: str) -> str:
        """Bereinigt JSON-String von häufigen Problemen"""
        
        # Entferne führende/nachfolgende Whitespace
        cleaned = json_str.strip()
        
        # Entferne Markdown-Syntax
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Ersetze häufige Probleme
        replacements = [
            (r'(\w+):', r'"\1":'),  # Unquoted keys
            (r':\s*([^"\[\{\d\-][^,\}\]]*)', r': "\1"'),  # Unquoted string values
            (r',\s*}', '}'),  # Trailing commas
            (r',\s*]', ']'),  # Trailing commas in arrays
        ]
        
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned
    
    def _validate_structure(self, data: Dict, expected_format: str) -> Dict[str, Any]:
        """Validiert die Struktur der geparsten Daten"""
        
        if not isinstance(data, dict):
            return {
                "valid": False,
                "confidence": 0.0,
                "errors": ["Response ist kein Dictionary"],
                "warnings": []
            }
        
        expected_fields = self.expected_fields.get(expected_format, [])
        errors = []
        warnings = []
        
        if expected_fields:
            present_fields = [field for field in expected_fields if field in data]
            missing_fields = [field for field in expected_fields if field not in data]
            
            confidence = len(present_fields) / len(expected_fields)
            
            if missing_fields:
                if len(missing_fields) == len(expected_fields):
                    errors.append(f"Keine erwarteten Felder gefunden: {missing_fields}")
                else:
                    warnings.append(f"Fehlende Felder: {missing_fields}")
            
            # Zusätzliche Validierung je nach Format
            if expected_format == "structured_json":
                confidence *= self._validate_analysis_structure(data)
            elif expected_format == "quick_json":
                confidence *= self._validate_feasibility_structure(data)
            
        else:
            # Fallback: Prüfe ob vernünftige Daten vorhanden
            confidence = 0.7 if data else 0.0
        
        is_valid = confidence > 0.5 and not errors
        
        return {
            "valid": is_valid,
            "confidence": confidence,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_analysis_structure(self, data: Dict) -> float:
        """Spezielle Validierung für Analyse-Struktur"""
        
        quality_score = 1.0
        
        # Prüfe Handlungsschritte
        steps = data.get("handlungsschritte", [])
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    quality_score *= 0.8
                    continue
                
                required_step_fields = ["titel", "beschreibung", "prioritaet"]
                present_step_fields = [f for f in required_step_fields if f in step]
                quality_score *= len(present_step_fields) / len(required_step_fields)
        
        # Prüfe technische Lösungen
        solutions = data.get("technische_loesungen", [])
        if isinstance(solutions, list) and solutions:
            quality_score *= 1.1  # Bonus für vorhandene Lösungen
        
        return min(quality_score, 1.0)
    
    def _validate_feasibility_structure(self, data: Dict) -> float:
        """Spezielle Validierung für Machbarkeits-Struktur"""
        
        quality_score = 1.0
        
        # Prüfe Machbarkeits-Bewertung
        feasibility = data.get("machbarkeit", "").lower()
        valid_feasibility = ["sehr gut", "gut", "mittel", "schwierig", "unrealistisch"]
        if feasibility not in valid_feasibility:
            quality_score *= 0.7
        
        # Prüfe Empfehlung
        recommendation = data.get("empfehlung", "").lower()
        valid_recommendations = ["go", "no-go", "überdenken"]
        if recommendation not in valid_recommendations:
            quality_score *= 0.8
        
        return quality_score
    
    def _extract_structured_text(self, response: str, expected_format: str) -> ParseResult:
        """Extrahiert strukturierte Informationen aus Freitext"""
        
        extracted_data = {}
        confidence = 0.4
        
        # Suche nach Abschnitts-Überschriften
        sections = self._find_text_sections(response)
        
        for section_title, section_content in sections.items():
            # Mappe Abschnitte zu Datenfeldern
            mapped_field = self._map_section_to_field(section_title, expected_format)
            if mapped_field:
                extracted_data[mapped_field] = section_content.strip()
                confidence += 0.1
        
        # Extrahiere Listen und Aufzählungen
        lists = self._extract_lists_from_text(response)
        if lists:
            if expected_format == "structured_json":
                extracted_data["handlungsschritte"] = lists.get("schritte", [])
                extracted_data["naechste_schritte"] = lists.get("empfehlungen", [])
            confidence += 0.2
        
        return ParseResult(
            success=bool(extracted_data),
            data=extracted_data,
            format_detected="structured_text",
            confidence=min(confidence, 1.0),
            errors=[],
            warnings=["Strukturierte Text-Extraktion - möglicherweise unvollständig"]
        )
    
    def _find_text_sections(self, text: str) -> Dict[str, str]:
        """Findet Abschnitte in Freitext basierend auf Überschriften"""
        
        sections = {}
        
        # Patterns für Überschriften
        heading_patterns = [
            r'^\*\*([^*]+)\*\*:?\s*$',  # **Überschrift**
            r'^#+\s*([^#\n]+)$',        # # Überschrift
            r'^([A-ZÄÖÜ][^:\n]*):$',    # Überschrift:
        ]
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Prüfe ob Zeile eine Überschrift ist
            is_heading = False
            for pattern in heading_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    # Speichere vorherigen Abschnitt
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Starte neuen Abschnitt
                    current_section = match.group(1).strip()
                    current_content = []
                    is_heading = True
                    break
            
            if not is_heading and current_section:
                current_content.append(line)
        
        # Letzten Abschnitt speichern
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _map_section_to_field(self, section_title: str, expected_format: str) -> Optional[str]:
        """Mappt Abschnitts-Titel zu Datenfeldern"""
        
        title_lower = section_title.lower()
        
        # Mapping für verschiedene Formate
        mappings = {
            "structured_json": {
                "zusammenfassung": ["zusammenfassung", "summary", "einschätzung"],
                "handlungsschritte": ["handlungsschritte", "schritte", "maßnahmen", "actions"],
                "technische_loesungen": ["technische", "lösungen", "solutions", "tools"],
                "risiken": ["risiken", "risks", "gefahren"],
                "chancen": ["chancen", "opportunities", "vorteile"],
                "naechste_schritte": ["nächste", "next steps", "empfehlungen"]
            },
            "quick_json": {
                "machbarkeit": ["machbarkeit", "feasibility"],
                "aufwand": ["aufwand", "effort"],
                "empfehlung": ["empfehlung", "recommendation"]
            }
        }
        
        format_mapping = mappings.get(expected_format, {})
        
        for field, keywords in format_mapping.items():
            if any(keyword in title_lower for keyword in keywords):
                return field
        
        return None
    
    def _extract_lists_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extrahiert Listen und Aufzählungen aus Text"""
        
        lists = {"schritte": [], "empfehlungen": [], "allgemein": []}
        
        # Patterns für Listen-Items
        list_patterns = [
            r'^\s*[-*•]\s*(.+)$',  # - Item oder * Item
            r'^\s*\d+\.\s*(.+)$',  # 1. Item
            r'^\s*[a-z]\)\s*(.+)$' # a) Item
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            for pattern in list_patterns:
                match = re.match(pattern, line)
                if match:
                    item = match.group(1).strip()
                    
                    # Kategorisiere basierend auf Schlüsselwörtern
                    item_lower = item.lower()
                    
                    if any(word in item_lower for word in ["schritt", "maßnahme", "aktion"]):
                        lists["schritte"].append(item)
                    elif any(word in item_lower for word in ["empfehlung", "sollte", "muss"]):
                        lists["empfehlungen"].append(item)
                    else:
                        lists["allgemein"].append(item)
                    
                    break
        
        return lists
    
    def _extract_feasibility_from_text(self, text: str) -> Dict[str, Any]:
        """Extrahiert Machbarkeits-Informationen aus Freitext"""
        
        text_lower = text.lower()
        
        # Machbarkeit erkennen
        feasibility = "mittel"
        if any(word in text_lower for word in ["sehr gut", "excellent", "einfach"]):
            feasibility = "sehr gut"
        elif any(word in text_lower for word in ["gut", "machbar", "realistisch"]):
            feasibility = "gut"
        elif any(word in text_lower for word in ["schwierig", "herausfordernd", "komplex"]):
            feasibility = "schwierig"
        elif any(word in text_lower for word in ["unrealistisch", "unmöglich", "nicht machbar"]):
            feasibility = "unrealistisch"
        
        # Aufwand erkennen
        effort = "mittel"
        if any(word in text_lower for word in ["geringer aufwand", "wenig aufwand", "einfach"]):
            effort = "gering"
        elif any(word in text_lower for word in ["hoher aufwand", "sehr aufwendig", "kompliziert"]):
            effort = "hoch"
        
        # Empfehlung ableiten
        recommendation = "überdenken"
        if "empfehlung" in text_lower and "ja" in text_lower:
            recommendation = "go"
        elif any(word in text_lower for word in ["nicht empfohlen", "nein", "stoppen"]):
            recommendation = "no-go"
        elif feasibility in ["sehr gut", "gut"] and effort in ["gering", "mittel"]:
            recommendation = "go"
        
        return {
            "machbarkeit": feasibility,
            "aufwand": effort,
            "empfehlung": recommendation,
            "begruendung": "Aus Freitext extrahiert"
        }
    
    def _extract_analysis_from_text(self, text: str) -> Dict[str, Any]:
        """Extrahiert Analyse-Informationen aus Freitext"""
        
        # Extrahiere Zusammenfassung (erster Absatz)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        summary = paragraphs[0] if paragraphs else "Keine Zusammenfassung verfügbar"
        
        # Extrahiere Listen
        lists = self._extract_lists_from_text(text)
        
        return {
            "zusammenfassung": summary,
            "handlungsschritte": [{"titel": item, "beschreibung": item} for item in lists["schritte"]],
            "naechste_schritte": lists["empfehlungen"] or lists["allgemein"]
        }
    
    def _extract_summary(self, text: str) -> str:
        """Extrahiert eine Zusammenfassung aus Text"""
        
        # Erster Absatz als Zusammenfassung
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if paragraphs:
            summary = paragraphs[0]
            # Kürze wenn zu lang
            if len(summary) > 300:
                summary = summary[:297] + "..."
            return summary
        
        return "Keine Zusammenfassung verfügbar"
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extrahiert Empfehlungen aus Text"""
        
        recommendations = []
        
        # Suche nach Empfehlungs-Schlüsselwörtern
        recommendation_markers = [
            "empfehlung", "sollte", "muss", "wichtig", "nächster schritt"
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(marker in line.lower() for marker in recommendation_markers):
                recommendations.append(line)
        
        return recommendations
    
    def _create_text_fallback(self, response: str, errors: List[str]) -> Dict[str, Any]:
        """Erstellt Fallback-Struktur wenn alle Parsing-Versuche fehlschlagen"""
        
        return {
            "zusammenfassung": "Parsing fehlgeschlagen - Originaltext verfügbar",
            "raw_response": response,
            "parsing_errors": errors,
            "naechste_schritte": [
                "Response manuell prüfen",
                "Prompt-Template überarbeiten",
                "KI-Modell-Parameter anpassen"
            ]
        }
    
    def validate_parsed_data(self, data: Dict[str, Any], expected_format: str) -> Dict[str, Any]:
        """Öffentliche Methode zur Validierung von geparsten Daten"""
        return self._validate_structure(data, expected_format)
    
    def clean_json_response(self, response: str) -> str:
        """Öffentliche Methode zum Bereinigen von JSON-Responses"""
        return self._clean_json_string(response)

# Test-Funktionen

def test_response_parser():
    """Test für Response Parser"""
    
    parser = ResponseParser()
    
    # Test-Responses
    test_cases = [
        {
            "name": "Clean JSON",
            "response": '{"machbarkeit": "gut", "aufwand": "mittel", "empfehlung": "go"}',
            "expected_format": "quick_json"
        },
        {
            "name": "Markdown JSON",
            "response": '''Hier ist die Analyse:
            
```json
{
    "zusammenfassung": "Test-Analyse",
    "handlungsschritte": [
        {"titel": "Schritt 1", "prioritaet": "hoch"}
    ]
}
```

Das war die Analyse.''',
            "expected_format": "structured_json"
        },
        {
            "name": "Mixed Content",
            "response": '''Die Analyse zeigt:

**Zusammenfassung:** Das ist eine Test-Analyse für die Parser-Funktionalität.

**Nächste Schritte:**
- Implementierung starten
- Team schulen
- Tests durchführen

Die Umsetzung sollte in 3 Monaten möglich sein.''',
            "expected_format": "structured_json"
        }
    ]
    
    print("🔍 Teste Response Parser...")
    
    for test_case in test_cases:
        print(f"\n--- Test: {test_case['name']} ---")
        
        try:
            result = parser.parse_response(
                test_case["response"], 
                test_case["expected_format"]
            )
            
            print(f"✅ Parsing erfolgreich")
            print(f"   Felder: {list(result.keys())}")
            
            if "zusammenfassung" in result:
                print(f"   Zusammenfassung: {result['zusammenfassung'][:50]}...")
            
        except Exception as e:
            print(f"❌ Parsing fehlgeschlagen: {e}")
    
    print("\n✅ Response Parser Tests abgeschlossen")

if __name__ == "__main__":
    test_response_parser()