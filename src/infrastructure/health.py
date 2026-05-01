#!/usr/bin/env python3
"""
Health Check HTTP Endpoint — Liveness/Readiness probe.

Guardrail (Architect + Optimizer):
- Isolated entirely within src/infrastructure/
- Uses Python's built-in http.server ONLY (no FastAPI/Flask dependencies)
- Provides basic Liveness + Readiness checks
- Does NOT connect to any use case or domain logic

Usage:
    python -m src.infrastructure.health
    # Serves on http://localhost:8080/health
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

START_TIME = time.time()

# Minimal readiness check — verify key infrastructure files exist
CRITICAL_FILES = [
    "src/infrastructure/logging.py",
    "src/domain/services/rules_engine.py",
]


def _liveness() -> dict:
    """Liveness: is the process alive?"""
    uptime = time.time() - START_TIME
    return {
        "status": "alive",
        "uptime_seconds": round(uptime, 1),
        "pid": _get_pid(),
    }


def _readiness() -> dict:
    """Readiness: are critical files accessible?"""
    missing = []
    for f in CRITICAL_FILES:
        if not Path(f).exists():
            missing.append(f)

    if missing:
        return {
            "status": "unhealthy",
            "missing_files": missing,
        }

    return {
        "status": "ready",
        "checks_passed": True,
    }


def _get_pid() -> int:
    try:
        return _get_pid_impl()
    except Exception:
        return -1


def _get_pid_impl() -> int:
    import os
    return os.getpid()


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for /health endpoint."""

    def do_GET(self):  # noqa: N802 — HTTP server convention
        if self.path == "/health" or self.path == "/health/":
            self._handle_health()
        elif self.path == "/ready" or self.path == "/ready/":
            self._handle_readiness()
        elif self.path == "/alive" or self.path == "/alive/":
            self._handle_liveness()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def _handle_health(self):
        liveness = _liveness()
        readiness = _readiness()

        if readiness["status"] != "ready":
            status_code = 503
            body = {"liveness": liveness, "readiness": readiness}
        else:
            status_code = 200
            body = {"liveness": liveness, "readiness": readiness}

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())

    def _handle_liveness(self):
        body = _liveness()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _handle_readiness(self):
        body = _readiness()
        status_code = 200 if body["status"] == "ready" else 503
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())

    def log_message(self, format, *args):  # noqa: A002 — override signature
        logger.debug("%s - %s", self.client_address[0], format % args)


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the health check HTTP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    server = HTTPServer((host, port), HealthHandler)
    logger.info("Health endpoint listening on http://%s:%d/health", host, port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down health endpoint")
        server.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port=port)
