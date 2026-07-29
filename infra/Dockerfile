FROM vllm/vllm-openai:latest

WORKDIR /app
COPY requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt
COPY . .

ENV INFERENCE_BACKEND=vllm \
    MODEL_PATH=/models/edspike \
    MAX_BATCH_SIZE=64

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "src.deployment.inference_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]

