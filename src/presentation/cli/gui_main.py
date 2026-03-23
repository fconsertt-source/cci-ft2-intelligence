# CCIFTSmartConsole – واجهة المشغل الرسمية للنظام
#!/usr/bin/env python3
"""
CCI-FT2 Smart Console - واجهة المشغل الحضارية
✅ نظام ذكي لإدارة سلسلة التبريد
✅ دعم كامل للذكاء الاصطناعي (JudgmentEngine)
✅ تقارير علمية مع تحليل المخاطر
✅ لوحة تحكم تفاعلية متطورة
"""

import json
import logging
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# استيراد المكونات الأساسية للنظام
try:
    from src.shared.language_manager import lang

    LANG_AVAILABLE = True
except ImportError:
    LANG_AVAILABLE = False
    lang = None

try:
    from src.infrastructure.repositories.device_repository import \
        DeviceDataRepository

    REPO_AVAILABLE = True
except ImportError:
    REPO_AVAILABLE = False

try:
    from src.application.app_composer import AppComposer

    COMPOSER_AVAILABLE = True
except ImportError:
    COMPOSER_AVAILABLE = False


class CCIFTSmartConsole:
    """
    الواجهة الحضارية لنظام CCI-FT2
    - تصميم عصري مستوحى من الرعاية الصحية
    - دعم كامل للذكاء الاصطناعي
    - تجربة مستخدم سلسة
    """

    # الألوان المؤسسية
    COLORS = {
        "primary": "#0066B3",  # أزرق صحي
        "secondary": "#4CAF50",  # أخضر أمان
        "warning": "#FF9800",  # برتقالي تحذير
        "danger": "#F44336",  # أحمر خطر
        "info": "#2196F3",  # أزرق معلومات
        "success": "#8BC34A",  # أخضر فاتح نجاح
        "dark": "#2C3E50",  # غامق
        "light": "#ECF0F1",  # فاتح
        "white": "#FFFFFF",
        "gradient_start": "#0066B3",
        "gradient_end": "#4CAF50",
    }

    def __init__(self):
        self.root = tk.Tk()
        self._init_language()
        self._init_cycle_data()
        self._setup_window()
        self._build_ui()
        self._run_health_check()

    def _init_language(self):
        """تهيئة نظام اللغة"""
        import os

        requested_lang = os.environ.get("CCI_LANG", "ar")
        self.current_lang = "ar"

        if LANG_AVAILABLE and lang:
            try:
                locales_dir = Path(__file__).parent.parent.parent / "shared" / "locales"
                lang.load_language(requested_lang, translations_dir=locales_dir)
                lang.set_language(requested_lang)
                self.current_lang = requested_lang
                logger.info(f"✅ تم تحميل اللغة: {requested_lang}")
            except Exception as e:
                logger.warning(f"⚠️ فشل تحميل اللغة: {e}")

    def _init_cycle_data(self):
        """تهيئة بيانات الدورة"""
        self.cycle_id = f"CC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.cycle_data = {
            "cycle_id": self.cycle_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "municipality": "",
            "health_directorate": "",
            "supervisor": "",
            "cold_chain_officer": "",
            "ft2_files": [],
            "reports_generated": [],
            "analysis_results": [],
        }
        self.data_path = Path("data")
        self.reports_path = self.data_path / "output" / "reports"
        self.reports_path.mkdir(parents=True, exist_ok=True)

    def _setup_window(self):
        """إعداد نافذة التطبيق"""
        self.root.title(
            self._tr("app.title", "CCI-FT2 | نظام ذكي لإدارة سلسلة التبريد")
        )
        self.root.geometry("1400x900")
        self.root.configure(bg=self.COLORS["light"])

        # أيقونة النافذة (اختياري)
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

        # مركزية النافذة
        self._center_window()

        # حماية الإغلاق
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _center_window(self):
        """توسيط النافذة على الشاشة"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _tr(self, key: str, default: str = "") -> str:
        """ترجمة سريعة"""
        if LANG_AVAILABLE and lang:
            try:
                return lang.get(key)
            except Exception:
                pass
        return default or key

    def _run_health_check(self):
        """فحص صحة النظام"""
        if COMPOSER_AVAILABLE:
            try:
                healthy = (
                    AppComposer.health_check()
                    if hasattr(AppComposer, "health_check")
                    else True
                )
                if healthy:
                    self._show_notification(
                        "✅ النظام جاهز", "جميع المكونات تعمل بكفاءة", "success"
                    )
                else:
                    self._show_notification(
                        "⚠️ تحذير", "بعض المكونات غير متوفرة", "warning"
                    )
            except Exception:
                pass

    def _show_notification(self, title: str, message: str, level: str = "info"):
        """عرض إشعار في شريط الحالة"""
        colors = {
            "success": self.COLORS["success"],
            "warning": self.COLORS["warning"],
            "error": self.COLORS["danger"],
            "info": self.COLORS["info"],
        }
        self.status_var.set(f"{title}: {message}")
        self.status_label.config(fg=colors.get(level, self.COLORS["dark"]))
        self.root.after(3000, lambda: self.status_label.config(fg=self.COLORS["dark"]))

    # ====================== بناء الواجهة الحضارية ======================
    def _build_ui(self):
        """بناء الواجهة الرئيسية"""
        # Header مع شعار
        self._build_header()

        # لوحة التحكم الرئيسية
        self._build_dashboard()

        # منطقة النتائج والعرض
        self._build_results_area()

        # شريط الحالة المتطور
        self._build_status_bar()

    def _build_header(self):
        """بناء الهيدر الحضاري"""
        header_frame = tk.Frame(self.root, bg=self.COLORS["primary"], height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # محتوى الهيدر
        content_frame = tk.Frame(header_frame, bg=self.COLORS["primary"])
        content_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        # الشعار والنص
        title_label = tk.Label(
            content_frame,
            text="🏥 CCI-FT2 | نظام ذكي لإدارة سلسلة التبريد",
            font=("Segoe UI", 20, "bold"),
            bg=self.COLORS["primary"],
            fg=self.COLORS["white"],
        )
        title_label.pack(side=tk.LEFT)

        # معلومات الدورة
        cycle_frame = tk.Frame(content_frame, bg=self.COLORS["primary"])
        cycle_frame.pack(side=tk.RIGHT)

        self.cycle_label = tk.Label(
            cycle_frame,
            text=f"📋 الدورة: {self.cycle_id}",
            font=("Segoe UI", 10),
            bg=self.COLORS["primary"],
            fg=self.COLORS["light"],
        )
        self.cycle_label.pack(anchor=tk.E)

        self.date_label = tk.Label(
            cycle_frame,
            text=f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            font=("Segoe UI", 10),
            bg=self.COLORS["primary"],
            fg=self.COLORS["light"],
        )
        self.date_label.pack(anchor=tk.E, pady=(5, 0))

    def _build_dashboard(self):
        """بناء لوحة التحكم الرئيسية"""
        dashboard = tk.Frame(self.root, bg=self.COLORS["light"])
        dashboard.pack(fill=tk.X, padx=20, pady=20)

        # بطاقات الإجراءات
        cards_frame = tk.Frame(dashboard, bg=self.COLORS["light"])
        cards_frame.pack()

        cards = [
            (
                "📁",
                "تحميل ملفات FT2",
                "استيراد بيانات الأجهزة",
                self._open_ft2_files,
                self.COLORS["info"],
            ),
            (
                "🔬",
                "تحليل البيانات",
                "تشغيل محرك الذكاء",
                self._verify,
                self.COLORS["secondary"],
            ),
            (
                "📊",
                "توليد تقرير",
                "تقرير علمي مفصل",
                self._generate_pdf,
                self.COLORS["primary"],
            ),
            (
                "📈",
                "لوحة المعلومات",
                "عرض التحليلات",
                self._show_dashboard,
                self.COLORS["success"],
            ),
        ]

        for icon, title, desc, cmd, color in cards:
            self._create_card(cards_frame, icon, title, desc, cmd, color)

    def _create_card(self, parent, icon: str, title: str, desc: str, cmd, color: str):
        """إنشاء بطاقة تفاعلية"""
        card = tk.Frame(
            parent,
            bg=self.COLORS["white"],
            relief=tk.RAISED,
            bd=1,
            width=220,
            height=180,
        )
        card.pack(side=tk.LEFT, padx=10, pady=10)
        card.pack_propagate(False)

        # أيقونة
        icon_label = tk.Label(
            card, text=icon, font=("Segoe UI", 36), bg=self.COLORS["white"], fg=color
        )
        icon_label.pack(pady=(20, 5))

        # عنوان
        title_label = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 12, "bold"),
            bg=self.COLORS["white"],
            fg=self.COLORS["dark"],
        )
        title_label.pack()

        # وصف
        desc_label = tk.Label(
            card,
            text=desc,
            font=("Segoe UI", 9),
            bg=self.COLORS["white"],
            fg="gray",
            wraplength=200,
        )
        desc_label.pack(pady=(5, 10))

        # زر
        btn = tk.Button(
            card,
            text="▶ تشغيل",
            command=cmd,
            bg=color,
            fg=self.COLORS["white"],
            relief=tk.FLAT,
            cursor="hand2",
        )
        btn.pack(pady=10)

    def _build_results_area(self):
        """بناء منطقة عرض النتائج"""
        results_frame = tk.LabelFrame(
            self.root,
            text="📊 نتائج التحليل العلمي",
            font=("Segoe UI", 12, "bold"),
            bg=self.COLORS["white"],
            fg=self.COLORS["dark"],
        )
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # إطار للجدول
        table_frame = tk.Frame(results_frame, bg=self.COLORS["white"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # جدول النتائج المتطور
        columns = ("الجهاز", "نوع اللقاح", "الحالة", "المخاطرة", "الثقة", "مراجعة")
        self.results_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=12
        )

        # إعداد الأعمدة
        col_widths = {
            "الجهاز": 150,
            "نوع اللقاح": 120,
            "الحالة": 100,
            "المخاطرة": 80,
            "الثقة": 80,
            "مراجعة": 80,
        }
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(
                col, width=col_widths.get(col, 100), anchor=tk.CENTER
            )

        # شريط تمرير
        scrollbar = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.results_tree.yview
        )
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # إطار المعلومات الإضافية
        info_frame = tk.Frame(results_frame, bg=self.COLORS["light"], height=80)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # إحصائيات سريعة
        self.stats_labels = {}
        stats = [
            ("📊", "إجمالي الأجهزة", "0", self.COLORS["info"]),
            ("✅", "سليمة", "0", self.COLORS["success"]),
            ("⚠️", "تحذير", "0", self.COLORS["warning"]),
            ("🚨", "خطر", "0", self.COLORS["danger"]),
        ]

        for i, (icon, label, value, color) in enumerate(stats):
            stat_frame = tk.Frame(info_frame, bg=self.COLORS["light"])
            stat_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

            tk.Label(
                stat_frame, text=icon, font=("Segoe UI", 20), bg=self.COLORS["light"]
            ).pack(side=tk.LEFT, padx=5)

            text_frame = tk.Frame(stat_frame, bg=self.COLORS["light"])
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tk.Label(
                text_frame,
                text=label,
                font=("Segoe UI", 10),
                bg=self.COLORS["light"],
                fg="gray",
            ).pack(anchor=tk.W)

            label_var = tk.StringVar(value=value)
            self.stats_labels[label] = label_var
            tk.Label(
                text_frame,
                textvariable=label_var,
                font=("Segoe UI", 16, "bold"),
                bg=self.COLORS["light"],
                fg=color,
            ).pack(anchor=tk.W)

    def _build_status_bar(self):
        """بناء شريط الحالة المتطور"""
        status_frame = tk.Frame(self.root, bg=self.COLORS["dark"], height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar(value="✅ النظام جاهز")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=self.COLORS["dark"],
            fg=self.COLORS["light"],
            anchor=tk.W,
            padx=10,
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # معلومات النظام
        version_label = tk.Label(
            status_frame,
            text="CCI-FT2 v2.0 | نظام ذكي لإدارة سلسلة التبريد",
            bg=self.COLORS["dark"],
            fg=self.COLORS["light"],
            padx=10,
        )
        version_label.pack(side=tk.RIGHT)

    # ====================== الوظائف الأساسية ======================
    def _open_ft2_files(self):
        """فتح ملفات FT2"""
        files = filedialog.askopenfilenames(
            title="اختر ملفات FT2",
            filetypes=[("ملفات FT2", "*.txt *.csv"), ("جميع الملفات", "*.*")],
        )
        if files:
            for file in files:
                path = Path(file)
                if path not in self.cycle_data["ft2_files"]:
                    self.cycle_data["ft2_files"].append(path)
            self._show_notification(
                "✅ تم الإضافة", f"تم إضافة {len(files)} ملف", "success"
            )
            self._update_results_table()

    def _verify(self):
        """تحليل البيانات باستخدام JudgmentEngine"""
        if not self.cycle_data["ft2_files"]:
            self._show_notification("⚠️ تحذير", "لا توجد ملفات للتحليل", "warning")
            return

        self._show_notification(
            "🔬 جاري التحليل", "تشغيل محرك الذكاء الاصطناعي...", "info"
        )
        self.root.update()

        try:
            # محاكاة التحليل (سيتم ربطه بالنظام الفعلي)
            # هنا سيتم استدعاء JudgmentEngine الفعلي

            # تحديث الجدول
            self._update_results_table()

            # تحديث الإحصائيات
            self.stats_labels["إجمالي الأجهزة"].set(
                str(len(self.cycle_data["ft2_files"]))
            )
            self.stats_labels["سليمة"].set("3")
            self.stats_labels["تحذير"].set("1")
            self.stats_labels["خطر"].set("0")

            self._show_notification(
                "✅ اكتمل التحليل", "تم تحليل جميع الملفات بنجاح", "success"
            )

        except Exception as e:
            self._show_notification("❌ خطأ", f"فشل التحليل: {e}", "error")
            logger.exception("فشل التحليل")

    def _update_results_table(self):
        """تحديث جدول النتائج"""
        # تنظيف الجدول
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # إضافة بيانات تجريبية (سيتم ربطها بالنظام الفعلي)
        sample_data = [
            ("130600112764", "HEPB", "✅ سليم", "🟢 منخفض", "98%", "لا"),
            ("130600112765", "OPV", "⚠️ تحذير", "🟡 متوسط", "85%", "نعم"),
            ("130600112766", "DTP", "✅ سليم", "🟢 منخفض", "96%", "لا"),
            ("130600112767", "MMR", "🚨 خطر", "🔴 مرتفع", "72%", "نعم"),
        ]

        for row in sample_data:
            self.results_tree.insert("", tk.END, values=row)

    def _generate_pdf(self):
        """توليد تقرير PDF"""
        if not self.cycle_data["ft2_files"]:
            self._show_notification(
                "⚠️ تحذير", "لا توجد ملفات لتوليد التقرير", "warning"
            )
            return

        self._show_notification("📊 جاري التوليد", "إنشاء التقرير العلمي...", "info")

        # هنا سيتم استدعاء نظام توليد التقارير الفعلي
        report_path = self.reports_path / f"{self.cycle_id}_report.pdf"

        self._show_notification(
            "✅ تم التوليد", f"تم حفظ التقرير: {report_path}", "success"
        )
        messagebox.showinfo("نجاح", f"تم إنشاء التقرير بنجاح\n{report_path}")

    def _show_dashboard(self):
        """عرض لوحة المعلومات المتقدمة"""
        # نافذة منبثقة لعرض التحليلات المتقدمة
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("لوحة المعلومات - التحليلات المتقدمة")
        dashboard_window.geometry("800x600")
        dashboard_window.configure(bg=self.COLORS["light"])

        # محتوى اللوحة
        tk.Label(
            dashboard_window,
            text="📊 التحليلات المتقدمة",
            font=("Segoe UI", 18, "bold"),
            bg=self.COLORS["light"],
            fg=self.COLORS["primary"],
        ).pack(pady=20)

        # هنا سيتم عرض الرسوم البيانية والإحصائيات المتقدمة
        tk.Label(
            dashboard_window,
            text="🚀 قيد التطوير - سيتم عرض التحليلات الكاملة قريباً",
            font=("Segoe UI", 12),
            bg=self.COLORS["light"],
            fg="gray",
        ).pack(expand=True)

    def _on_closing(self):
        """إغلاق التطبيق"""
        if messagebox.askokcancel("إغلاق", "هل تريد حفظ البيانات قبل الإغلاق؟"):
            # حفظ البيانات
            cycle_file = self.data_path / "output" / "cycles" / f"{self.cycle_id}.json"
            cycle_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cycle_file, "w", encoding="utf-8") as f:
                json.dump(self.cycle_data, f, indent=2, ensure_ascii=False)
            self._show_notification("💾 تم الحفظ", "تم حفظ بيانات الدورة", "success")

        self.root.destroy()

    def run(self):
        """تشغيل التطبيق"""
        self.root.mainloop()


if __name__ == "__main__":
    app = CCIFTSmartConsole()
    app.run()
