# infrastructure/security/pdf_structural_extractor.py
"""استخراج القيم السيادية من تقارير Berlinger PDF للمقارنة مع ملفات TXT الموقعة"""

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

import hashlib
import re
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from pathlib import Path
from typing import List

from domain.evidence.pdf_extraction_result import PDFExtractionResult
from domain.exceptions.license_exceptions import ExtractionError

logger = logging.getLogger(__name__)


class PDFStructuralExtractor:
    """استخراج القيم الأساسية من تقرير Berlinger PDF"""
    
    def extract(self, pdf_path: Path) -> PDFExtractionResult:
        """
        استخراج البيانات الأساسية من تقرير PDF
        
        Args:
            pdf_path: مسار ملف PDF
            
        Returns:
            PDFExtractionResult يحتوي على القيم السيادية
            
        Raises:
            RuntimeError: إذا لم تكن مكتبة PyMuPDF مثبتة
            ExtractionError: إذا فشل الاستخراج لأي سبب
        """
        # التحقق المبكر من توفر المكتبة
        if fitz is None:
            raise RuntimeError(
                "PyMuPDF is required for PDF extraction. "
                "Install with: pip install PyMuPDF"
            )
        
        if not pdf_path.exists():
            raise ExtractionError(f"الملف غير موجود: {pdf_path}")
        
        logger.info(f"بدء استخراج البيانات من: {pdf_path.name}")
        
        # 1. حساب الهاش للملف الأصلي
        pdf_hash = self._calculate_hash(pdf_path)
        logger.debug(f"هاش الملف (SHA256): {pdf_hash[:16]}...")
        
        # 2. فتح المستند
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise ExtractionError(f"فشل فتح ملف PDF: {e}")
        
        logger.info(f"تم فتح المستند - عدد الصفحات: {len(doc)}")
        
        # 3. استخراج النص الكامل
        full_text = self._extract_full_text(doc)
        logger.debug(f"حجم النص المستخرج: {len(full_text)} حرف")
        
        # 4. استخراج القيم مع التسجيل
        extraction_log = {}
        
        try:
            device_id = self._extract_device_id(full_text)
            extraction_log['device_id'] = device_id
            logger.info(f"✓ Device ID: {device_id}")
            
            serial = self._extract_serial(full_text)
            extraction_log['serial'] = serial
            logger.info(f"✓ Serial: {serial}")
            
            start_date = self._extract_start_date(full_text)
            extraction_log['start_date'] = start_date.isoformat()
            logger.info(f"✓ Start Date: {start_date}")
            
            stop_date = self._extract_stop_date(full_text)
            extraction_log['stop_date'] = stop_date.isoformat()
            logger.info(f"✓ Stop Date: {stop_date}")
            
            min_temp = self._extract_min_temperature(full_text)
            extraction_log['min_temp'] = str(min_temp)
            logger.info(f"✓ Min Temp: {min_temp}°C")
            
            max_temp = self._extract_max_temperature(full_text)
            extraction_log['max_temp'] = str(max_temp)
            logger.info(f"✓ Max Temp: {max_temp}°C")
            
            avg_temp = self._extract_avg_temperature(full_text)
            extraction_log['avg_temp'] = str(avg_temp)
            logger.info(f"✓ Avg Temp: {avg_temp}°C")
            
            alarm_count = self._extract_alarm_count(full_text)
            extraction_log['alarm_count'] = alarm_count
            logger.info(f"✓ Alarm Count: {alarm_count}")
            
            total_readings = self._extract_total_readings(full_text)
            extraction_log['total_readings'] = total_readings
            logger.info(f"✓ Total Readings: {total_readings}")
            
        except ExtractionError as e:
            logger.error(f"فشل استخراج القيم: {e}")
            doc.close()
            raise
        finally:
            doc.close()
        
        # تسجيل ملخص الاستخراج
        logger.info(f"تم استخراج {len(extraction_log)} قيمة بنجاح")
        logger.debug(f"تفاصيل الاستخراج: {extraction_log}")
        
        return PDFExtractionResult(
            device_id=device_id,
            serial=serial,
            start_date=start_date,
            stop_date=stop_date,
            min_temperature=min_temp,
            max_temperature=max_temp,
            avg_temperature=avg_temp,
            alarm_count=alarm_count,
            total_readings=total_readings,
            extraction_timestamp=datetime.utcnow(),
            pdf_hash=pdf_hash
        )
    
    def _calculate_hash(self, file_path: Path) -> str:
        """حساب هاش SHA256 للملف للتحقق من سلامته لاحقاً"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_full_text(self, doc: fitz.Document) -> str:
        """استخراج النص الكامل من جميع صفحات المستند"""
        texts = []
        for page_num, page in enumerate(doc):
            try:
                text = page.get_text()
                if text.strip():
                    texts.append(text)
                    logger.debug(f"الصفحة {page_num + 1}: استخرج {len(text)} حرف")
            except Exception as e:
                logger.warning(f"فشل استخراج النص من الصفحة {page_num + 1}: {e}")
        
        if not texts:
            raise ExtractionError("فشل استخراج أي نص من ملف PDF")
        
        return "\n".join(texts)
    
    def _extract_device_id(self, text: str) -> str:
        """استخراج نوع الجهاز (Device ID)"""
        # البحث عن الأنماط الشائعة في تقارير Berlinger
        patterns = [
            r'Device\s*[:\s]+(Q-tag Fridge-tag 2 E)',
            r'Q-tag Fridge-tag 2 E',
            r'Device Type\s*[:\s]+([^,\n\r]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                logger.debug(f"تم العثور على Device ID: {result}")
                return result
        
        logger.warning("لم يتم العثور على Device ID باستخدام الأنماط المعروفة")
        # محاولة استخراج عام كحل بديل
        match = re.search(r'Device\s*[:\s]+([^\n\r]+)', text, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            logger.debug(f"تم استخدام نمط عام للعثور على Device ID: {result}")
            return result
        
        raise ExtractionError("لم يتم العثور على Device ID في التقرير")
    
    def _extract_serial(self, text: str) -> str:
        """استخراج الرقم التسلسلي (Serial Number)"""
        patterns = [
            r'Serial\s*[:\s]+(\d{12,})',  # Berlinger تستخدم 12+ رقم
            r'Serial No\.?\s*[:\s]+(\d+)',
            r'S/N\s*[:\s]+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                logger.debug(f"تم العثور على Serial: {result}")
                return result
        
        raise ExtractionError("لم يتم العثور على Serial Number في التقرير")
    
    def _extract_start_date(self, text: str) -> date:
        """استخراج تاريخ البداية (أول تاريخ في السجل)"""
        # البحث عن جميع التواريخ بتنسيق ISO
        dates = self._extract_all_dates(text)
        
        if not dates:
            raise ExtractionError("لم يتم العثور على تواريخ في التقرير")
        
        # تاريخ البداية = أقدم تاريخ في السجل
        start_date = min(dates)
        logger.debug(f"تم تحديد تاريخ البداية: {start_date} (أقدم تاريخ)")
        return start_date
    
    def _extract_stop_date(self, text: str) -> date:
        """استخراج تاريخ النهاية (آخر تاريخ في السجل)"""
        # البحث عن جميع التواريخ بتنسيق ISO
        dates = self._extract_all_dates(text)
        
        if not dates:
            raise ExtractionError("لم يتم العثور على تواريخ في التقرير")
        
        # تاريخ النهاية = أحدث تاريخ في السجل
        stop_date = max(dates)
        logger.debug(f"تم تحديد تاريخ النهاية: {stop_date} (أحدث تاريخ)")
        return stop_date
    
    def _extract_all_dates(self, text: str) -> List[date]:
        """استخراج جميع التواريخ بتنسيق ISO من النص"""
        matches = re.findall(r'(\d{4})-(\d{2})-(\d{2})', text)
        dates = []
        
        for year, month, day in matches:
            try:
                d = date(int(year), int(month), int(day))
                # تجاهل التواريخ غير المنطقية (مثل تواريخ التصنيع القديمة جداً)
                if d.year >= 2020 and d <= date.today():
                    dates.append(d)
            except ValueError:
                continue
        
        return dates
    
    def _extract_min_temperature(self, text: str) -> Decimal:
        """استخراج أقل درجة حرارة من جميع القراءات"""
        matches = re.findall(r'Min T\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)', text, re.IGNORECASE)
        
        if not matches:
            raise ExtractionError("لم يتم العثور على قيم Min T في التقرير")
        
        try:
            values = [Decimal(v.replace(',', '.')) for v in matches]
            result = min(values)
            logger.debug(f"تم العثور على {len(values)} قيم Min T - الأدنى: {result}°C")
            return result
        except InvalidOperation as e:
            raise ExtractionError(f"فشل تحويل قيم درجات الحرارة إلى أرقام: {e}")
    
    def _extract_max_temperature(self, text: str) -> Decimal:
        """استخراج أعلى درجة حرارة من جميع القراءات"""
        matches = re.findall(r'Max T\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)', text, re.IGNORECASE)
        
        if not matches:
            raise ExtractionError("لم يتم العثور على قيم Max T في التقرير")
        
        try:
            values = [Decimal(v.replace(',', '.')) for v in matches]
            result = max(values)
            logger.debug(f"تم العثور على {len(values)} قيم Max T - الأعلى: {result}°C")
            return result
        except InvalidOperation as e:
            raise ExtractionError(f"فشل تحويل قيم درجات الحرارة إلى أرقام: {e}")
    
    def _extract_avg_temperature(self, text: str) -> Decimal:
        """استخراج متوسط درجات الحرارة"""
        matches = re.findall(r'(?:Avrg|Avg|Average) T\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)', text, re.IGNORECASE)
        
        if not matches:
            raise ExtractionError("لم يتم العثور على قيم متوسط درجات الحرارة في التقرير")
        
        try:
            values = [Decimal(v.replace(',', '.')) for v in matches]
            result = sum(values) / len(values)
            logger.debug(f"تم حساب متوسط {len(values)} قراءة: {result}°C")
            return result
        except InvalidOperation as e:
            raise ExtractionError(f"فشل تحويل قيم المتوسط إلى أرقام: {e}")
    
    def _extract_alarm_count(self, text: str) -> int:
        """استخراج إجمالي عدد التنبيهات (t Acc > 0)"""
        # البحث عن قيم t Acc
        matches = re.findall(r't Acc\s*[:=]?\s*(\d+)', text, re.IGNORECASE)
        
        if not matches:
            logger.debug("لم يتم العثور على قيم t Acc - افتراض عدم وجود تنبيهات")
            return 0
        
        total = sum(int(v) for v in matches if int(v) > 0)
        logger.debug(f"تم حساب إجمالي التنبيهات: {total} (من {len(matches)} قيمة)")
        return total
    
    def _extract_total_readings(self, text: str) -> int:
        """استخراج عدد القراءات الكلية"""
        # الطريقة 1: البحث عن "Report history length"
        match = re.search(r'Report history length\s*[:=]?\s*(\d+)', text, re.IGNORECASE)
        if match:
            result = int(match.group(1))
            logger.debug(f"تم العثور على Report history length: {result}")
            return result
        
        # الطريقة 2: عد التواريخ الفريدة
        dates = self._extract_all_dates(text)
        if dates:
            result = len(set(dates))
            logger.debug(f"تم حساب عدد القراءات من التواريخ الفريدة: {result}")
            return result
        
        logger.warning("لم يتم العثور على عدد القراءات - افتراض 60 يوماً (القيمة الافتراضية لـ Berlinger)")
        return 60  # القيمة الافتراضية لأجهزة Berlinger