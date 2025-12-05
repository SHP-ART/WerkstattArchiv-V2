# Werkstatt-Archiv Docker Image
# Python 3.11 mit Tesseract OCR und deutscher Sprache

FROM python:3.11-slim

# Metadaten
LABEL maintainer="SHP-ART"
LABEL description="Werkstatt-Archiv - PDF Archivierung mit OCR"
LABEL version="1.0"

# Umgebungsvariablen
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# System-Dependencies installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-deu \
    # PDF-Verarbeitung (für pdf2image)
    poppler-utils \
    # Bildverarbeitung
    libpng-dev \
    libjpeg-dev \
    # Für Pillow
    zlib1g-dev \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Requirements zuerst kopieren (für Docker Cache)
# Build-Context ist das Elternverzeichnis (..)
COPY requirements.txt .

# Python-Dependencies installieren
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir waitress

# Anwendung kopieren
COPY *.py ./
COPY templates/ ./templates/

# Verzeichnisse für Volumes erstellen
RUN mkdir -p /data/archiv /data/eingang /data/backup /app/logs

# Port freigeben
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/stats')" || exit 1

# Standard-Befehl: Web-Server starten
CMD ["python", "web_app.py", "--host", "0.0.0.0", "--port", "8080"]
