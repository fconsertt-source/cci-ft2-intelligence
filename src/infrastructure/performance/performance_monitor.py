# src/infrastructure/performance/performance_monitor.py
"""
Performance monitoring for Phase 2.
"""
import time
from contextlib import contextmanager
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os
from src.application.ports.performance_monitor_port import PerformanceMonitorPort


@dataclass
class PerformanceMetrics:
    """بيانات مقاييس الأداء"""
    operation: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    memory_usage_mb: float
    cpu_percent: float
    metadata: Dict[str, Any]


class PerformanceMonitor(PerformanceMonitorPort):
    """تنفيذ فعلي لـ PerformanceMonitorPort"""

    def __init__(self, log_file: str = None):
        self.log_file = log_file or "data/reports/performance_metrics.jsonl"
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    @contextmanager
    def measure(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager to measure performance."""
        start_time = datetime.now()
        
        # Simple memory estimation (not accurate, but better than nothing)
        try:
            import psutil
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            start_cpu = psutil.cpu_percent(interval=None)
            has_psutil = True
        except ImportError:
            start_memory = 0.0
            start_cpu = 0.0
            has_psutil = False

        try:
            yield
        finally:
            end_time = datetime.now()
            
            if has_psutil:
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                end_cpu = psutil.cpu_percent(interval=None)
            else:
                end_memory = 0.0
                end_cpu = 0.0

            duration = (end_time - start_time).total_seconds() * 1000

            metrics = PerformanceMetrics(
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration,
                memory_usage_mb=end_memory - start_memory,
                cpu_percent=end_cpu - start_cpu,
                metadata=metadata or {}
            )

            self._log_metrics(metrics)

    def _log_metrics(self, metrics: PerformanceMetrics):
        """Log metrics to file."""
        data = {
            "operation": metrics.operation,
            "start_time": metrics.start_time.isoformat(),
            "end_time": metrics.end_time.isoformat(),
            "duration_ms": metrics.duration_ms,
            "memory_usage_mb": metrics.memory_usage_mb,
            "cpu_percent": metrics.cpu_percent,
            "metadata": metrics.metadata
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps(data, ensure_ascii=False) + '\n')