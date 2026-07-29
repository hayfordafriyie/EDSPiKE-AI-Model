# Business Integration Guide

This guide explains how to integrate EDSPiKE AI into your business — no deep ML knowledge required.

---

## 1. What You Need (Overview)

| What | Who Handles It | When |
|------|----------------|------|
| Your business data (policies, customer Q&As, procedures, etc.) | Your team | Day 1 |
| A server with a GPU (optional for testing) | IT/DevOps | Week 1 |
| Model weights (or use our training pipeline) | ML/DevOps | Week 1-2 |

---

## 2. Get Your Data Ready

Format your business data as simple JSONL files (one JSON object per line):

```json
{"instruction": "What is our return policy?", "output": "Items can be returned within 30 days..."}
{"instruction": "Write a welcome email for a new client", "output": "Dear [Client], welcome to..."}
```

Place files in `data/raw/`. The platform accepts JSON, JSONL, CSV, TXT, and MD.
See `README.md` → **Data contract** for the full schema.

---

## 3. Access the AI

### Option A — API (Recommended for Apps)

Start the server:
```bash
cp .env.example .env    # Set your API key
uvicorn src.deployment.inference_server:app --host 0.0.0.0 --port 8000
```

Call it from any app:
```bash
curl http://localhost:8000/v1/generate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is our return policy?"}'
```

### Option B — Docker (Production)

```bash
docker compose -f infra/docker-compose.yml up --build
```

### Option C — Python Script (Quick Testing)

```python
from src.deployment.inference_server import app
# or use the client library
```

---

## 4. Continuous Learning Loop

The model improves automatically as you use it:

1. Users interact via the API
2. Feedback is stored in `feedback.db`
3. Run retraining periodically:

```bash
python -m src.continuous_learning.collector --db feedback.db
python -m src.continuous_learning.train --db feedback.db --output checkpoints/v2
```

No manual data science work needed between cycles.

---

## 5. Roles & Responsibilities

| Role | What They Do |
|------|-------------|
| **Business Owner** | Provides data, defines use cases, reviews answers |
| **DevOps / IT** | Deploys the server, manages GPU, sets up monitoring |
| **ML Engineer** (optional) | Trains custom models, tunes performance |

---

## 6. Quick Decision Flow

```
Want to try it out with sample data?
  → pip install -e ".[ml,test]" && python -m src.data_pipeline.cli process

Have your own business data?
  → Place JSONL in data/raw/ → run data pipeline → start the API

Need a custom model trained on your data?
  → Prepare dataset → python -m src.training.trainer --config configs/base_config.yaml

Going to production?
  → Quantize model → docker compose up → monitor with Prometheus
```

---

## 7. Support

- Issues: https://github.com/hayfordafriyie/EDSPiKE-AI-Model/issues
- Build guide: `docs/EDSPIKE_AI_MODEL_BUILD_GUIDE.md`

