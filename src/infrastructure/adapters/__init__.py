# استيراد الـ Adapters الموجودة فعلياً
from .ledger_writer_adapter import HashChainedLedgerWriter

# ✅ استيراد مشروط للـ Adapters الأخرى (إن وجدت)
try:
    from .filesystem_adapter import FilesystemAdapter
except ImportError:
    pass

try:
    from .jsonl_index_adapter import JSONLIndexAdapter
except ImportError:
    pass

__all__ = [
    'HashChainedLedgerWriter',
    'FilesystemAdapter',
    'JSONLIndexAdapter'
]
