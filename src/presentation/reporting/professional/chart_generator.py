import base64
import io
import os
from pathlib import Path
from typing import List, Optional

os.environ.setdefault("MPLCONFIGDIR", "/tmp/.matplotlib")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
from src.application.dtos.reading_dto import ReadingDTO

class ReportChartGenerator:
    def generate_temperature_timeline(self, readings: List[ReadingDTO]) -> Optional[str]:
        if not readings or len(readings) < 2:
            return None

        times = [r.timestamp for r in readings]
        temps = [float(r.temperature) for r in readings]

        plt.figure(figsize=(10, 4))
        plt.plot(times, temps, marker="o", linestyle="-", color="#1e40af", linewidth=2.4)
        plt.title("Temperature Timeline")
        plt.xlabel("Time")
        plt.ylabel("Temperature (°C)")
        plt.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
        plt.close()
        buf.seek(0)

        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"

    def generate_stability_budget_bar(self, consumed_pct: float) -> Optional[str]:
        """
        توليد رسم بياني شريطي يوضح الميزانية المستهلكة للاستقرار الحراري.
        يعيد الصورة بصيغة Base64 لتضمينها في الـ HTML.
        """
        try:
            import matplotlib.pyplot as plt
            import io
            import base64

            plt.figure(figsize=(6, 1))
            
            # تحديد اللون بناءً على الاستهلاك
            color = 'green' if consumed_pct < 50 else ('orange' if consumed_pct < 80 else 'red')
            
            plt.barh([0], [consumed_pct], color=color, height=0.5)
            plt.barh([0], [100], color='lightgray', height=0.5, zorder=0) # الخلفية
            
            plt.xlim(0, 100)
            plt.yticks([])
            plt.xlabel('Stability Budget Consumed (%)')
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
            plt.close()
            buf.seek(0)
            
            return base64.b64encode(buf.read()).decode('utf-8')
        except Exception as e:
            print(f"Warning: Failed to generate stability bar chart: {e}")
            return None
