# Build the React/Vite frontend with Node available in the build image.
FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

# Install from the lockfile for reproducible deployment builds.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# Run FastAPI with only the application and production Python dependencies.
FROM python:3.12-slim AS backend

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# These are the backend modules and bundled fallback data required at runtime.
COPY backend/ ./backend/
COPY finance_engine/ ./finance_engine/
COPY data/ ./data/

# FastAPI serves this generated build from the same origin as the API.
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
