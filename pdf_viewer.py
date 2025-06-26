"""
PDF-Viewer Widget für die KI Manager Anwendung
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
import io

try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"PDF-Viewer Abhängigkeiten fehlen: {e}")
    print("Installiere mit: pip install PyMuPDF pillow")

from utils.logger import log_function_call, log_performance

class PDFViewerWidget:
    """PDF-Viewer Widget"""
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger("ki_manager")
        
        # PDF-Dokument Zustand
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.photo = None  # PhotoImage Referenz halten
        
        self.setup_ui()
        self.logger.debug("PDF-Viewer initialisiert")
    
    @log_function_call
    def setup_ui(self):
        """Erstellt die PDF-Viewer Oberfläche"""
        # Toolbar
        toolbar = ttk.Frame(self.parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Navigation Buttons
        nav_frame = ttk.Frame(toolbar)
        nav_frame.pack(side=tk.LEFT)
        
        ttk.Button(nav_frame, text="◀◀", command=self.first_page, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="◀", command=self.prev_page, width=5).pack(side=tk.LEFT, padx=2)
        
        self.page_var = tk.StringVar(value="0 / 0")
        ttk.Label(nav_frame, textvariable=self.page_var).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(nav_frame, text="▶", command=self.next_page, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="▶▶", command=self.last_page, width=5).pack(side=tk.LEFT, padx=2)
        
        # Zoom Controls
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        zoom_frame = ttk.Frame(toolbar)
        zoom_frame.pack(side=tk.LEFT)
        
        ttk.Button(zoom_frame, text="Zoom +", command=self.zoom_in, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom -", command=self.zoom_out, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Fit", command=self.fit_page, width=5).pack(side=tk.LEFT, padx=2)
        
        self.zoom_var = tk.StringVar(value="100%")
        ttk.Label(zoom_frame, textvariable=self.zoom_var).pack(side=tk.LEFT, padx=5)
        
        # PDF Display Area
        self.canvas_frame = ttk.Frame(self.parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas mit Scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Grid Layout
        self.canvas.grid(row=0, column=0, sticky='nsew')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Mouse Wheel Binding
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        
        # Keyboard Bindings
        self.canvas.bind("<Key>", self._on_keypress)
        self.canvas.focus_set()
    
    def _on_mousewheel(self, event):
        """Mouse Wheel Handler"""
        if event.delta:
            delta = event.delta
        elif event.num == 4:
            delta = 120
        elif event.num == 5:
            delta = -120
        else:
            delta = 0
            
        # Ctrl + Wheel = Zoom
        if event.state & 0x4:  # Ctrl pressed
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Normal scroll
            self.canvas.yview_scroll(int(-1 * (delta / 120)), "units")
    
    def _on_keypress(self, event):
        """Keyboard Handler"""
        if event.keysym == "Left":
            self.prev_page()
        elif event.keysym == "Right":
            self.next_page()
        elif event.keysym == "Home":
            self.first_page()
        elif event.keysym == "End":
            self.last_page()
    
    @log_performance
    def load_pdf(self, pdf_path: str):
        """Lädt eine PDF-Datei"""
        try:
            # Vorheriges Dokument schließen
            if self.doc:
                self.doc.close()
                
            self.doc = fitz.open(pdf_path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            
            if self.total_pages > 0:
                self.show_page()
                self.logger.info(f"PDF geladen: {pdf_path} ({self.total_pages} Seiten)")
            else:
                messagebox.showwarning("Warnung", "PDF-Datei enthält keine Seiten.")
                
        except Exception as e:
            self.logger.error(f"PDF konnte nicht geladen werden: {e}")
            messagebox.showerror("Fehler", f"PDF konnte nicht geladen werden: {e}")
    
    @log_function_call
    def show_page(self):
        """Zeigt die aktuelle Seite an"""
        if not self.doc or self.current_page >= self.total_pages:
            return
            
        try:
            # Seite rendern
            page = self.doc[self.current_page]
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Pixmap zu PIL Image konvertieren
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # Zu PhotoImage konvertieren
            self.photo = ImageTk.PhotoImage(img)
            
            # Canvas leeren und Bild anzeigen
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Scroll-Region aktualisieren
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Anzeigen aktualisieren
            self.update_display()
            
        except Exception as e:
            self.logger.error(f"Seite konnte nicht angezeigt werden: {e}")
            messagebox.showerror("Fehler", f"Seite konnte nicht angezeigt werden: {e}")
    
    def update_display(self):
        """Aktualisiert die Anzeige-Informationen"""
        self.page_var.set(f"{self.current_page + 1} / {self.total_pages}")
        self.zoom_var.set(f"{int(self.zoom * 100)}%")
    
    # Navigation Methoden
    def first_page(self):
        """Springt zur ersten Seite"""
        if self.doc and self.total_pages > 0:
            self.current_page = 0
            self.show_page()
    
    def prev_page(self):
        """Springt zur vorherigen Seite"""
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.show_page()
    
    def next_page(self):
        """Springt zur nächsten Seite"""
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page()
    
    def last_page(self):
        """Springt zur letzten Seite"""
        if self.doc and self.total_pages > 0:
            self.current_page = self.total_pages - 1
            self.show_page()
    
    # Zoom Methoden
    def zoom_in(self):
        """Vergrößert die Ansicht"""
        if self.zoom < 3.0:
            self.zoom += 0.2
            self.show_page()
    
    def zoom_out(self):
        """Verkleinert die Ansicht"""
        if self.zoom > 0.2:
            self.zoom -= 0.2
            self.show_page()
    
    def fit_page(self):
        """Passt Seite an Fenstergröße an"""
        if not self.doc or self.total_pages == 0:
            return
            
        try:
            page = self.doc[self.current_page]
            page_rect = page.rect
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                zoom_x = canvas_width / page_rect.width
                zoom_y = canvas_height / page_rect.height
                self.zoom = min(zoom_x, zoom_y) * 0.9  # 90% für Ränder
                self.show_page()
                
        except Exception as e:
            self.logger.error(f"Fit page error: {e}")
    
    def close_pdf(self):
        """Schließt die aktuelle PDF"""
        if self.doc:
            self.doc.close()
            self.doc = None
        
        self.canvas.delete("all")
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.page_var.set("0 / 0")
        self.zoom_var.set("100%")
        self.logger.debug("PDF geschlossen")
    
    def get_current_page_info(self) -> dict:
        """Gibt Informationen zur aktuellen Seite zurück"""
        return {
            'current_page': self.current_page + 1,
            'total_pages': self.total_pages,
            'zoom': self.zoom,
            'has_document': self.doc is not None
        }
    
    def goto_page(self, page_number: int):
        """Springt zu einer bestimmten Seite"""
        if self.doc and 1 <= page_number <= self.total_pages:
            self.current_page = page_number - 1
            self.show_page()
            return True
        return False
    
    def set_zoom(self, zoom_level: float):
        """Setzt Zoom-Level direkt"""
        if 0.1 <= zoom_level <= 5.0:
            self.zoom = zoom_level
            self.show_page()
            return True
        return False