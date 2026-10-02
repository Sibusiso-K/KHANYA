# REEFPRINT Live, secure server. Build from presentation/belt-monitor:
#   docker build -f deploy/Dockerfile -t reefprint-live .
#   docker run --read-only --tmpfs /tmp -v reefprint-data:/data -e REEFPRINT_DATA_KEY=... -p 127.0.0.1:8531:8531 reefprint-live
# Non-root, read-only root filesystem, one writable volume (/data). Not yet built: Docker is not installed on the dev laptop.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    REEFPRINT_DATA=/data REEFPRINT_PORT=8531 REEFPRINT_BIND=0.0.0.0

WORKDIR /app
COPY requirements-secure.txt /app/
# exact versions pinned; pip-audit clean on 2026-10-02
RUN pip install --no-cache-dir -r /app/requirements-secure.txt

# Only what the server needs: the page, the data replay, fonts and the server code. Never data_secure/ or keys.
COPY index.html app.js server.py app_server.py manage.py /app/
COPY secure/ /app/secure/
COPY live/ /app/live/
COPY fonts/ /app/fonts/

RUN useradd --system --uid 10001 --home /nonexistent --shell /usr/sbin/nologin reef \
    && mkdir -p /data && chown reef /data
USER 10001
VOLUME ["/data"]
EXPOSE 8531
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request,os;urllib.request.urlopen('http://127.0.0.1:'+os.environ['REEFPRINT_PORT']+'/live/summary.json',timeout=4)" || exit 1
CMD ["python", "app_server.py"]
