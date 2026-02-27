#!/usr/bin/env python3
"""
واجهة المشغل الرئيسية (Tkinter MVP)

✅ Offline-first
✅ دعم أساسي للعربية
✅ بسيطة وسريعة النشر
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from src.shared.language_manager import lang


class GuardianGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(lang.get("app.title"))
        self.root.geometry("1200x800")
        
        # تحميل اللغة
        try:
            lang.load_language("ar")
        except FileNotFoundError:
            pass  # Fallback to keys
        
        self._build_ui()
    
    def _build_ui(self):
        # Header
        header = ttk.Label(
            self.root, 
            text=lang.get("app.title"), 
            font=('Arial', 16, 'bold')
        )
        header.pack(pady=10)
        
        # Menu Bar
        self._build_menu()
        
        # Dashboard Frame
        dashboard = ttk.Frame(self.root)
        dashboard.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Buttons Frame
        btn_frame = ttk.Frame(dashboard)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text=lang.get("dashboard.general_data")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=lang.get("dashboard.units")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=lang.get("dashboard.vaccines")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=lang.get("dashboard.ft2_files")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=lang.get("dashboard.verify"), command=self._verify).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=lang.get("dashboard.generate_pdf"), command=self._generate_pdf).pack(side=tk.LEFT, padx=5)
        
        # Results Table
        results_frame = ttk.LabelFrame(dashboard, text=lang.get("dashboard.results"))
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.results_tree = ttk.Treeview(
            results_frame, 
            columns=('Unit', 'Vaccine', 'Status', 'Decision'),
            show='headings'
        )
        self.results_tree.heading('#0', text='ID')
        self.results_tree.heading('Unit', text=lang.get("unit.name"))
        self.results_tree.heading('Vaccine', text=lang.get("vaccine.name"))
        self.results_tree.heading('Status', text=lang.get("status.safe"))
        self.results_tree.heading('Decision', text=lang.get("decision.pass"))
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
    
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        
        # Language Menu
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="العربية", command=lambda: self._switch_lang("ar"))
        lang_menu.add_command(label="English", command=lambda: self._switch_lang("en"))
        menubar.add_cascade(label="Language / اللغة", menu=lang_menu)
        
        self.root.config(menu=menubar)
    
    def _switch_lang(self, lang_code):
        try:
            lang.set_language(lang_code)
            self._refresh_ui_texts()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _refresh_ui_texts(self):
        self.root.title(lang.get("app.title"))
        # تحديث باقي العناصر...
    
    def _verify(self):
        messagebox.showinfo("Verify", "Digital verification started...")
        # هنا يتم استدعاء process_ft2.py
    
    def _generate_pdf(self):
        messagebox.showinfo("PDF", "Generating comprehensive PDF report...")
        # هنا يتم استدعاء unified_pdf_generator.py
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = GuardianGUI()
    app.run()
