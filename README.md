# EDSPiKE AI Model — Business AI Platform

Production-grade data pipeline, training, evaluation, optimization and inference stack for
building domain-agnostic language models that **learn continuously from your business data**.
Any organization can plug in their data and get an AI assistant that grows smarter over time.

The repository works without model weights; GPU training and production inference require
datasets, a base model and suitable NVIDIA hardware.

## What is included

- **Privacy-first data collector** with deterministic pseudonymization (JSON/JSONL/CSV/TXT/MD)
- **Data ingestion pipeline** — normalization, filtering, deduplication, stratified splitting
- **Custom BPE tokenizer** workflow
- **Llama-style** from-scratch architecture and pretrained-model training paths
- **Reproducible Hugging Face Trainer** workflow
- **Evaluation** — exact-match, token-F1, readability, business-domain relevance, code syntax
- **AWQ 4-bit quantization** for deployment
- **Dual inference backends** — Transformers (dev/CPU) and vLLM (production GPU)
- **FastAPI server** with auth, rate limits, Prometheus metrics, batch generation
- **Continuous learning loop** — collect feedback, store interactions, trigger retraining
- **Docker Compose** deployment with Prometheus monitoring
- **Benchmark script** and **automated tests**

Model weights and copyrighted training material are intentionally excluded.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
```

For the ML stack:

```bash
pip install -e ".[ml,test]"
cp data/sample_input.jsonl data/raw/sample.jsonl
python -m src.data_pipeline.cli process
python -m src.data_pipeline.cli split
```

The sample demonstrates data formats but is too small for meaningful training.
Replace it with your licensed, quality-reviewed business data.

## Data contract

Processed JSONL records have these fields:

```json
{
  "instruction": "Question or task",
  "input": "Optional context",
  "output": "Expected response",
  "category": "general",
  "source": "provenance identifier",
  "license": "usage rights"
}
```

Never train on identifiable personal records. Obtain authorization, document provenance
and licensing, and use aggregate operational examples where possible.

## Training

Edit `configs/base_config.yaml`, then:

```bash
python -m src.training.trainer --config configs/base_config.yaml
```

The default is a practical 1.1B pretrained base for an MVP. `--from-scratch` initializes
the configured Llama architecture, but meaningful from-scratch training requires a very
large corpus and substantial GPU capacity.

## Evaluation

Write one JSON object per line to `predictions.jsonl`, each containing `prediction`, then:

```bash
python -m src.evaluation.evaluate \
  --predictions predictions.jsonl \
  --test data/splits/test.jsonl
```

## Serving

Set a model path and API key:

```bash
cp .env.example .env
export MODEL_PATH=checkpoints/v1/final
export EDSPIKE_API_KEY='replace-me'
uvicorn src.deployment.inference_server:app --host 0.0.0.0 --port 8000
```

Generate:

```bash
curl http://localhost:8000/v1/generate \
  -H "Authorization: Bearer replace-me" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is our return policy?","max_tokens":128}'
```

Batch generation is `POST /v1/generate-batch`. Operational endpoints are `GET /health`
and `GET /metrics`.

## Continuous learning

The platform supports a feedback-driven retraining loop:

```bash
# Collect user feedback into the learning store
python -m src.continuous_learning.collector --db feedback.db

# Trigger incremental fine-tuning on accumulated data
python -m src.continuous_learning.train --db feedback.db --output checkpoints/v2
```

As your business grows and more data accumulates, the model improves automatically.

## GPU production

Mount a compatible model at `./models/edspike`, set `INFERENCE_BACKEND=vllm`, then:

```bash
docker compose -f infra/docker-compose.yml up --build
python scripts/benchmark.py --api-key "$EDSPIKE_API_KEY"
```

Throughput depends on model architecture, quantization, prompt/output lengths, GPU,
vLLM version and batch concurrency. Measure on your final hardware and model.

## Release checklist

1. Verify data licensing, consent, provenance and de-identification.
2. Run contamination, duplication, toxicity and domain-context quality reviews.
3. Record training configuration, dataset version and model checksum.
4. Evaluate against a frozen held-out suite and domain experts.
5. Red-team privacy leakage, prompt injection and unsafe actions.
6. Use API authentication, TLS, rate limiting and network isolation.
7. Load-test the exact quantized release on production hardware.
8. Establish rollback, incident response and model monitoring.

