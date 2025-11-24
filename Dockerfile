### Multi-stage Dockerfile for HypePrice Tracker
# Stage 1: Build frontend with Node (Vite)
FROM node:18-bullseye-slim AS frontend-build
WORKDIR /app/frontend

# Copy only package files first for better cacheability
COPY frontend/package.json frontend/package-lock.json ./

# Use npm ci when lockfile exists; fall back to npm install if needed
# Use flags to reduce failures related to peer deps and permission issues in CI
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
RUN if [ -f package-lock.json ]; then \
            npm ci --prefer-offline --no-audit --no-progress --legacy-peer-deps --unsafe-perm || npm install --no-audit --no-progress --legacy-peer-deps --unsafe-perm; \
        else \
            npm install --no-audit --no-progress --legacy-peer-deps --unsafe-perm; \
        fi

# Copy rest of frontend sources and build
COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime with Playwright browsers
FROM python:3.11-slim
WORKDIR /app

# Install apt deps required by Playwright and some browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates git curl build-essential libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxshmfence1 libasound2 libpangocairo-1.0-0 libgtk-3-0 libx11-xcb1 libxcb1 libx11-6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source
COPY backend ./backend
COPY requirements.txt ./

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (binaries) after playwright is installed
RUN playwright install --with-deps

# Copy built frontend files from the builder
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
