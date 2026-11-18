FROM python:3.11-slim

WORKDIR /app

# System deps for pandas/numpy/scipy and Excel parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy project-level config, scripts, and data (available because context = project root)
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY backend/data/ /app/data/
# Fixtures are copied as part of `COPY backend/ .` above (backend/fixtures → /app/fixtures)

# Cache directory (mounted as named volume in compose)
RUN mkdir -p /app/.cache

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
