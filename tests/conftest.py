# tests/conftest.py
import sys
from pathlib import Path
import pytest

# إضافة مسار src للمشاريع
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def sample_device_data():
    """بيانات جهاز عينة للاختبار"""
    return {
        'device_id': 'DEV_001',
        'center_id': 'CTR_001',
        'center_name': 'مستشفى الاختبار',
        'temperature_ranges': {'min': 2.0, 'max': 8.0},
    }


@pytest.fixture
def sample_report_dto():
    """DTO تقرير عينة"""
    from src.application.dtos.device_report_dto import DeviceReportDTO, ReportDecision, VVMStage
    return {
        'device_id': 'DEV_001',
        'center_id': 'CTR_001',
        'center_name': 'Test',
        'temperature_ranges': {'min': 2.0, 'max': 8.0},
        'decision': ReportDecision.ACCEPTED,
        'vvm_stage': VVMStage.A
    }


@pytest.fixture(scope="session")
def weasyprint_config():
    """إعدادات WeasyPrint الموحدة للاختبارات."""
    return {
        'presentational_hints': True,
        'hyphenate': False,
        'font_config': {
            'Tajawal': {
                'normal': '/usr/share/fonts/truetype/tajawal/Tajawal-Regular.ttf',
                'bold': '/usr/share/fonts/truetype/tajawal/Tajawal-Bold.ttf',
            }
        }
    }


@pytest.fixture
def sample_vaccine_freeze_sensitive():
    """عينة لقاح حساس للتجميد"""
    return {
        'code': 'HEPB',
        'name_ar': 'التهاب الكبد B',
        'name_en': 'Hepatitis B',
        'category': 'freeze-sensitive',
        'vvm_type': 'VVM14',
        'storage_temp': '+2°C إلى +8°C'
    }


@pytest.fixture
def sample_readings_stable():
    """قراءات حرارة ضمن النطاق الآمن"""
    return [
        {'timestamp': '2025-01-01T08:00:00Z', 'temperature': 4.2},
        {'timestamp': '2025-01-01T09:00:00Z', 'temperature': 4.8},
        {'timestamp': '2025-01-01T10:00:00Z', 'temperature': 5.1},
    ]


@pytest.fixture
def temp_pdf_output(tmp_path):
    """مسار مؤقت لمخرجات PDF"""
    return tmp_path / 'test_report.pdf'


# تخطي تلقائي للاختبارات المؤرشة

def pytest_collection_modifyitems(config, items):
    for item in items:
        if 'archive_reportlab_legacy' in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason='مؤرشف: تم الانتقال إلى WeasyPrint'))
