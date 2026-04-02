FROM python:3.10-slim

# System deps: ffmpeg for audio decode, libsndfile for soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 libsndfile1-dev gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download HF models so container starts fast
# Only downloaded when PREFETCH_HF_MODELS=true; skipped for Sarvam (default)
COPY scripts/prefetch_models.py /tmp/prefetch_models.py
RUN python /tmp/prefetch_models.py

# Copy application code
COPY . .

# HuggingFace Spaces runs on port 7860
EXPOSE 7860

ENV PYTHONUNBUFFERED=1 \
    API_PORT=7860 \
    MCP_SERVER_PORT=8000 \
    VOICE_PROVIDER=sarvam

# Startup script: launch MCP server in background, then API server on 7860
CMD ["sh", "-c", "\
  echo '🔧 Starting MCP server on :8000...' && \
  cd /app/phase-2-mcp-tools && \
  python -m uvicorn server.mcp_server:app --host 0.0.0.0 --port 8000 & \
  sleep 3 && \
  echo '🚀 Starting AdvisorAI API on :7860...' && \
  cd /app && \
  python phase-4-integration/api_server.py \
"]
