"""
Workspace-Komponente für Formular-Darstellung und -Bearbeitung
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from datetime import datetime
from pathlib import Path
import os

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

from utils.logger import log_function_call, log_performance

class Workspace:
    """Arbeitsbereich für Formulare und Dokumentenbearbeitung"""
    
    def __init__(self, parent, config, document_manager, main_window):
        self.parent = parent
        self.config = config
        self.document_manager = document_manager
        self.main_window = main_window
        self.logger = logging.getLogger("ki_manager")
        
        # Zustand des Arbeitsbereichs
        self.current_document_type = None
        self.current_document_data = None
        self.form_entries = {}
        self.has_changes = False
        
        self.setup_workspace()
        self.logger.debug("Workspace initialisiert")
    
    @log_function_call
    def setup_workspace(self):
        """Richtet den Arbeitsbereich ein"""
        # Container für verschiedene Ansichten
        self.container = ttk.Frame(self.parent)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Verschiedene Frames für unterschiedliche Ansichten
        self.frames = {}
        self.create_frames()
        
        # Initial Willkommensseite anzeigen
        self.show_welcome()
    
    def create_frames(self):
        """Erstellt verschiedene Frame-Container"""
        # Welcome Frame
        self.frames['welcome'] = ttk.Frame(self.container)
        
        # Use Case Frame
        self.frames['use_case'] = ttk.Frame(self.container)
        
        # Company Profile Frame  
        self.frames['company_profile'] = ttk.Frame(self.container)
        
        # Document List Frame
        self.frames['document_list'] = ttk.Frame(self.container)
        
        # Alle Frames im Container platzieren
        for frame in self.frames.values():
            frame.place(x=0, y=0, relwidth=1, relheight=1)
    
    def show_frame(self, frame_name):
        """Zeigt einen bestimmten Frame an"""
        if frame_name in self.frames:
            self.frames[frame_name].tkraise()
            self.logger.debug(f"Frame angezeigt: {frame_name}")
    
    @log_function_call
    def show_welcome(self):
        """Zeigt die Willkommensseite"""
        self.clear_frame('welcome')
        frame = self.frames['welcome']
        
        # Logo-Bereich
        logo_frame = tk.Frame(frame, bg='white', height=100)
        logo_frame.pack(fill=tk.X, pady=(20, 30))
        logo_frame.pack_propagate(False)
        
        # Logo laden falls vorhanden
        self._load_logo(logo_frame)
        
        # Willkommenstext
        welcome_text = """
Willkommen zum KI Use Case & Unternehmenssteckbrief Manager

Wählen Sie eine Option aus der Sidebar, um zu beginnen:

📋 Neuer KI Use Case
   Erfassen Sie strukturiert neue KI-Anwendungsfälle

🏢 Neuer Unternehmenssteckbrief  
   Analysieren Sie das Digitalisierungspotenzial von Unternehmen

📁 Dokument öffnen
   Bearbeiten Sie vorhandene Dokumente

Features:
• Automatische PDF-Generierung
• Integrierte PDF-Vorschau
• Suchfunktion in Dokumenten
• Export- und Backup-Funktionen
        """
        
        welcome_label = ttk.Label(
            frame, 
            text=welcome_text,
            font=('Arial', 12),
            anchor='center',
            justify='center'
        )
        welcome_label.pack(expand=True)
        
        # Statistiken anzeigen
        self._show_statistics(frame)
        
        self.show_frame('welcome')
        self.current_document_type = None
        self.has_changes = False
    
    def _load_logo(self, logo_frame):
        """Lädt und zeigt das Logo an"""
        logo_path = Path(self.config.app_config.logo_path)
        
        if logo_path.exists() and Image:
            try:
                image = Image.open(logo_path)
                image = image.resize((
                    self.config.app_config.logo_width,
                    self.config.app_config.logo_height
                ), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                logo_label = ttk.Label(logo_frame, image=photo)
                logo_label.image = photo  # Referenz halten
                logo_label.pack(expand=True)
                
            except Exception as e:
                self.logger.warning(f"Logo konnte nicht geladen werden: {e}")
                self._show_text_logo(logo_frame)
        else:
            self._show_text_logo(logo_frame)
    
    def _show_text_logo(self, logo_frame):
        """Zeigt Text-Logo als Fallback"""
        text_logo = ttk.Label(
            logo_frame,
            text="KI Manager",
            font=('Arial', 24, 'bold'),
            foreground='#2c3e50'
        )
        text_logo.pack(expand=True)
    
    def _show_statistics(self, parent):
        """Zeigt Dokumentenstatistiken"""
        try:
            stats = self.document_manager.get_statistics()
            
            stats_frame = ttk.LabelFrame(parent, text="Dokumentenstatistiken", padding=10)
            stats_frame.pack(pady=20, padx=50, fill=tk.X)
            
            stats_text = f"""
