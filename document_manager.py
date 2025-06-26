"""
Dokumentenverwaltung für KI Manager
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from utils.config import Config, UseCase, CompanyProfile, ExtendedConfig
from data.pdf_generator import PDFGenerator
from utils.logger import log_function_call, log_performance

class DocumentManager:
    """Zentrale Dokumentenverwaltung"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("ki_manager")
        self.pdf_generator = PDFGenerator(config)
        
        # Dokumentenordner sicherstellen
        self.docs_folder = Path(config.app_config.docs_folder)
        self.docs_folder.mkdir(exist_ok=True)
        
        self.logger.info(f"DocumentManager initialisiert mit Ordner: {self.docs_folder}")
    
    @log_function_call
    def get_document_list(self) -> List[Dict[str, Union[str, datetime]]]:
        """
        Gibt Liste aller Dokumente zurück
        
        Returns:
            Liste mit Dokumenten-Metadaten
        """
        documents = []
        
        try:
            for pdf_file in sorted(self.docs_folder.glob("*.pdf")):
                json_file = pdf_file.with_suffix('.json')
                
                doc_info = {
                    'filename': pdf_file.name,
                    'pdf_path': pdf_file,
                    'json_path': json_file if json_file.exists() else None,
                    'modified': datetime.fromtimestamp(pdf_file.stat().st_mtime),
                    'size': pdf_file.stat().st_size,
                    'type': self._determine_document_type(pdf_file.name)
                }
                
                # Zusätzliche Metadaten aus JSON laden
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                            doc_info.update({
                                'title': self._extract_title(json_data),
                                'created': datetime.fromisoformat(json_data.get('created', '1970-01-01')),
                                'version': json_data.get('version', '1.0')
                            })
                    except Exception as e:
                        self.logger.warning(f"Metadaten für {pdf_file.name} konnten nicht geladen werden: {e}")
                
                documents.append(doc_info)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Dokumentenliste: {e}")
        
        return documents
    
    def _determine_document_type(self, filename: str) -> str:
        """Bestimmt Dokumenttyp anhand des Dateinamens"""
        if "UseCase" in filename:
            return "use_case"
        elif "Steckbrief" in filename:
            return "company_profile"
        else:
            return "unknown"
    
    def _extract_title(self, data: dict) -> str:
        """Extrahiert Titel aus Dokumentdaten"""
        if data.get('type') == 'use_case':
            return data.get('beschreibung', 'Unbenannter Use Case')[:50] + "..."
        elif data.get('type') == 'company_profile':
            return data.get('unternehmensname', 'Unbenanntes Unternehmen')
        return "Unbekanntes Dokument"
    
    @log_performance
    def load_document(self, file_path: Path) -> dict:
        """
        Lädt ein Dokument
        
        Args:
            file_path: Pfad zur PDF- oder JSON-Datei
            
        Returns:
            Dokumentdaten als Dictionary
            
        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            json.JSONDecodeError: Wenn JSON ungültig
        """
        # JSON-Datei bestimmen
        if file_path.suffix == '.pdf':
            json_file = file_path.with_suffix('.json')
        else:
            json_file = file_path
            
        if not json_file.exists():
            raise FileNotFoundError(f"JSON-Datei nicht gefunden: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.logger.info(f"Dokument geladen: {json_file}")
        return data
    
    @log_performance
    def save_document(self, document_type: str, data: dict) -> Path:
        """
        Speichert ein Dokument
        
        Args:
            document_type: 'use_case' oder 'company_profile'
            data: Dokumentdaten
            
        Returns:
            Pfad zur gespeicherten PDF-Datei
            
        Raises:
            ValueError: Bei ungültigem Dokumenttyp
        """
        if document_type not in ['use_case', 'company_profile']:
            raise ValueError(f"Ungültiger Dokumenttyp: {document_type}")
        
        # Zeitstempel hinzufügen
        now = datetime.now()
        data['created'] = data.get('created', now.isoformat())
        data['modified'] = now.isoformat()
        data['type'] = document_type
        
        # Dateiname generieren
        filename = self._generate_filename(document_type, data)
        pdf_path = self.docs_folder / f"{filename}.pdf"
        json_path = self.docs_folder / f"{filename}.json"
        
        # JSON speichern
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # PDF generieren
        if document_type == 'use_case':
            self.pdf_generator.create_use_case_pdf(data, pdf_path)
        elif document_type == 'company_profile':
            self.pdf_generator.create_company_profile_pdf(data, pdf_path)
        
        self.logger.info(f"Dokument gespeichert: {pdf_path}")
        return pdf_path
    
    def _generate_filename(self, document_type: str, data: dict) -> str:
        """Generiert Dateiname basierend auf Typ und Inhalt"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if document_type == 'use_case':
            name = data.get('verantwortlich', 'Unbekannt')
            prefix = "UseCase"
        elif document_type == 'company_profile':
            name = data.get('unternehmensname', 'Unbekannt')
            prefix = "Steckbrief"
        else:
            name = "Unbekannt"
            prefix = "Dokument"
        
        # Ungültige Zeichen entfernen
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        return f"{prefix}_{safe_name}_{timestamp}"
    
    @log_function_call
    def delete_document(self, file_path: Path) -> bool:
        """
        Löscht ein Dokument (PDF und JSON)
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            True wenn erfolgreich
        """
        try:
            pdf_file = file_path.with_suffix('.pdf')
            json_file = file_path.with_suffix('.json')
            
            deleted_files = []
            
            if pdf_file.exists():
                pdf_file.unlink()
                deleted_files.append(pdf_file.name)
            
            if json_file.exists():
                json_file.unlink()
                deleted_files.append(json_file.name)
            
            if deleted_files:
                self.logger.info(f"Dateien gelöscht: {', '.join(deleted_files)}")
                return True
            else:
                self.logger.warning(f"Keine Dateien zum Löschen gefunden: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen: {e}")
            return False
    
    @log_function_call
    def duplicate_document(self, file_path: Path) -> Optional[Path]:
        """
        Dupliziert ein Dokument
        
        Args:
            file_path: Pfad zum Original
            
        Returns:
            Pfad zum duplizierten Dokument oder None
        """
        try:
            # Original laden
            data = self.load_document(file_path)
            
            # Als Kopie markieren
            if 'beschreibung' in data:
                data['beschreibung'] = f"[KOPIE] {data['beschreibung']}"
            elif 'unternehmensname' in data:
                data['unternehmensname'] = f"[KOPIE] {data['unternehmensname']}"
            
            # Zeitstempel zurücksetzen
            data.pop('created', None)
            data.pop('modified', None)
            
            # Speichern
            return self.save_document(data['type'], data)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Duplizieren: {e}")
            return None
    
    def search_documents(self, query: str) -> List[Dict]:
        """
        Durchsucht Dokumente nach Text
        
        Args:
            query: Suchbegriff
            
        Returns:
            Liste gefundener Dokumente
        """
        results = []
        query_lower = query.lower()
        
        for doc_info in self.get_document_list():
            if doc_info['json_path']:
                try:
                    data = self.load_document(doc_info['json_path'])
                    
                    # In verschiedenen Feldern suchen
                    searchable_text = ""
                    if data.get('type') == 'use_case':
                        searchable_text = " ".join([
                            data.get('verantwortlich', ''),
                            data.get('bereich', ''),
                            data.get('beschreibung', ''),
                            data.get('problemstellung', ''),
                            data.get('zielstellung', '')
                        ])
                    elif data.get('type') == 'company_profile':
                        searchable_text = " ".join([
                            data.get('unternehmensname', ''),
                            data.get('branche', ''),
                            data.get('hauptleistungen', ''),
                            data.get('kontaktperson', '')
                        ])
                    
                    if query_lower in searchable_text.lower():
                        results.append(doc_info)
                        
                except Exception as e:
                    self.logger.warning(f"Fehler beim Durchsuchen von {doc_info['filename']}: {e}")
        
        return results
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Gibt Statistiken über die Dokumente zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        documents = self.get_document_list()
        
        stats = {
            'total_documents': len(documents),
            'use_cases': len([d for d in documents if d['type'] == 'use_case']),
            'company_profiles': len([d for d in documents if d['type'] == 'company_profile']),
            'unknown_types': len([d for d in documents if d['type'] == 'unknown']),
            'total_size_mb': sum(d['size'] for d in documents) / (1024 * 1024)
        }
        
        return stats
    
    def backup_documents(self, backup_path: Path) -> bool:
        """
        Erstellt Backup aller Dokumente
        
        Args:
            backup_path: Ziel-Verzeichnis
            
        Returns:
            True wenn erfolgreich
        """
        try:
            import shutil
            
            backup_path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = backup_path / f"ki_manager_backup_{timestamp}"
            
            shutil.copytree(self.docs_folder, backup_folder)
            
            self.logger.info(f"Backup erstellt: {backup_folder}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup fehlgeschlagen: {e}")
            return False