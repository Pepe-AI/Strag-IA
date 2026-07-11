# Servicio Stragia (FastAPI + WeasyPrint) para Render (runtime: Docker).
FROM python:3.12-slim

# Libs nativas de WeasyPrint (Pango/HarfBuzz/fontconfig) + fuentes.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi8 libfontconfig1 \
      fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# uv para instalar dependencias desde el lockfile (reproducible).
RUN pip install --no-cache-dir uv

WORKDIR /app

# Instala dependencias primero (mejor caché de capas).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Código de la aplicación.
COPY app/ ./app/

# Render inyecta $PORT. Shell form para que se expanda.
CMD uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
