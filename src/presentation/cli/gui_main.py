#!/usr/bin/env python3
"""
واجهة المشغل الرئيسية (Tkinter Production-ready) - الإصدار المحسّن
✅ Offline-first
✅ دعم كامل للعربية والإنجليزية
✅ تقارير لكل جهاز أو تقرير كامل للدورة
✅ إدراج ملفات FT2 من أي مسار
"""
import json
import logging
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
import os
import sys
import signal
import subprocess
from importlib import util

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# استيراد مساعد الاستيراد الآمن
try:
    from src.utils.import_helpers import safe_import, check_module_available
except ImportError:
    # تعريف دالة مبسطة في حال عدم توفر ملف المساعد
    def safe_import(module_path, attr=None, fallback=None, **kwargs):
        try:
            mod = __import__(module_path, fromlist=[attr] if attr else [])
            if attr:
                return getattr(mod, attr)
            return mod
        except (ImportError, AttributeError):
            return fallback
    
    def check_module_available(module_path):
        return util.find_spec(module_path) is not None

# استيراد LanguageManager بأمان باستخدام safe_import
lang = safe_import("src.shared.language_manager", "lang", fallback=None)
LANG_AVAILABLE = lang is not None
if not LANG_AVAILABLE:
    logger.warning("LanguageManager غير متاح، سيتم استخدام النصوص الاحتياطية")

# التحقق من توفر Use Case
UC_AVAILABLE = check_module_available("src.application.use_cases.generate_device_report_uc")

# التحقق من توفر Repository
REPO_AVAILABLE = check_module_available("src.infrastructure.repositories.device_repository")

# استيراد AppComposer بأمان
AppComposer = safe_import("src.application.app_composer", "AppComposer", fallback=None)
COMPOSER_AVAILABLE = AppComposer is not None


