"""
Sidebar-Komponente für Navigation und Dokumentenverwaltung
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import subprocess
import sys
from pathlib import Path

from utils.logger import log_function_call

class Sidebar:
    """Sidebar für Navigation und Dokumentenverwaltung"""
    
    def __init__(self, parent, config, document_manager, main_window):
        self.parent = parent
        self.config = config
        self.document_manager = document_manager
        self.main_window = main_window
        self.logger = logging.getLogger("ki_manager")
        
        self.setup_ui()
        self.refresh_documents()
    
    @log_function_call
    def setup_ui(self):
        """Erstellt die Sidebar-Oberfläche"""
        # Hauptfunktionen
        functions_frame = ttk.LabelFrame(self.parent, text="Dokumente erstellen", padding=5)
        functions_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(functions_frame, text="Neuer KI Use Case", 
                  command=self.new_use_case, width=25).pack(pady=2)
        ttk.Button(functions_frame, text="Neuer Steckbrief", 
                  command=self.new_company_profile, width=25).pack(pady=2)
        
        ttk.Separator(functions_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        ttk.Button(functions_frame, text="Dokument öffnen", 
                  command=self.open_document, width=25).pack(pady=2)
        
        # Dokumentenverwaltung
        management_frame = ttk.LabelFrame(self.parent, text="Verwaltung", padding=5)
        management_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(management_frame, text="Ordner öffnen", 
                  command=self.open_docs_folder, width=25).pack(pady=2)
        ttk.Button(management_frame, text="Aktualisieren", 
                  command=self.refresh_documents, width=25).pack(pady=2)
        
        # Dokumentenliste
        docs_frame = ttk.LabelFrame(self.parent, text="Vorhandene Dokumente", padding=5)
        docs_frame.pack(fill=tk.BOTH, expand=True)
        
        # Suchfeld
        search_frame = ttk.Frame(docs_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Suchen:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Listbox mit Scrollbar
        list_frame = ttk.Frame(docs_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.docs_listbox = tk.Listbox(list_frame, height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.docs_listbox.yview)
        self.docs_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.docs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Event Bindings
        self.docs_listbox.bind('<Double-1>', self.on_document_double_click)
        self.docs_listbox.bind('<Button-3>', self.show_context_menu)  # Rechtsklick
        
        # Dokumentinfo-Label
        self.info_var = tk.StringVar(value="Keine Dokumente")
        info_label = ttk.Label(docs_frame, textvariable=self.info_var, font=('Arial', 8))
        info_label.pack(pady=(5, 0))
    
    def on_search(self, event=None):
        """Filtert Dokumentenliste basierend auf Suchbegriff"""
        query = self.search_var.get().strip()
        
        if not query:
            self.refresh_documents()
            return
        
        # Suche durchführen
        results = self.document_manager.search_documents(query)
        
        # Liste aktualisieren
        self.docs_listbox.delete(0, tk.END)
        
        for doc in results:
            display_name = self._format_document_name(doc)
            self.docs_listbox.insert(tk.END, display_name)
        
        self.update_info_label(f"Gefunden: {len(results)}")
    
    def _format_document_name(self, doc_info: dict) -> str:
        """Formatiert Dokumentname für Anzeige"""
        filename = doc_info['filename']
        doc_type = "UC" if doc_info['type'] == 'use_case' else "SP"
        modified = doc_info['modified'].strftime('%d.%m.%Y')
        
        return f"[{doc_type}] {filename} ({modified})"
    
    @log_function_call
    def refresh_documents(self):
        """Aktualisiert die Dokumentenliste"""
        try:
            documents = self.document_manager.get_document_list()
            
            self.docs_listbox.delete(0, tk.END)
            self.document_list = documents  # Für späteren Zugriff speichern
            
            for doc in documents:
                display_name = self._format_document_name(doc)
                self.docs_listbox.insert(tk.END, display_name)
            
            # Statistiken aktualisieren
            stats = self.document_manager.get_statistics()
            info_text = f"Gesamt: {stats['total_documents']} | UC: {stats['use_cases']} | SP: {stats['company_profiles']}"
            self.update_info_label(info_text)
            
            self.logger.debug(f"Dokumentenliste aktualisiert: {len(documents)} Dokumente")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Dokumentenliste: {e}")
            messagebox.showerror("Fehler", f"Dokumentenliste konnte nicht aktualisiert werden:\n{e}")
    
    def update_info_label(self, text: str):
        """Aktualisiert Info-Label"""
        self.info_var.set(text)
    
    # Event Handler
    def new_use_case(self):
        """Erstellt neuen Use Case"""
        self.main_window.show_use_case_form()
    
    def new_company_profile(self):
        """Erstellt neuen Unternehmenssteckbrief"""
        self.main_window.show_company_profile_form()
    
    def open_document(self):
        """Öffnet Dokument-Dialog"""
        filetypes = [
            ("JSON files", "*.json"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Dokument öffnen",
            initialdir=self.document_manager.docs_folder,
            filetypes=filetypes
        )
        
        if filename:
            self.main_window.load_document(Path(filename))
    
    def open_docs_folder(self):
        """Öffnet Dokumentenordner im Dateiexplorer"""
        try:
            folder_path = self.document_manager.docs_folder
            
            if sys.platform == "win32":
                subprocess.run(['explorer', str(folder_path)])
            elif sys.platform == "darwin":
                subprocess.run(['open', str(folder_path)])
            else:
                subprocess.run(['xdg-open', str(folder_path)])
                
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Ordners: {e}")
            messagebox.showerror("Fehler", f"Ordner konnte nicht geöffnet werden:\n{e}")
    
    def on_document_double_click(self, event):
        """Handler für Doppelklick auf Dokument"""
        selection = self.docs_listbox.curselection()
        if not selection:
            return
        
        try:
            doc_info = self.document_list[selection[0]]
            self.main_window.load_document(doc_info['pdf_path'])
        except (IndexError, KeyError) as e:
            self.logger.error(f"Fehler beim Öffnen des Dokuments: {e}")
    
    def show_context_menu(self, event):
        """Zeigt Kontextmenü für Dokumente"""
        selection = self.docs_listbox.curselection()
        if not selection:
            return
        
        try:
            doc_info = self.document_list[selection[0]]
            
            # Kontextmenü erstellen
            context_menu = tk.Menu(self.parent, tearoff=0)
            
            context_menu.add_command(
                label="Bearbeiten",
                command=lambda: self.main_window.load_document(doc_info['pdf_path'])
            )
            
            context_menu.add_command(
                label="PDF anzeigen",
                command=lambda: self.main_window.show_pdf(doc_info['pdf_path'])
            )
            
            context_menu.add_separator()
            
            context_menu.add_command(
                label="Duplizieren",
                command=lambda: self.duplicate_document(doc_info['pdf_path'])
            )
            
            context_menu.add_command(
                label="Datei-Speicherort öffnen",
                command=lambda: self.open_file_location(doc_info['pdf_path'])
            )
            
            context_menu.add_separator()
            
            context_menu.add_command(
                label="Löschen",
                command=lambda: self.delete_document(doc_info['pdf_path'])
            )
            
            # Menü anzeigen
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
                
        except (IndexError, KeyError) as e:
            self.logger.error(f"Fehler beim Anzeigen des Kontextmenüs: {e}")
    
    def duplicate_document(self, file_path):
        """Dupliziert ein Dokument"""
        try:
            new_path = self.document_manager.duplicate_document(file_path)
            if new_path:
                self.refresh_documents()
                messagebox.showinfo("Erfolg", f"Dokument wurde dupliziert:\n{new_path.name}")
            else:
                messagebox.showerror("Fehler", "Dokument konnte nicht dupliziert werden.")
        except Exception as e:
            self.logger.error(f"Fehler beim Duplizieren: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Duplizieren:\n{e}")
    
    def delete_document(self, file_path):
        """Löscht ein Dokument nach Bestätigung"""
        response = messagebox.askyesno(
            "Dokument löschen",
            f"Möchten Sie das Dokument '{file_path.name}' wirklich löschen?\n\n"
            "Diese Aktion kann nicht rückgängig gemacht werden."
        )
        
        if response:
            try:
                if self.document_manager.delete_document(file_path):
                    self.refresh_documents()
                    messagebox.showinfo("Erfolg", "Dokument wurde gelöscht.")
                else:
                    messagebox.showerror("Fehler", "Dokument konnte nicht gelöscht werden.")
            except Exception as e:
                self.logger.error(f"Fehler beim Löschen: {e}")
                messagebox.showerror("Fehler", f"Fehler beim Löschen:\n{e}")
    
    def open_file_location(self, file_path):
        """Öffnet Datei-Speicherort im Explorer"""
        try:
            if sys.platform == "win32":
                subprocess.run(['explorer', '/select,', str(file_path)])
            elif sys.platform == "darwin":
                subprocess.run(['open', '-R', str(file_path)])
            else:
                subprocess.run(['xdg-open', str(file_path.parent)])
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Speicherorts: {e}")
            messagebox.showerror("Fehler", f"Speicherort konnte nicht geöffnet werden:\n{e}")
    
    def get_selected_document(self):
        """Gibt aktuell ausgewähltes Dokument zurück"""
        selection = self.docs_listbox.curselection()
        if selection:
            try:
                return self.document_list[selection[0]]
            except (IndexError, KeyError):
                return None
        return None
    
    def select_document_by_name(self, filename: str):
        """Wählt Dokument anhand des Dateinamens aus"""
        for i, doc in enumerate(self.document_list):
            if doc['filename'] == filename:
                self.docs_listbox.selection_clear(0, tk.END)
                self.docs_listbox.selection_set(i)
                self.docs_listbox.see(i)
                return True
        return False