"""
Hauptfenster der KI Manager Anwendung
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path

from gui.sidebar import Sidebar
from gui.workspace import Workspace
from gui.pdf_viewer import PDFViewerWidget
from data.document_manager import DocumentManager
from utils.logger import log_function_call, log_performance

class MainWindow:
    """Hauptfenster der Anwendung"""
    
    def __init__(self, root: tk.Tk, config):
        self.root = root
        self.config = config
        self.logger = logging.getLogger("ki_manager")
        
        # Document Manager
        self.document_manager = DocumentManager(config)
        
        # UI-Komponenten
        self.sidebar = None
        self.workspace = None
        self.pdf_viewer = None
        
        self.setup_window()
        self.setup_ui()
        self.setup_bindings()
        
        self.logger.info("Hauptfenster initialisiert")
    
    @log_function_call
    def setup_window(self):
        """Konfiguriert das Hauptfenster"""
        self.root.title(self.config.app_config.window_title)
        self.root.geometry(f"{self.config.app_config.window_width}x{self.config.app_config.window_height}")
        self.root.configure(bg='#f0f0f0')
        
        # Icon setzen (falls vorhanden)
        icon_path = Path("assets/icon.ico")
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception as e:
                self.logger.warning(f"Icon konnte nicht geladen werden: {e}")
    
    @log_function_call
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        # Hauptframe
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Sidebar (feste Breite)
        sidebar_frame = ttk.LabelFrame(main_frame, text="Navigation", padding=10)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Sidebar feste Breite setzen
        sidebar_frame.pack_propagate(False)
        sidebar_frame.configure(width=280)
        
        self.sidebar = Sidebar(
            sidebar_frame, 
            self.config, 
            self.document_manager,
            self
        )
        
        # Rechte Seite: Container für Workspace und PDF-Viewer
        right_container = ttk.Frame(main_frame)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Workspace (optimale Breite für Formulare - nicht expandierend)
        workspace_frame = ttk.LabelFrame(right_container, text="Arbeitsbereich", padding=5)
        workspace_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Workspace feste optimale Breite für Formulare
        workspace_frame.pack_propagate(False)
        workspace_frame.configure(width=750)  # Vergrößert von 700 auf 800px
        
        self.workspace = Workspace(
            workspace_frame,
            self.config,
            self.document_manager,
            self
        )
        
        # PDF Viewer (nimmt den gesamten restlichen Platz ein)
        pdf_frame = ttk.LabelFrame(right_container, text="PDF-Vorschau", padding=3)
        pdf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.pdf_viewer = PDFViewerWidget(pdf_frame)
        
        # Initial Willkommensseite anzeigen
        self.workspace.show_welcome()
    
    def setup_bindings(self):
        """Richtet Event-Bindings ein"""
        # Window Close Handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Keyboard Shortcuts
        self.root.bind('<Control-n>', lambda e: self.sidebar.new_use_case())
        self.root.bind('<Control-o>', lambda e: self.sidebar.open_document())
        self.root.bind('<Control-s>', lambda e: self.workspace.save_current_document())
        self.root.bind('<F5>', lambda e: self.sidebar.refresh_documents())
    
    @log_function_call
    def on_closing(self):
        """Handler für Fenster schließen"""
        # Überprüfe ob ungespeicherte Änderungen vorhanden
        if self.workspace.has_unsaved_changes():
            response = messagebox.askyesnocancel(
                "Änderungen speichern?",
                "Es gibt ungespeicherte Änderungen. Möchten Sie diese vor dem Beenden speichern?"
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes - Save
                if not self.workspace.save_current_document():
                    return  # Save failed
        
        # Konfiguration speichern
        try:
            self.config.save_config()
            self.logger.info("Konfiguration gespeichert")
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
        
        # Anwendung beenden
        self.root.quit()
        self.root.destroy()
    
    # Callback-Methoden für Komponenten-Kommunikation
    
    def show_pdf(self, pdf_path: Path):
        """Zeigt PDF in Viewer an"""
        if pdf_path and pdf_path.exists():
            self.pdf_viewer.load_pdf(str(pdf_path))
    
    def refresh_document_list(self):
        """Aktualisiert Dokumentenliste"""
        self.sidebar.refresh_documents()
    
    def show_use_case_form(self, data=None):
        """Zeigt Use Case Formular"""
        self.workspace.show_use_case_form(data)
    
    def show_company_profile_form(self, data=None):
        """Zeigt Company Profile Formular"""
        self.workspace.show_company_profile_form(data)
    
    def show_document_list(self):
        """Zeigt Dokumentenliste"""
        self.workspace.show_document_list()
    
    @log_performance
    def load_document(self, file_path: Path):
        """Lädt ein Dokument"""
        try:
            document = self.document_manager.load_document(file_path)
            
            if document.get('type') == 'use_case':
                self.show_use_case_form(document)
            elif document.get('type') == 'company_profile':
                self.show_company_profile_form(document)
            else:
                messagebox.showerror("Fehler", "Unbekannter Dokumenttyp")
                return
            
            # PDF automatisch laden falls vorhanden
            pdf_path = file_path.with_suffix('.pdf')
            if pdf_path.exists():
                self.show_pdf(pdf_path)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Dokuments: {e}")
            messagebox.showerror("Fehler", f"Dokument konnte nicht geladen werden:\n{e}")
    
    @log_performance
    def save_document(self, document_type: str, data: dict):
        """Speichert ein Dokument"""
        try:
            file_path = self.document_manager.save_document(document_type, data)
            
            # PDF automatisch anzeigen
            pdf_path = file_path.with_suffix('.pdf')
            if pdf_path.exists():
                self.show_pdf(pdf_path)
            
            # Dokumentenliste aktualisieren
            self.refresh_document_list()
            
            messagebox.showinfo("Erfolg", f"Dokument wurde gespeichert:\n{file_path.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern: {e}")
            messagebox.showerror("Fehler", f"Dokument konnte nicht gespeichert werden:\n{e}")
            return False