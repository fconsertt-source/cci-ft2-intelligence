"""منفذ مراقبة الأداء — يُعرّف في Application، يُنفذ في Infrastructure"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional, Dict, Any


class PerformanceMonitorPort(ABC):
    """منفذ مراقبة الأداء"""

    @abstractmethod
    @contextmanager
    def measure(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        قياس أداء عملية.

        Usage:
            with performance_monitor.measure('generate_report'):
                pass
        """
        pass