Gesamt: {stats['total_documents']} Dokumente
KI Use Cases: {stats['use_cases']}
Unternehmenssteckbriefe: {stats['company_profiles']}
Gesamtgröße: {stats['total_size_mb']:.1f} MB
            """.strip()
            
            ttk.Label(stats_frame, text=stats_text, justify='center').pack()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Statistiken: {e}")
    
    @log_function_call
    def show_use_case_form(self, data=None):
        """Zeigt das Use Case Formular"""
        self.current_document_type = 'use_case'
        self.current_document_data = data or {}
        self.has_changes = False
        
        self.clear_frame('use_case')
        frame = self.frames['use_case']
        
        # Scrollbarer Container
        canvas = tk.Canvas(frame, bg='white')
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Formular erstellen
        self._build_use_case_form(scrollable_frame)
        
        # Canvas und Scrollbar packen
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Daten laden falls Bearbeitung
        if data:
            self._load_use_case_data(data)
        
        # Mouse wheel binding für Canvas
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        self.show_frame('use_case')
    
    def _build_use_case_form(self, parent):
        """Erstellt das Use Case Formular"""
        self.form_entries = {}
        
        # Titel
        title_label = ttk.Label(parent, text="KI Use Case Canvas", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        # Grundinformationen
        basic_frame = ttk.LabelFrame(parent, text="Grundinformationen", padding=10)
        basic_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Grid für Grunddaten
        basic_grid = ttk.Frame(basic_frame)
        basic_grid.pack(fill=tk.X)
        
        fields = [
            ("Verantwortlich:", "verantwortlich"),
            ("Bereich/Abteilung:", "bereich")
        ]
        
        for i, (label, key) in enumerate(fields):
            ttk.Label(basic_grid, text=label).grid(row=i//2, column=(i%2)*2, sticky='w', pady=5, padx=5)
            entry = ttk.Entry(basic_grid, width=30)
            entry.grid(row=i//2, column=(i%2)*2+1, pady=5, padx=5)
            entry.bind('<KeyRelease>', self._on_form_change)
            self.form_entries[key] = entry
        
        # Status
        ttk.Label(basic_grid, text="Status:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        status_combo = ttk.Combobox(basic_grid, values=self.config.get_status_options(), width=27)
        status_combo.grid(row=1, column=1, pady=5, padx=5)
        status_combo.bind('<<ComboboxSelected>>', self._on_form_change)
        self.form_entries['status'] = status_combo
        
        # Beschreibungsbereich
        desc_frame = ttk.LabelFrame(parent, text="Beschreibung", padding=10)
        desc_frame.pack(fill=tk.X, padx=20, pady=10)
        
        desc_fields = [
            ("Beschreibung des Use-Cases:", "beschreibung", 4),
            ("Problemstellung:", "problemstellung", 3),
            ("Zielstellung/Nutzen:", "zielstellung", 3)
        ]
        
        for label, key, height in desc_fields:
            ttk.Label(desc_frame, text=label).pack(anchor='w', pady=(10, 0))
            text_widget = scrolledtext.ScrolledText(desc_frame, height=height, width=80)
            text_widget.pack(fill=tk.X, pady=5)
            text_widget.bind('<KeyRelease>', self._on_form_change)
            self.form_entries[key] = text_widget
        
        # KI-Fähigkeiten
        ki_frame = ttk.LabelFrame(parent, text="Relevante KI-Fähigkeiten", padding=10)
        ki_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.form_entries['ki_faehigkeiten'] = {}
        ki_capabilities = self.config.get_ki_capabilities()
        
        ki_grid = ttk.Frame(ki_frame)
        ki_grid.pack(fill=tk.X)
        
        for i, capability in enumerate(ki_capabilities):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(ki_grid, text=capability, variable=var, 
                               command=self._on_form_change)
            cb.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=3)
            self.form_entries['ki_faehigkeiten'][capability] = var
        
        # Mehrwert
        value_frame = ttk.LabelFrame(parent, text="Mehrwert", padding=10)
        value_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(value_frame, text="Wie passt der Use-Case zur KI-Vision?").pack(anchor='w')
        ki_vision_text = scrolledtext.ScrolledText(value_frame, height=3, width=80)
        ki_vision_text.pack(fill=tk.X, pady=5)
        ki_vision_text.bind('<KeyRelease>', self._on_form_change)
        self.form_entries['ki_vision'] = ki_vision_text
        
        # Strategische Vorteile
        ttk.Label(value_frame, text="Strategische Vorteile:").pack(anchor='w', pady=(15, 5))
        self.form_entries['strategische_vorteile'] = {}
        
        advantages = self.config.get_strategic_advantages()
        for advantage in advantages:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(value_frame, text=advantage, variable=var,
                               command=self._on_form_change)
            cb.pack(anchor='w', pady=2)
            self.form_entries['strategische_vorteile'][advantage] = var
        
        # Geschäftswert
        ttk.Label(value_frame, text="Geschätzter Geschäftswert:").pack(anchor='w', pady=(15, 5))
        geschaeftswert_entry = ttk.Entry(value_frame, width=60)
        geschaeftswert_entry.pack(anchor='w', pady=5)
        geschaeftswert_entry.bind('<KeyRelease>', self._on_form_change)
        self.form_entries['geschaeftswert'] = geschaeftswert_entry
        
        # Bewertung
        eval_frame = ttk.LabelFrame(parent, text="Bewertung (0-5 Punkte)", padding=10)
        eval_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.form_entries['bewertung'] = {}
        criteria = self.config.get_evaluation_criteria()
        
        for i, criterion in enumerate(criteria):
            criterion_frame = ttk.Frame(eval_frame)
            criterion_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(criterion_frame, text=f"{criterion}:", width=25).pack(side=tk.LEFT)
            scale = tk.Scale(criterion_frame, from_=0, to=5, orient=tk.HORIZONTAL, 
                           length=300, command=lambda v, c=criterion: self._on_form_change())
            scale.pack(side=tk.LEFT, padx=10)
            self.form_entries['bewertung'][criterion] = scale
        
        # Zeitschätzung
        time_frame = ttk.LabelFrame(parent, text="Zeitschätzung", padding=10)
        time_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(time_frame, text="Entwicklungszeit bis Proof of Concept:").pack(anchor='w')
        time_combo = ttk.Combobox(time_frame, values=self.config.get_development_time_options(), width=30)
        time_combo.pack(anchor='w', pady=10)
        time_combo.bind('<<ComboboxSelected>>', self._on_form_change)
        self.form_entries['entwicklungszeit'] = time_combo
        
        # Buttons
        self._add_form_buttons(parent)
    
    @log_function_call  
    def show_company_profile_form(self, data=None):
        """Zeigt das Company Profile Formular"""
        self.current_document_type = 'company_profile'
        self.current_document_data = data or {}
        self.has_changes = False
        
        self.clear_frame('company_profile')
        frame = self.frames['company_profile']
        
        # Scrollbarer Container
        canvas = tk.Canvas(frame, bg='white')
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Formular erstellen
        self._build_company_profile_form(scrollable_frame)
        
        # Canvas und Scrollbar packen
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Daten laden falls Bearbeitung
        if data:
            self._load_company_profile_data(data)
        
        # Mouse wheel binding
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        self.show_frame('company_profile')
    
    def _build_company_profile_form(self, parent):
        """Erstellt das Company Profile Formular"""
        self.form_entries = {}
        
        # Titel
        title_label = ttk.Label(parent, text="Unternehmenssteckbrief - Digitalisierung & KI-Potenzial", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        # Unternehmensdaten
        company_frame = ttk.LabelFrame(parent, text="Unternehmensdaten", padding=10)
        company_frame.pack(fill=tk.X, padx=20, pady=10)
        
        company_grid = ttk.Frame(company_frame)
        company_grid.pack(fill=tk.X)
        
        # Grunddaten-Felder
        basic_fields = [
            ("Name des Unternehmens:", "unternehmensname"),
            ("Gründungsjahr:", "gruendungsjahr"),
            ("Adresse:", "adresse"),
            ("Branche/Gewerk:", "branche"),
            ("Anzahl Mitarbeiter:", "mitarbeiter"),
            ("Davon Auszubildende:", "auszubildende"),
            ("Kontaktperson:", "kontaktperson"),
            ("Position im Betrieb:", "position"),
            ("Telefon:", "telefon"),
            ("E-Mail:", "email"),
            ("Website:", "website")
        ]
        
        for i, (label, key) in enumerate(basic_fields):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(company_grid, text=label).grid(row=row, column=col, sticky='w', pady=5, padx=5)
            entry = ttk.Entry(company_grid, width=30)
            entry.grid(row=row, column=col+1, pady=5, padx=5)
            entry.bind('<KeyRelease>', self._on_form_change)
            self.form_entries[key] = entry
        
        # Umsatzklasse
        row = len(basic_fields) // 2
        ttk.Label(company_grid, text="Umsatzklasse:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        umsatz_combo = ttk.Combobox(company_grid, values=self.config.get_revenue_classes(), width=27)
        umsatz_combo.grid(row=row, column=1, pady=5, padx=5)
        umsatz_combo.bind('<<ComboboxSelected>>', self._on_form_change)
        self.form_entries['umsatzklasse'] = umsatz_combo
        
        # Geschäftstätigkeit
        business_frame = ttk.LabelFrame(parent, text="Aktuelle Geschäftstätigkeit", padding=10)
        business_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(business_frame, text="Hauptleistungen/Produkte:").pack(anchor='w')
        hauptleistungen_text = scrolledtext.ScrolledText(business_frame, height=3, width=80)
        hauptleistungen_text.pack(fill=tk.X, pady=5)
        hauptleistungen_text.bind('<KeyRelease>', self._on_form_change)
        self.form_entries['hauptleistungen'] = hauptleistungen_text
        
        # Kundengruppen
        ttk.Label(business_frame, text="Typische Kundengruppen:").pack(anchor='w', pady=(15, 5))
        self.form_entries['kundengruppen'] = {}
        
        customer_frame = ttk.Frame(business_frame)
        customer_frame.pack(fill=tk.X, pady=5)
        
        customer_groups = self.config.get_customer_groups()
        for i, group in enumerate(customer_groups):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(customer_frame, text=group, variable=var,
                               command=self._on_form_change)
            cb.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=2)
            self.form_entries['kundengruppen'][group] = var
        
        # Geschäftsradius und Aufträge
        business_details = ttk.Frame(business_frame)
        business_details.pack(fill=tk.X, pady=10)
        
        ttk.Label(business_details, text="Geschäftsradius:").grid(row=0, column=0, sticky='w', pady=5)
        radius_combo = ttk.Combobox(business_details, values=self.config.get_business_radius_options(), width=30)
        radius_combo.grid(row=0, column=1, sticky='w', pady=5, padx=10)
        radius_combo.bind('<<ComboboxSelected>>', self._on_form_change)
        self.form_entries['geschaeftsradius'] = radius_combo
        
        ttk.Label(business_details, text="Aufträge pro Monat:").grid(row=1, column=0, sticky='w', pady=5)
        auftraege_entry = ttk.Entry(business_details, width=30)
        auftraege_entry.grid(row=1, column=1, sticky='w', pady=5, padx=10)
        auftraege_entry.bind('<KeyRelease>', self._on_form_change)
        self.form_entries['auftraege_monat'] = auftraege_entry
        
        # Digitalisierungsstand
        digital_frame = ttk.LabelFrame(parent, text="Digitalisierungsstand", padding=10)
        digital_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(digital_frame, text="Genutzte digitale Systeme:").pack(anchor='w')
        self.form_entries['digitale_systeme'] = {}
        
        systems_frame = ttk.Frame(digital_frame)
        systems_frame.pack(fill=tk.X, pady=10)
        
        digital_systems = self.config.get_digital_systems()
        for i, system in enumerate(digital_systems):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(systems_frame, text=system, variable=var,
                               command=self._on_form_change)
            cb.grid(row=i//3, column=i%3, sticky='w', padx=5, pady=3)
            self.form_entries['digitale_systeme'][system] = var
        
        # Digitalisierungsgrad
        ttk.Label(digital_frame, text="Digitalisierungsgrad im Branchenvergleich:").pack(anchor='w', pady=(15, 5))
        digital_combo = ttk.Combobox(digital_frame, values=self.config.get_digitalization_levels(), width=30)
        digital_combo.pack(anchor='w', pady=5)
        digital_combo.bind('<<ComboboxSelected>>', self._on_form_change)
        self.form_entries['digitalisierungsgrad'] = digital_combo
        
        # Herausforderungen
        challenges_frame = ttk.LabelFrame(parent, text="Herausforderungen & Potenziale", padding=10)
        challenges_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(challenges_frame, text="Größte betriebliche Herausforderungen:").pack(anchor='w')
        self.form_entries['herausforderungen'] = {}
        
        challenges_grid = ttk.Frame(challenges_frame)
        challenges_grid.pack(fill=tk.X, pady=10)
        
        challenges = self.config.get_challenges()
        for i, challenge in enumerate(challenges):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(challenges_grid, text=challenge, variable=var,
                               command=self._on_form_change)
            cb.grid(row=i//2, column=i%2, sticky='w', padx=5, pady=3)
            self.form_entries['herausforderungen'][challenge] = var
        
        # Digitalisierungspotenzial
        ttk.Label(challenges_frame, text="Potenzial für Digitalisierung/KI:").pack(anchor='w', pady=(15, 5))
        potential_text = scrolledtext.ScrolledText(challenges_frame, height=3, width=80)
        potential_text.pack(fill=tk.X, pady=5)
        potential_text.bind('<KeyRelease>', self._on_form_change)
        self.form_entries['digitalisierungspotenzial'] = potential_text
        
        # KI-Readiness
        ki_frame = ttk.LabelFrame(parent, text="KI-Readiness", padding=10)
        ki_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ki_details = ttk.Frame(ki_frame)
        ki_details.pack(fill=tk.X)
        
        ttk.Label(ki_details, text="Verständnis von KI-Technologien:").grid(row=0, column=0, sticky='w', pady=5)
        ki_understanding_combo = ttk.Combobox(ki_details, values=self.config.get_ai_understanding_levels(), width=30)
        ki_understanding_combo.grid(row=0, column=1, sticky='w', pady=5, padx=10)
        ki_understanding_combo.bind('<<ComboboxSelected>>', self._on_form_change)
        self.form_entries['ki_verstaendnis'] = ki_understanding_combo
        
        ttk.Label(ki_details, text="Bereits genutzte KI-Anwendungen:").grid(row=1, column=0, sticky='w', pady=5)
        ki_apps_entry = ttk.Entry(ki_details, width=50)
        ki_apps_entry.grid(row=1, column=1, sticky='w', pady=5, padx=10)
        ki_apps_entry.bind('<KeyRelease>', self._on_form_change)
        self.form_entries['ki_anwendungen'] = ki_apps_entry
        
        # Buttons
        self._add_form_buttons(parent)
    
    def _add_form_buttons(self, parent):
        """Fügt Formular-Buttons hinzu"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=20, pady=30)
        
        # Button-Container zentrieren
        button_container = ttk.Frame(button_frame)
        button_container.pack(anchor='center')
        
        ttk.Button(button_container, text="Speichern & PDF erstellen", 
                  command=self.save_current_document, width=25).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_container, text="Abbrechen", 
                  command=self.show_welcome, width=15).pack(side=tk.LEFT, padx=5)
        
        # Shortcuts anzeigen
        shortcut_label = ttk.Label(button_frame, text="Shortcuts: Ctrl+S = Speichern, Esc = Abbrechen", 
                                  font=('Arial', 8), foreground='gray')
        shortcut_label.pack(pady=(10, 0))
        
        # Keyboard bindings
        parent.bind_all('<Control-s>', lambda e: self.save_current_document())
        parent.bind_all('<Escape>', lambda e: self.show_welcome())
    
    def _on_form_change(self, event=None):
        """Handler für Formular-Änderungen"""
        self.has_changes = True
        self.logger.debug("Formular-Änderung erkannt")
    
    def _load_use_case_data(self, data):
        """Lädt Use Case Daten in das Formular"""
        try:
            # Einfache Textfelder
            simple_fields = ['verantwortlich', 'bereich', 'status', 'geschaeftswert', 'entwicklungszeit']
            for field in simple_fields:
                if field in data and field in self.form_entries:
                    widget = self.form_entries[field]
                    if isinstance(widget, ttk.Combobox):
                        widget.set(data[field])
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, data[field])
            
            # Textbereiche
            text_fields = ['beschreibung', 'problemstellung', 'zielstellung', 'ki_vision']
            for field in text_fields:
                if field in data and field in self.form_entries:
                    widget = self.form_entries[field]
                    widget.delete('1.0', tk.END)
                    widget.insert('1.0', data[field])
            
            # Checkboxen
            checkbox_groups = ['ki_faehigkeiten', 'strategische_vorteile']
            for group in checkbox_groups:
                if group in data and group in self.form_entries:
                    for key, value in data[group].items():
                        if key in self.form_entries[group]:
                            self.form_entries[group][key].set(value)
            
            # Bewertungen (Scales)
            if 'bewertung' in data and 'bewertung' in self.form_entries:
                for key, value in data['bewertung'].items():
                    if key in self.form_entries['bewertung']:
                        self.form_entries['bewertung'][key].set(value)
            
            self.has_changes = False
            self.logger.debug("Use Case Daten geladen")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Use Case Daten: {e}")
            messagebox.showerror("Fehler", f"Daten konnten nicht geladen werden:\n{e}")
    
    def _load_company_profile_data(self, data):
        """Lädt Company Profile Daten in das Formular"""
        try:
            # Einfache Textfelder
            text_fields = [
                'unternehmensname', 'gruendungsjahr', 'adresse', 'branche',
                'mitarbeiter', 'auszubildende', 'kontaktperson', 'position',
                'telefon', 'email', 'website', 'auftraege_monat', 'ki_anwendungen'
            ]
            
            for field in text_fields:
                if field in data and field in self.form_entries:
                    widget = self.form_entries[field]
                    widget.delete(0, tk.END)
                    widget.insert(0, data[field])
            
            # Comboboxen
            combo_fields = ['umsatzklasse', 'geschaeftsradius', 'digitalisierungsgrad', 'ki_verstaendnis']
            for field in combo_fields:
                if field in data and field in self.form_entries:
                    self.form_entries[field].set(data[field])
            
            # Textbereiche
            text_areas = ['hauptleistungen', 'digitalisierungspotenzial']
            for field in text_areas:
                if field in data and field in self.form_entries:
                    widget = self.form_entries[field]
                    widget.delete('1.0', tk.END)
                    widget.insert('1.0', data[field])
            
            # Checkboxen-Gruppen
            checkbox_groups = ['kundengruppen', 'digitale_systeme', 'herausforderungen']
            for group in checkbox_groups:
                if group in data and group in self.form_entries:
                    for key, value in data[group].items():
                        if key in self.form_entries[group]:
                            self.form_entries[group][key].set(value)
            
            self.has_changes = False
            self.logger.debug("Company Profile Daten geladen")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Company Profile Daten: {e}")
            messagebox.showerror("Fehler", f"Daten konnten nicht geladen werden:\n{e}")
    
    def clear_frame(self, frame_name):
        """Leert einen Frame komplett"""
        if frame_name in self.frames:
            for widget in self.frames[frame_name].winfo_children():
                widget.destroy()
    
    @log_performance
    def save_current_document(self):
        """Speichert das aktuelle Dokument"""
        if not self.current_document_type:
            messagebox.showwarning("Warnung", "Kein Dokument zum Speichern geöffnet.")
            return False
        
        try:
            # Daten aus Formular sammeln
            if self.current_document_type == 'use_case':
                data = self._collect_use_case_data()
            elif self.current_document_type == 'company_profile':
                data = self._collect_company_profile_data()
            else:
                messagebox.showerror("Fehler", f"Unbekannter Dokumenttyp: {self.current_document_type}")
                return False
            
            # Validierung
            if not self._validate_document_data(data):
                return False
            
            # Speichern über Hauptfenster
            success = self.main_window.save_document(self.current_document_type, data)
            
            if success:
                self.has_changes = False
                return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern: {e}")
            messagebox.showerror("Fehler", f"Dokument konnte nicht gespeichert werden:\n{e}")
        
        return False
    
    def _collect_use_case_data(self):
        """Sammelt Use Case Daten aus dem Formular"""
        data = {
            'type': 'use_case',
            'version': '2.0'
        }
        
        # Einfache Felder
        simple_fields = ['verantwortlich', 'bereich', 'status', 'geschaeftswert', 'entwicklungszeit']
        for field in simple_fields:
            if field in self.form_entries:
                widget = self.form_entries[field]
                if isinstance(widget, ttk.Combobox):
                    data[field] = widget.get()
                else:
                    data[field] = widget.get()
        
        # Textbereiche
        text_fields = ['beschreibung', 'problemstellung', 'zielstellung', 'ki_vision']
        for field in text_fields:
            if field in self.form_entries:
                data[field] = self.form_entries[field].get('1.0', tk.END).strip()
        
        # Checkboxen
        checkbox_groups = ['ki_faehigkeiten', 'strategische_vorteile']
        for group in checkbox_groups:
            if group in self.form_entries:
                data[group] = {k: v.get() for k, v in self.form_entries[group].items()}
        
        # Bewertungen
        if 'bewertung' in self.form_entries:
            data['bewertung'] = {k: v.get() for k, v in self.form_entries['bewertung'].items()}
        
        return data
    
    def _collect_company_profile_data(self):
        """Sammelt Company Profile Daten aus dem Formular"""
        data = {
            'type': 'company_profile',
            'version': '2.0'
        }
        
        # Einfache Textfelder
        text_fields = [
            'unternehmensname', 'gruendungsjahr', 'adresse', 'branche',
            'mitarbeiter', 'auszubildende', 'kontaktperson', 'position',
            'telefon', 'email', 'website', 'auftraege_monat', 'ki_anwendungen'
        ]
        
        for field in text_fields:
            if field in self.form_entries:
                data[field] = self.form_entries[field].get()
        
        # Comboboxen
        combo_fields = ['umsatzklasse', 'geschaeftsradius', 'digitalisierungsgrad', 'ki_verstaendnis']
        for field in combo_fields:
            if field in self.form_entries:
                data[field] = self.form_entries[field].get()
        
        # Textbereiche
        text_areas = ['hauptleistungen', 'digitalisierungspotenzial']
        for field in text_areas:
            if field in self.form_entries:
                data[field] = self.form_entries[field].get('1.0', tk.END).strip()
        
        # Checkboxen-Gruppen
        checkbox_groups = ['kundengruppen', 'digitale_systeme', 'herausforderungen']
        for group in checkbox_groups:
            if group in self.form_entries:
                data[group] = {k: v.get() for k, v in self.form_entries[group].items()}
        
        return data
    
    def _validate_document_data(self, data):
        """Validiert Dokumentdaten vor dem Speichern"""
        if data['type'] == 'use_case':
            required_fields = ['verantwortlich', 'beschreibung']
            field_names = {'verantwortlich': 'Verantwortlich', 'beschreibung': 'Beschreibung'}
        elif data['type'] == 'company_profile':
            required_fields = ['unternehmensname', 'branche']
            field_names = {'unternehmensname': 'Unternehmensname', 'branche': 'Branche'}
        else:
            return True
        
        # Prüfe Pflichtfelder
        missing_fields = []
        for field in required_fields:
            if not data.get(field, '').strip():
                missing_fields.append(field_names.get(field, field))
        
        if missing_fields:
            messagebox.showerror(
                "Validierungsfehler",
                f"Folgende Pflichtfelder müssen ausgefüllt werden:\n\n• " + 
                "\n• ".join(missing_fields)
            )
            return False
        
        return True
    
    def has_unsaved_changes(self):
        """Prüft ob ungespeicherte Änderungen vorhanden sind"""
        return self.has_changes
    
    def show_document_list(self):
        """Zeigt eine Dokumentenliste im Arbeitsbereich"""
        self.clear_frame('document_list')
        frame = self.frames['document_list']
        
        # Titel
        title_label = ttk.Label(frame, text="Dokumentenübersicht", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        # Dokumentenliste mit Details
        try:
            documents = self.document_manager.get_document_list()
            
            if not documents:
                ttk.Label(frame, text="Keine Dokumente vorhanden.", 
                         font=('Arial', 12)).pack(expand=True)
                self.show_frame('document_list')
                return
            
            # Treeview für Dokumentenliste
            tree_frame = ttk.Frame(frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            columns = ('Typ', 'Name', 'Erstellt', 'Größe')
            tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
            
            # Spalten konfigurieren
            tree.heading('#0', text='Dateiname')
            tree.column('#0', width=200)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Dokumente einfügen
            for doc in documents:
                doc_type = "Use Case" if doc['type'] == 'use_case' else "Steckbrief"
                created = doc.get('created', doc['modified']).strftime('%d.%m.%Y')
                size = f"{doc['size'] / 1024:.1f} KB"
                title = doc.get('title', doc['filename'])[:30]
                
                tree.insert('', tk.END, text=doc['filename'],
                           values=(doc_type, title, created, size))
            
            # Doppelklick-Binding
            tree.bind('<Double-1>', lambda e: self._on_tree_double_click(tree))
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Statistiken
            stats_frame = ttk.LabelFrame(frame, text="Statistiken", padding=10)
            stats_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            
            stats = self.document_manager.get_statistics()
            stats_text = f"Gesamt: {stats['total_documents']} | Use Cases: {stats['use_cases']} | Steckbriefe: {stats['company_profiles']}"
            ttk.Label(stats_frame, text=stats_text).pack()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Anzeigen der Dokumentenliste: {e}")
            ttk.Label(frame, text=f"Fehler beim Laden der Dokumente:\n{e}").pack(expand=True)
        
        self.show_frame('document_list')
    
    def _on_tree_double_click(self, tree):
        """Handler für Doppelklick auf Treeview-Element"""
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            filename = item['text']
            
            # Dokument laden
            file_path = self.document_manager.docs_folder / filename
            if file_path.exists():
                self.main_window.load_document(file_path)
    
    def get_current_document_info(self):
        """Gibt Informationen zum aktuellen Dokument zurück"""
        return {
            'type': self.current_document_type,
            'has_changes': self.has_changes,
            'data': self.current_document_data
        }
    
    def reset_form(self):
        """Setzt das aktuelle Formular zurück"""
        if self.current_document_type == 'use_case':
            self.show_use_case_form()
        elif self.current_document_type == 'company_profile':
            self.show_company_profile_form()
    
    def export_current_document(self, format='json'):
        """Exportiert aktuelles Dokument in verschiedene Formate"""
        # Placeholder für zukünftige Export-Funktionalität
        pass
    
    def import_document_data(self, file_path):
        """Importiert Dokumentdaten aus Datei"""
        # Placeholder für zukünftige Import-Funktionalität
        pass