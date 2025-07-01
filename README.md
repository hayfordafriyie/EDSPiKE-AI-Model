# EDSPiKE AI Model

Production-oriented data, training, evaluation, optimization and inference code for an
EDSPiKE educational language model. The repository is runnable without model weights;
GPU training and production inference require separately licensed datasets, a base model
and suitable NVIDIA hardware.

## What is included

- Privacy-first data collector with deterministic pseudonymization
- JSON/JSONL/CSV/text ingestion, normalization, filtering and deduplication
- Stratified deterministic train/validation/test splitting
- Custom BPE tokenizer workflow
- Llama-style from-scratch architecture and pretrained-model training paths
- Reproducible Hugging Face Trainer workflow
- Exact-match, token-F1, curriculum-alignment and code-syntax evaluation
- AWQ quantization command
- Lazy Transformers and vLLM inference backends
- Authenticated FastAPI endpoints, input limits, health and Prometheus metrics
- GPU container, Compose deployment, benchmark script and automated tests

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

The three-record sample demonstrates formats but is too small for meaningful training.
Replace it with licensed, quality-reviewed data.

## Data contract

Processed JSONL records have these fields:

```json
{
  "instruction": "Question or task",
  "input": "Optional context",
  "output": "Expected response",
  "category": "education",
  "source": "provenance identifier",
  "license": "usage rights"
}
```

Never train on identifiable student, parent or staff records. Obtain authorization,
document provenance and licensing, and use aggregate operational examples where possible.

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
  -d '{"prompt":"Explain formative assessment.","max_tokens":128}'
```

Batch generation is `POST /v1/generate-batch`. Operational endpoints are `GET /health`
and `GET /metrics`.

## GPU production

Mount a compatible model at `./models/edspike`, set `INFERENCE_BACKEND=vllm`, then:

```bash
docker compose up --build
python scripts/benchmark.py --api-key "$EDSPIKE_API_KEY"
```

Throughput depends on model architecture, quantization, prompt/output lengths, GPU,
vLLM version and batch concurrency. The guide's 300 tokens/second figure is a benchmark
target, not a guarantee; measure it on the final hardware and model.

## Release checklist

1. Verify data licensing, consent, provenance and de-identification.
2. Run contamination, duplication, toxicity and Ghana-context quality reviews.
3. Record training configuration, dataset version and model checksum.
4. Evaluate against a frozen held-out suite and human educators.
5. Red-team privacy leakage, prompt injection and unsafe administrative actions.
6. Use API authentication, TLS, rate limiting and network isolation.
7. Load-test the exact quantized release on production hardware.
8. Establish rollback, incident response and model monitoring.

