# Dockerfile para Comunidad Bot (no-root, reproducible)
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Crear usuario no-root
RUN adduser --disabled-password --gecos "" appuser

# Instalar dependencias de Python desde requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copiar código
COPY src /app/src
COPY config /app/config
COPY run.py /app/run.py

USER appuser
EXPOSE 8001

# START_MODE=server | polling
ENV START_MODE=server
CMD ["python", "run.py"]
