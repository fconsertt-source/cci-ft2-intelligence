import logging
import json
import os
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'device_id'):
            log_entry['device_id'] = record.device_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'user'):
            log_entry['user'] = record.user
            
        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = StructuredFormatter()
        fh = logging.FileHandler('pipeline.log', mode='a', encoding='utf-8')
        fh.setFormatter(formatter)
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(sh)
    return logger


def get_audit_logger(name: str = "audit") -> logging.Logger:
    """
    Returns a dedicated audit logger that writes to logs/audit.log
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)

        formatter = StructuredFormatter()
        fh = logging.FileHandler('logs/audit.log', mode='a', encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.propagate = False
    return logger
