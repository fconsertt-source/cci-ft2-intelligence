import logging
import os


def get_logger(name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh = logging.FileHandler("pipeline.log", mode="a", encoding="utf-8")
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
        os.makedirs("logs", exist_ok=True)

        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh = logging.FileHandler("logs/audit.log", mode="a", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.propagate = False
    return logger
