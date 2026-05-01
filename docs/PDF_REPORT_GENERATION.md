# PDF Report Generation - Clean Architecture Implementation

## Overview

The PDF report generation system has been refactored to follow Clean Architecture principles, transitioning from ReportLab to WeasyPrint for better Arabic support and maintainability.

## Architecture

### Application Layer
- **Port**: `IPDFReportGenerator` (`src/application/ports/i_pdf_report_generator.py`)
- **Use Case**: `GeneratePDFReportUseCase` (`src/application/use_cases/generate_pdf_report_uc.py`)

### Infrastructure Layer
- **Adapter**: `PDFGenerator` (`src/infrastructure/adapters/reporting/new_pdf_engine.py`)
- **Wrapper**: `UnifiedPDFGeneratorWrapper` (for backward compatibility)

### Presentation Layer
- **Templates**: HTML/CSS templates in `src/presentation/reporting/professional/templates/`
- **Charts**: Matplotlib-based chart generation in `src/presentation/reporting/professional/chart_generator.py`

## Usage

### Recommended: Clean Architecture Approach

```python
from src.application.app_composer import AppComposer
from src.application.dtos.device_report_dto import DeviceReportDTO

# Create Use Case
pdf_uc = AppComposer.create_generate_pdf_report_uc()

# Generate PDF
pdf_bytes = pdf_uc.execute_device_report(dto, report_type="official", language="ar")
```

### Legacy: Direct Adapter Usage

```python
from src.infrastructure.adapters.reporting.new_pdf_engine import PDFGenerator

generator = PDFGenerator()
pdf_bytes = generator.generate(dto, report_type="official", language="ar")
```

## Visual Test Models

The system uses models from `data/output/visual_tests/` to ensure reports match design specifications:

- `mock_visual_data.tsv`: Test data for different decision scenarios
- `visual_test_arabic.pdf`: Arabic report reference
- `visual_test_official.pdf`: Official report reference
- `visual_test_tech.pdf`: Technical report reference

### Test Data Structure

| Field | Description |
|-------|-------------|
| center_id | Center identifier |
| center_name | Center display name |
| decision | ACCEPTED/REJECTED/PARTIAL |
| alert_level | GREEN/YELLOW/RED |
| vvm_stage | NONE/STAGE_A/STAGE_B/etc |
| stability_budget_consumed_pct | Percentage used |
| category_display | Vaccine category |

## Report Types

1. **Official**: Formal reports with signatures
2. **Technical**: Detailed technical data
3. **Arabic**: Arabic language support

## Features

- ✅ Full Arabic RTL support with proper shaping
- ✅ Professional charts (Temperature Timeline, Stability Budget)
- ✅ Clean separation of concerns
- ✅ Template-based design for easy customization
- ✅ DTO-driven data flow
- ✅ Backward compatibility

## Migration Guide

### From Legacy ReportLab

1. Replace direct `ProfessionalVaccineReport` usage with `GeneratePDFReportUseCase`
2. Convert data dictionaries to `DeviceReportDTO` objects
3. Use `AppComposer.create_generate_pdf_report_uc()` for instantiation

### Example Migration

**Before:**
```python
report_generator = ProfessionalVaccineReport()
pdf_path = report_generator.generate_vaccine_a4(context, readings)
```

**After:**
```python
pdf_uc = AppComposer.create_generate_pdf_report_uc()
pdf_bytes = pdf_uc.execute_device_report(dto)
```

## Testing

Run tests with:
```bash
pytest tests/unit/test_new_pdf_engine.py
pytest tests/unit/test_unified_pdf_generator_wrapper.py
```

## Future Enhancements

- Center-level summary reports
- QR code integration
- Multi-language support beyond Arabic/English
- Advanced chart types