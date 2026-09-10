ARG PYTHON_VERSION=3.12-slim-bookworm

# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_BASE=/static/
RUN npm run build

# ── Stage 2: Python app ──────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Install Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    pip install gunicorn psycopg2-binary whitenoise && \
    rm -rf /root/.cache/

# Copy backend code
COPY backend/ /code/

# Copy built frontend assets into Django staticfiles
# index.html goes to staticfiles/ for the index view to find
# assets/ go to staticfiles/ for WhiteNoise to serve at /static/
COPY --from=frontend-builder /frontend/dist/index.html /code/staticfiles/index.html
COPY --from=frontend-builder /frontend/dist/assets/ /code/staticfiles/assets/

# Collect Django static files (admin, DRF, etc.) alongside frontend assets
RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 retirement_backend.wsgi"]
