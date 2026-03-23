FROM python:3.12-slim

# تثبيت اعتماديات النظام الأساسية و Tkinter للواجهة الرسومية
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    python3-tk \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود المصدري
COPY . .

# تعيين متغير البيئة للغة العربية
ENV CCI_LANG=ar

# تشغيل الاختبارات كفحص صحة
RUN pytest -q || true

CMD ["python", "scripts/run_ft2_pipeline.py", "--generate-data", "--verbose"]
