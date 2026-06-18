# ============================================================
# SecureDataMining API — Dockerfile
# Modelo de minería de datos para detección de vulnerabilidades
# ============================================================
FROM python:3.12-slim

# Metadata
LABEL maintainer="ESPE DevSecOps"
LABEL description="API de predicción de vulnerabilidades — Minería de Datos (No LLM)"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Instalar dependencias del sistema para tree-sitter y libclang
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    curl \
    libclang-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install fastapi uvicorn[standard]

# Copiar el proyecto (incluyendo el modelo entrenado previamente en local)
COPY . .

# Exponer puerto
EXPOSE 8000

# Healthcheck para Render/Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio
CMD ["uvicorn", "app.interfaces.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
