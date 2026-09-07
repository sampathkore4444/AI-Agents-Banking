# Sathapana KYC Agent — Linux container (dev parity, offline embedding model).
#
# Build:   docker build -t sathapana-kyc-agent:latest .
# Run API: docker run --rm -p 8000:8000 -v "%cd%:/app" -w /app sathapana-kyc-agent:latest
#          (then open http://localhost:8000/  — Swagger UI)
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HOME=/models \
    SENTENCE_TRANSFORMERS_HOME=/models

WORKDIR /app

# Runtime deps (torch/sentence-transformers are pure Python wheels on Linux).
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Pre-download the default embedding model into the image so the container is
# offline-capable on first start. Override with a different MODEL via --build-arg.
ARG EMBEDDING_MODEL=all-MiniLM-L6-v2
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL}
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}'); print('embedding model cached:', '${EMBEDDING_MODEL}')"

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=5)"

# Default command: REST API + Swagger UI. For the MCP server use e.g.:
#   docker run ... sathapana-kyc-agent:latest python main.py serve                  (stdio)
#   docker run ... -e MCP_PORT=8888 -p 8888:8888 ... python main.py serve --transport tcp
CMD ["python", "main.py", "serve-api", "--host", "0.0.0.0", "--port", "8000"]