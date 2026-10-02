# REEFPRINT Live on a Hugging Face Docker Space (always on; the laptop can be off).
# Built from the Space repo root, which deploy/hf_deploy.py fills with the files below.
# Non-root (uid 1000, as Spaces require), one writable data directory, no keys or databases in the image.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    REEFPRINT_PORT=7860 REEFPRINT_BIND=0.0.0.0 \
    REEFPRINT_DATA=/home/user/data \
    REEFPRINT_HOSTS=lethabomh14-reefprint.hf.space \
    REEFPRINT_SECURE_COOKIES=1 REEFPRINT_TRUST_PROXY=1 \
    REEFPRINT_FRAME_ANCESTORS=https://huggingface.co

RUN useradd -m -u 1000 user
WORKDIR /home/user/app
COPY --chown=user requirements-secure.txt ./
# exact versions pinned; pip-audit clean on 2026-10-02; all have manylinux wheels (no compiler needed)
RUN pip install --no-cache-dir -r requirements-secure.txt

COPY --chown=user index.html app.js server.py app_server.py manage.py ./
COPY --chown=user secure/ ./secure/
COPY --chown=user live/ ./live/
COPY --chown=user fonts/ ./fonts/

USER user
RUN mkdir -p /home/user/data
EXPOSE 7860
CMD ["python", "app_server.py"]
