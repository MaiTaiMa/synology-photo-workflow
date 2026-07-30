# Synology Photo Workflow | Dockerfile
# Mitentwickler: MaiTai | Erstellt: 2026-07-29 | Projektversion: 7.7.0
# Funktion: Nicht-privilegiertes CPU-Containerimage fuer einen kontrollierten Lauf.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home workflow
COPY app ./app
USER workflow
ENTRYPOINT ["python", "-m", "app.photoworkflow"]
