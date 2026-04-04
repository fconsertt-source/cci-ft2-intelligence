# دليل النشر والتوزيع

## متطلبات النظام

- Python 3.12+
- PostgreSQL 13+
- Docker & Docker Compose
- 4GB RAM minimum
- 10GB disk space

## خطوات النشر

### 1. إعداد البيئة
```bash
git clone <repository>
cd cci-ft2-intelligence-clean
cp config/base.yaml config/production.yaml
# تعديل production.yaml حسب البيئة
```

### 2. تشغيل عبر Docker
```bash
docker-compose up -d
```

### 3. تشغيل يدوياً
```bash
pip install -r requirements.txt
export CCI_ENV=production
python -m src.presentation.cli.main
```

## متغيرات البيئة

- `CCI_ENV`: production/development
- `CCI_DATA_ROOT`: مسار بيانات النظام
- `CCI_LOG_LEVEL`: مستوى التسجيل

## نقاط النهاية

- `/health`: فحص الصحة
- `/metrics`: المقاييس (Prometheus)
- `/api/v1/reports`: API التقارير