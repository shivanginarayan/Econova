FROM node:22-alpine AS web
WORKDIR /build
COPY package.json package-lock.json tsconfig.json ./
COPY apps/web ./apps/web
RUN npm ci && npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ECONOMY_PUBLIC_MODE=1 ECONOMY_STATIC_DIR=/app/dist ECONOMY_DB_PATH=/app/data/economy.sqlite3 APIFY_CALIBRATION_DIR=/app/data/calibrations ECONOMY_BENCHMARK_DIR=/app/data/benchmarks
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --create-home --uid 10001 econova && mkdir /app/data && chown econova:econova /app/data
COPY backend ./backend
COPY scripts ./scripts
COPY deployment/public-inputs.json ./deployment/public-inputs.json
COPY --from=web /build/dist ./dist
USER econova
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health',timeout=4)"
CMD ["python", "-m", "scripts.run_hosted"]
