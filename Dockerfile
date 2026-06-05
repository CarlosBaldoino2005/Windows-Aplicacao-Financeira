# Imagem para deploy na nuvem (Render, Fly.io, etc.)
FROM python:3.12-slim

WORKDIR /app

# Dependencias do sistema para matplotlib (caso algum grafico server-side no futuro)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

COPY api/ ./api/
COPY src/ ./src/
COPY modelo-ui/ ./modelo-ui/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
