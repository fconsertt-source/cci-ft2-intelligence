import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FT2Parser:
    """
    محلل لملفات Fridge-tag 2 النصية (Legacy Format)
    """
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        تحليل ملف نصي واستخراج البيانات
        """
        data = {
            'device_info': {},
            'history': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_section = None
            current_entry = {}
            current_alarm_idx = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # استخراج معلومات الجهاز
                if line.startswith('Serial:'):
                    data['device_info']['serial_number'] = line.split('Serial:')[1].strip()
                elif line.startswith('Device:'):
                    data['device_info']['model'] = line.split('Device:')[1].strip()
                
                # تحديد القسم
                if line.startswith('Hist:'):
                    current_section = 'history'
                    continue
                
                # معالجة قسم التاريخ
                if current_section == 'history':
                    # بداية يوم جديد (رقم متبوع بنقطتين، مثل "1:")
                    if re.match(r'^\d+:$', line):
                        if current_entry:
                            data['history'].append(current_entry)
                        current_entry = {}
                        current_alarm_idx = None
                    
                    # استخراج البيانات لليوم الحالي
                    elif current_entry is not None:
                        if line.startswith('Date:'):
                            current_entry['date'] = line.split('Date:')[1].strip()
                        
                        # استخراج درجات الحرارة (قد تكون في سطر واحد أو أسطر متعددة)
                        # مثال: Min T: +6.1, TS Min T: 16:19
                        if 'Min T:' in line:
                            match = re.search(r'Min T:\s*([+\-]?\d+\.\d+)', line)
                            if match:
                                current_entry['min_temp'] = float(match.group(1))
                        
                        if 'Max T:' in line:
                            match = re.search(r'Max T:\s*([+\-]?\d+\.\d+)', line)
                            if match:
                                current_entry['max_temp'] = float(match.group(1))
                                
                        if 'Avrg T:' in line:
                            match = re.search(r'Avrg T:\s*([+\-]?\d+\.\d+)', line)
                            if match:
                                current_entry['avg_temp'] = float(match.group(1))
                        
                        # استخراج زمن التنبيهات (t Acc)
                        if line.startswith('0:'):
                            current_alarm_idx = '0'
                        elif line.startswith('1:'):
                            current_alarm_idx = '1'
                        
                        if 't Acc:' in line and current_alarm_idx:
                            match = re.search(r't Acc:\s*(\d+)', line)
                            if match:
                                if 'alarms' not in current_entry: current_entry['alarms'] = {}
                                current_entry['alarms'][current_alarm_idx] = int(match.group(1))

            # إضافة آخر إدخال
            if current_entry:
                data['history'].append(current_entry)
                
            logger.info(f"تم استخراج {len(data['history'])} سجل يومي من {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"خطأ في تحليل الملف النصي {file_path}: {e}")
            return {}

    def get_summary(self):
        return {}