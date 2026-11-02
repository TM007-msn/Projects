# Single container: FastAPI serves the API, the static frontend and content JSON.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATA_DIR=/data \
    CONTENT_DIR=/app/content

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Content is baked in as a fallback; docker-compose mounts ./content over it
# so content edits show up without a rebuild.
COPY content ./content

# Run as an unprivileged user. /data is the mounted volume for the SQLite file.
RUN useradd --create-home --uid 1000 revision && mkdir -p /data && chown revision /data
USER revision

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health', timeout=2)"

# --proxy-headers is off on purpose: the app is reached directly over LAN/Tailscale.
CMD ["sh", "-c", "exec uvicorn --factory app.main:create_app --host 0.0.0.0 --port ${PORT}"]
