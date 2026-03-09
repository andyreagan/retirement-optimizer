# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install Python dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend into Django staticfiles
COPY --from=frontend-build /app/frontend/dist/ ./backend/staticfiles/

# Collect static files (admin, DRF, etc.) and merge with frontend build
RUN SECRET_KEY=build-placeholder uv run python backend/manage.py collectstatic --noinput

# Create volume mount point for persistent SQLite database
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

WORKDIR /app/backend

# Migrate and start gunicorn
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/docker-entrypoint.sh"]
