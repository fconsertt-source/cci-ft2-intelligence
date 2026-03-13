# Lightweight container for running tests and develop PDF engine
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# copy source
COPY . /app

# entrypoint for convenience
ENTRYPOINT ["/bin/bash"]