class GuardianGUI:
    def __init__(self):
        self.root = tk.Tk()
        self._init_language()
        self.root.title(self._get_text("app.title"))
        self.root.geometry("1200x800")

        self.cycle_id = f"CC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.cycle_data = {
            "cycle_id": self.cycle_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "municipality": "",
            "health_directorate": "",
            "supervisor": "",
            "cold_chain_officer": "",
            "units": [],
            "vaccines": [],
            "ft2_files": [],
            "reports_generated": [],
        }

        self.ui_refs = {}
        self._build_ui()
        
        # perform a quick health check on start-up
        if COMPOSER_AVAILABLE and AppComposer:
            healthy = (
                AppComposer.health_check()
                if hasattr(AppComposer, "health_check")
                else True
            )
            if not healthy:
                messagebox.showwarning(
                    self._get_text("error.title"),
                    "تحذير: فحص صحة التطبيق فشل. قد تكون بعض المكونات غير متوفرة.",
                )
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ========================== دعم اللغة ==========================
    def _init_language(self):
        """تهيئة اللغة الافتراضية (العربية) مع fallback للإنجليزية."""
        requested_lang = os.environ.get("CCI_LANG", "ar")
        self.current_lang = "en"
        if not LANG_AVAILABLE or not lang:
            logger.warning("LanguageManager غير متاح، استخدام الإنجليزية")
            return

        try:
            locales_dir = Path(__file__).parent.parent.parent / "shared" / "locales"
            lang.load_language(requested_lang, translations_dir=locales_dir)
            self.current_lang = requested_lang
            lang.set_language(self.current_lang)
            logger.info("تم تحميل الترجمة العربية بنجاح")
        except Exception as e:
            logger.warning(f"فشل تحميل العربية: {e}")
            try:
                lang.load_language("en", translations_dir=locales_dir)
                self.current_lang = "en"
                lang.set_language(self.current_lang)
                logger.info("تم تحميل الترجمة الإنجليزية كبديل")
            except Exception as e2:
                logger.error(f"فشل تحميل أي لغة: {e2}")

    def _get_text(self, key: str, **kwargs) -> str:
        """الحصول على نص مترجم مع fallback آمن."""
        if LANG_AVAILABLE and lang:
            try:
                return lang.get(key, **kwargs)
            except Exception:
                return key
        return key

    def _is_rtl(self) -> bool:
        """Return True if current language is right-to-left."""
        if LANG_AVAILABLE and lang:
            try:
                return lang.get_direction() == "rtl"
            except Exception:
                pass
        return False

    def _ensure_ft2_data_available(self) -> bool:
        """التحقق من توفر بيانات FT2 قبل المتابعة — آمن في وضع Headless"""
        if not os.path.exists(getattr(self, "data_path", "")):
            try:
                import tkinter.messagebox as msg
                msg.showwarning(
                    "بيانات مفقودة", "ملف FT2 غير موجود. يرجى التحقق من المسار."
                )
            except Exception:
                logger.warning(
                    "ft2_file_missing", extra={"path": getattr(self, "data_path", None)}
                )
            return False
        return True

    def _switch_lang(self, lang_code: str):
        """تبديل لغة الواجهة وتحديث جميع النصوص."""
        if not LANG_AVAILABLE or not lang:
            messagebox.showerror(
                self._get_text("error.title"), "LanguageManager غير متاح"
            )
            return

        try:
            # تحميل اللغة إذا لم تكن محملة مسبقاً
            if hasattr(lang, '_translations') and lang_code not in lang._translations:
                locales_dir = Path(__file__).parent.parent.parent / "shared" / "locales"
                lang.load_language(lang_code, translations_dir=locales_dir)

            lang.set_language(lang_code)
            self.current_lang = lang_code
            logger.info(f"تم تبديل اللغة إلى: {lang_code}")
            
            # إعادة تشغيل الواجهة باللغة الجديدة
            self.root.destroy()
            env = {
                **os.environ,
                "CCI_LANG": lang_code,
                "PYTHONPATH": str(Path(__file__).parent.parent.parent.parent),
            }
            subprocess.Popen(
                [sys.executable, __file__], env=env, start_new_session=True
            )
            os.kill(os.getpid(), signal.SIGKILL)
        except Exception as e:
            logger.exception(f"فشل تبديل اللغة: {e}")
            messagebox.showerror(self._get_text("error.title"), str(e))

    def _refresh_ui_texts(self):
        """تحديث جميع النصوص في الواجهة بعد تغيير اللغة."""
        self.root.title(self._get_text("app.title"))

        if "header" in self.ui_refs:
            self.ui_refs["header"].config(text=self._get_text("app.title"))
        if "cycle_info" in self.ui_refs:
            self.ui_refs["cycle_info"].config(
                text=f"Cycle ID: {self.cycle_id} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

        self._build_menu()

        btn_mapping = {
            "btn_general": "dashboard.general_data",
            "btn_units": "dashboard.units",
            "btn_vaccines": "dashboard.vaccines",
            "btn_ft2": "dashboard.ft2_files",
            "btn_verify": "dashboard.verify",
            "btn_generate": "dashboard.generate_pdf",
        }
        for ref_name, text_key in btn_mapping.items():
            if ref_name in self.ui_refs:
                self.ui_refs[ref_name].config(text=self._get_text(text_key))

        if "results_frame" in self.ui_refs:
            self.ui_refs["results_frame"].config(
                text=self._get_text("dashboard.results")
            )

        if hasattr(self, "results_tree"):
            self.results_tree.heading("Unit", text=self._get_text("unit.name"))
            self.results_tree.heading("Vaccine", text=self._get_text("vaccine.name"))
            self.results_tree.heading("Status", text=self._get_text("status.safe"))
            self.results_tree.heading("Decision", text=self._get_text("decision.pass"))

        if "status_bar" in self.ui_refs:
            self.status_var.set(self._get_text("status.ready"))

    # ========================== بناء الواجهة ==========================
    def _build_ui(self):
        self._build_header()
        self._build_menu()
        self._build_dashboard()
        self._build_status_bar()

    def _build_header(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.ui_refs["header"] = tk.Label(
            header_frame,
            text=self._get_text("app.title"),
            font=("Arial", 16, "bold"),
            bg="#f0f0f0",
        )
        self.ui_refs["header"].pack(pady=5)

        self.ui_refs["cycle_info"] = tk.Label(
            header_frame,
            text=f"Cycle ID: {self.cycle_id} | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            fg="gray",
            bg="#f0f0f0",
        )
        self.ui_refs["cycle_info"].pack(pady=5)

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label=self._get_text("menu.save_cycle"), command=self._save_cycle
        )
        file_menu.add_command(
            label=self._get_text("menu.load_cycle"), command=self._load_cycle
        )
        file_menu.add_separator()
        file_menu.add_command(
            label=self._get_text("menu.exit"), command=self._on_closing
        )
        menubar.add_cascade(label=self._get_text("menu.file"), menu=file_menu)

        # زر toggle للغة
        if LANG_AVAILABLE and lang and hasattr(lang, '_shape_arabic'):
            toggle_label = (
                "English"
                if self.current_lang == "ar"
                else lang._shape_arabic("عربي")
            )
        else:
            toggle_label = "English" if self.current_lang == "ar" else "عربي"
            
        target_lang = "en" if self.current_lang == "ar" else "ar"
        menubar.add_command(
            label=toggle_label, command=lambda: self._switch_lang(target_lang)
        )
        self.ui_refs["lang_toggle"] = menubar

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label=self._get_text("menu.about"), command=self._show_about
        )
        menubar.add_cascade(label=self._get_text("menu.help"), menu=help_menu)

        self.root.config(menu=menubar)
        self.ui_refs["menu"] = menubar

    def _build_dashboard(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.ui_refs["dashboard"] = frame

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)

        buttons = [
            ("btn_general", "dashboard.general_data", self._open_general_data),
            ("btn_units", "dashboard.units", self._open_units),
            ("btn_vaccines", "dashboard.vaccines", self._open_vaccines),
            ("btn_ft2", "dashboard.ft2_files", self._open_ft2_files),
        ]
        for ref, key, cmd in buttons:
            self.ui_refs[ref] = ttk.Button(
                btn_frame, text=self._get_text(key), command=cmd
            )
            self.ui_refs[ref].pack(side=tk.LEFT, padx=5)

        self.ui_refs["btn_verify"] = tk.Button(
            btn_frame,
            text=self._get_text("dashboard.verify"),
            command=self._verify,
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            relief=tk.RAISED,
            cursor="hand2",
        )
        self.ui_refs["btn_verify"].pack(side=tk.LEFT, padx=5)

        self.ui_refs["btn_generate"] = tk.Button(
            btn_frame,
            text=self._get_text("dashboard.generate_pdf"),
            command=self._generate_pdf,
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            activeforeground="white",
            relief=tk.RAISED,
            cursor="hand2",
        )
        self.ui_refs["btn_generate"].pack(side=tk.LEFT, padx=5)

        # إطار النتائج
        self.ui_refs["results_frame"] = ttk.LabelFrame(
            frame, text=self._get_text("dashboard.results")
        )
        self.ui_refs["results_frame"].pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("Unit", "Vaccine", "Status", "Decision")
        self.results_tree = ttk.Treeview(
            self.ui_refs["results_frame"],
            columns=columns,
            show="headings"
        )
        self.results_tree.heading("#0", text="ID")
        self.results_tree.heading("Unit", text=self._get_text("unit.name"))
        self.results_tree.heading("Vaccine", text=self._get_text("vaccine.name"))
        self.results_tree.heading("Status", text=self._get_text("status.safe"))
        self.results_tree.heading("Decision", text=self._get_text("decision.pass"))

        self.results_tree.column("#0", width=100)
        self.results_tree.column("Unit", width=150)
        self.results_tree.column("Vaccine", width=150)
        self.results_tree.column("Status", width=100)
        self.results_tree.column("Decision", width=100)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            self.ui_refs["results_frame"],
            orient=tk.VERTICAL,
            command=self.results_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value=self._get_text("status.ready"))
        self.ui_refs["status_bar"] = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#f0f0f0",
            fg="gray",
        )
        self.ui_refs["status_bar"].pack(side=tk.BOTTOM, fill=tk.X)

    # ========================== التعامل مع ملفات FT2 ==========================
    def _open_ft2_files(self):
        """فتح حوار اختيار ملفات FT2 مع قبول أي مسار وملفات PDF/TXT."""
        files = filedialog.askopenfilenames(
            title=self._get_text("dialog.select_ft2"),
            filetypes=[
                (self._get_text("filetype.txt"), "*.txt"),
                (self._get_text("filetype.pdf"), "*.pdf"),
                (self._get_text("filetype.all"), "*.*"),
            ],
        )
        if files:
            added = 0
            for file in files:
                path = Path(file).resolve()
                if path not in self.cycle_data["ft2_files"]:
                    self.cycle_data["ft2_files"].append(path)
                    added += 1
            self.status_var.set(f"{added} {self._get_text('msg.files_added')}")
            messagebox.showinfo(
                self._get_text("msg.success"),
                f"{added} {self._get_text('msg.files_added')}",
            )

    # ========================== توليد التقرير ==========================
    def _generate_pdf(self):
        """توليد تقرير لكل جهاز أو تقرير كامل للدورة مع دعم فلترة حسب فترة زمنية."""
        if not self.cycle_data["ft2_files"]:
            messagebox.showwarning(
                self._get_text("msg.warning"), self._get_text("msg.no_ft2_files")
            )
            return

        if not COMPOSER_AVAILABLE or not AppComposer:
            messagebox.showerror(self._get_text("error.title"), "AppComposer غير متوفر")
            return

        # استيراد محلي لتجنب الاعتماديات غير الضرورية
        try:
            from src.application.use_cases.generate_device_report_uc import (
                GenerateDeviceReportRequest,
            )
        except ImportError:
            messagebox.showerror(
                self._get_text("error.title"), 
                "GenerateDeviceReportRequest غير متوفر"
            )
            return

        try:
            use_case = AppComposer.create_generate_device_report_uc()
            repository = getattr(use_case, "_repo", None)
            if repository is None:
                # fallback to direct instantiation if composer doesn't expose it
                if REPO_AVAILABLE:
                    from src.infrastructure.repositories.device_repository import DeviceDataRepository
                    repository = DeviceDataRepository()
                else:
                    messagebox.showerror(
                        self._get_text("error.title"),
                        "DeviceDataRepository غير متوفر"
                    )
                    return

            choice = messagebox.askquestion(
                self._get_text("dashboard.generate_pdf"),
                "هل تريد تقرير لكل جهاز؟ (نعم) أم تقرير كامل للدورة؟ (لا)",
            )

            output_dir = Path("data/output/reports")
            output_dir.mkdir(parents=True, exist_ok=True)

            if choice == "yes":
                device_id = simpledialog.askstring(
                    self._get_text("dashboard.generate_pdf"), "أدخل معرف الجهاز:"
                )
                if not device_id:
                    return

                request = GenerateDeviceReportRequest(device_id=device_id)
                use_case.execute(request)

                report_filename = f"{self.cycle_id}_{device_id}_report.pdf"
                report_path = output_dir / report_filename
                self.cycle_data["reports_generated"].append(str(report_path))
                messagebox.showinfo(
                    self._get_text("msg.success"), f"تم إنشاء التقرير: {report_path}"
                )
            else:
                date_from_str = simpledialog.askstring(
                    self._get_text("dashboard.generate_pdf"),
                    "أدخل تاريخ البداية (YYYY-MM-DD) أو اتركه فارغاً:",
                )
                date_to_str = simpledialog.askstring(
                    self._get_text("dashboard.generate_pdf"),
                    "أدخل تاريخ النهاية (YYYY-MM-DD) أو اتركه فارغاً:",
                )

                date_from = None
                if date_from_str:
                    try:
                        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showerror(
                            self._get_text("error.title"),
                            self._get_text("error.invalid_date"),
                        )
                        return

                date_to = None
                if date_to_str:
                    try:
                        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showerror(
                            self._get_text("error.title"),
                            self._get_text("error.invalid_date"),
                        )
                        return

                if date_from and date_to and date_to < date_from:
                    messagebox.showerror(
                        self._get_text("error.title"),
                        "تاريخ النهاية يجب أن يكون بعد تاريخ البداية",
                    )
                    return

                if not hasattr(repository, 'get_all_device_ids'):
                    messagebox.showerror(
                        self._get_text("error.title"),
                        "Repository لا يدعم get_all_device_ids"
                    )
                    return

                all_device_ids = repository.get_all_device_ids(
                    date_from=date_from, date_to=date_to
                )

                if not all_device_ids:
                    messagebox.showinfo(
                        self._get_text("msg.info"), "لا توجد أجهزة ضمن الفترة المحددة"
                    )
                    return

                reports_count = 0
                for device_id in all_device_ids:
                    try:
                        request = GenerateDeviceReportRequest(
                            device_id=device_id, date_from=date_from, date_to=date_to
                        )
                        use_case.execute(request)

                        suffix = (
                            f"_{date_from_str or 'start'}_{date_to_str or 'end'}"
                            if (date_from_str or date_to_str)
                            else ""
                        )
                        report_filename = (
                            f"{self.cycle_id}_{device_id}{suffix}_report.pdf"
                        )
                        report_path = output_dir / report_filename

                        self.cycle_data["reports_generated"].append(str(report_path))
                        reports_count += 1
                    except Exception as e:
                        logger.error(f"فشل توليد تقرير للجهاز {device_id}: {e}")
                        continue

                messagebox.showinfo(
                    self._get_text("msg.success"),
                    f"تم إنشاء {reports_count} من {len(all_device_ids)} تقرير",
                )

            self._save_cycle()
            self.status_var.set(self._get_text("status.ready"))

        except Exception as e:
            logger.exception("فشل توليد التقرير")
            messagebox.showerror(
                self._get_text("error.title"),
                f"{self._get_text('error.pdf_generation_failed')}: {str(e)}",
            )
            self.status_var.set(self._get_text("status.error"))

    # ========================== حفظ/تحميل الدورة ==========================
    def _save_cycle(self):
        try:
            output_dir = Path("data/output/cycles")
            output_dir.mkdir(parents=True, exist_ok=True)
            cycle_file = output_dir / f"{self.cycle_id}.json"
            with open(cycle_file, "w", encoding="utf-8") as f:
                json.dump(self.cycle_data, f, indent=2, ensure_ascii=False)
            self.status_var.set(self._get_text("msg.cycle_saved"))
        except Exception as e:
            messagebox.showerror(self._get_text("error.title"), str(e))

    def _load_cycle(self):
        file = filedialog.askopenfilename(
            title=self._get_text("dialog.load_cycle"),
            filetypes=[(self._get_text("filetype.json"), "*.json")],
        )
        if file:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    self.cycle_data = json.load(f)
                    self.cycle_id = self.cycle_data["cycle_id"]
                messagebox.showinfo(
                    self._get_text("msg.success"), self._get_text("msg.cycle_loaded")
                )
            except Exception as e:
                messagebox.showerror(self._get_text("error.title"), str(e))

    # ========================== أزرار مساعدة ==========================
    def _open_general_data(self):
        messagebox.showinfo(
            self._get_text("dashboard.general_data"),
            self._get_text("msg.feature_coming_soon"),
        )

    def _open_units(self):
        messagebox.showinfo(
            self._get_text("dashboard.units"), self._get_text("msg.feature_coming_soon")
        )

    def _open_vaccines(self):
        messagebox.showinfo(
            self._get_text("dashboard.vaccines"),
            self._get_text("msg.feature_coming_soon"),
        )

    def _verify(self):
        messagebox.showinfo(
            self._get_text("dashboard.verify"),
            self._get_text("msg.feature_coming_soon"),
        )

    def _show_about(self):
        messagebox.showinfo(
            self._get_text("menu.about"),
            f"CCI-FT2 Intelligence\nVersion: v1.0.0-Production-Trial\n\n{self._get_text('msg.copyright')}",
        )

    def _on_closing(self):
        title = self._get_text("msg.quit")
        msg = self._get_text("msg.quit_confirm")
        if messagebox.askokcancel(title, msg):
            self._save_cycle()
            self.root.destroy()
            os.kill(os.getpid(), signal.SIGKILL)

    # ========================== تشغيل ==========================
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = GuardianGUI()
    app.run()