FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libimage-exiftool-perl libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY app ./app
COPY config ./config
RUN useradd --create-home --uid 1000 workflow && mkdir -p data/TEMP models training familyfaces && chown -R workflow:workflow /workspace
USER workflow
ENTRYPOINT ["python", "-m", "app.photoworkflow"]
CMD ["--help"]
