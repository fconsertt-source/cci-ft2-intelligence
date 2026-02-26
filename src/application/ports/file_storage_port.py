"""
واجهة مجردة للعمليات على نظام الملفات.

يسمح باستبدال التخزين مستقبلاً (S3, NFS, etc.)
دون تغيير منطق الأعمال.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileStoragePort(Protocol):
    """
    واجهة مجردة للعمليات على نظام الملفات.
    
    الضمانات:
    - عمليات ذرية (atomic)
    - fsync بعد الكتابة
    - تحقق من السلامة
    """
    
    def compute_hash(self, path: Path) -> str:
        """
        حساب SHA-256 للملف.
        
        Args:
            path: مسار الملف
            
        Returns:
            str: بصمة SHA-256 سداسية عشرية
        """
        ...
    
    def move_atomic(self, src: Path, dst: Path) -> None:
        """
        نقل ذري محصّن.
        
        الضمانات:
        - fsync بعد الكتابة
        - atomic rename
        - تحقق من اكتمال النقل
        
        Args:
            src: مسار المصدر
            dst: مسار الوجهة
            
        Raises:
            RuntimeError: إذا فشل النقل
        """
        ...
    
    def delete_secure(self, path: Path) -> None:
        """
        حذف آمن للملف.
        
        Args:
            path: مسار الملف للحذف
        """
        ...
    
    def exists(self, path: Path) -> bool:
        """
        التحقق من وجود الملف.
        
        Args:
            path: مسار الملف
            
        Returns:
            bool: True إذا كان الملف موجوداً
        """
        ...
    
    def get_size(self, path: Path) -> int:
        """
        الحصول على حجم الملف.
        
        Args:
            path: مسار الملف
            
        Returns:
            int: حجم الملف بالبايت
        """
        ...
