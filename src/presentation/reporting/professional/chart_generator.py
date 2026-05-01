import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from pathlib import Path

from src.shared.language_manager import lang


class ReportChartGenerator:
    """توليد الرسوم البيانية للتقارير"""

    def __init__(self):
        self.output_dir = Path("data/output/reports/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_temperature_timeline(self, readings, filename="temp_timeline.png"):
        """خط زمني لدرجة الحرارة"""
        if not readings or len(readings) < 2:
            return None

        times = [r.timestamp for r in readings]
        temps = [float(r.temperature) for r in readings]

        plt.figure(figsize=(10, 4))
        plt.plot(times, temps, marker="o", linestyle="-", color="#1e40af", linewidth=2.4)
        plt.axhline(y=8, color="#dc2626", linestyle="--", alpha=0.7, label=lang.get("chart.temp_max"))
        plt.axhline(y=2, color="#2563eb", linestyle="--", alpha=0.7, label=lang.get("chart.temp_min"))

        plt.title(lang.get("chart.temp_title"), fontsize=14, pad=14)
        plt.xlabel(lang.get("chart.temp_y_label"))
        plt.ylabel(lang.get("chart.temp_y_label"))
        plt.grid(True, alpha=0.25)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
        plt.xticks(rotation=40, ha="right")
        plt.legend(fontsize=8)
        plt.tight_layout()

        path = self.output_dir / filename
        plt.savefig(path, dpi=200, bbox_inches="tight")
        plt.close()
        return str(path)

    def generate_stability_budget_bar(self, stability_pct, filename="stability_budget.png"):
        """مخطط شريطي لميزانية الاستقرار"""
        plt.figure(figsize=(8, 3.2))
        color = "#16a34a" if stability_pct < 50 else "#eab308" if stability_pct < 75 else "#dc2626"

        plt.barh([lang.get("report.stability_budget")], [stability_pct], color=color, height=0.6)
        plt.xlim(0, 100)
        plt.xlabel(lang.get("report.stability_budget"))
        plt.title(lang.get("report.stability_budget"), fontsize=14)
        plt.gca().invert_yaxis()
        plt.gca().xaxis.set_major_locator(plt.MultipleLocator(20))
        plt.gca().xaxis.grid(True, linestyle="--", alpha=0.3)
        plt.gca().spines["top"].set_visible(False)
        plt.gca().spines["right"].set_visible(False)
        plt.gca().spines["left"].set_visible(False)
        plt.gca().spines["bottom"].set_color("#cbd5e1")

        plt.text(stability_pct + 2.5, 0, f"{stability_pct:.1f}%", va="center", fontsize=11, fontweight="bold")
        plt.tight_layout()

        path = self.output_dir / filename
        plt.savefig(path, dpi=200, bbox_inches="tight")
        plt.close()
        return str(path)
