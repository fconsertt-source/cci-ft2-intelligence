# Lightweight container for running tests and develop PDF engine
FROM python:3.12-slim

WORKDIR /app

# === Install WeasyPrint system dependencies ===
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libgobject-2.0-0 \
    libffi8 \
    libfontconfig1 \
    libfreetype6 \
    fonts-liberation \
    fonts-dejavu \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . /app

# Optional: entrypoint
ENTRYPOINT ["/bin/bash"]