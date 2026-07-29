# EDSPiKE AI Agent — Autonomous AI Coding & Business Platform

Production-grade multi-agent orchestration, tool-use (ReAct), continuous learning, and
deployment stack for building domain-agnostic AI agents that **learn continuously from your data**.
Any organization can plug in their data and get an AI agent that grows smarter over time.

## What is included

- **Privacy-first data collector** with deterministic pseudonymization (JSON/JSONL/CSV/TXT/MD)
- **Data ingestion pipeline** — normalization, filtering, deduplication, stratified splitting
- **Multi-agent orchestration** — 8+ agent definitions, worker pool, boss judge, ReAct tool-use loop
- **AI provider system** — OpenAI, Anthropic, Google, DeepSeek, local models with smart routing
- **Session store** — SQLite with event sourcing, session runner, sharing, undo/redo
- **LSP integration** — code intelligence, diagnostics, goto-definition, references, hover
- **CodeMode sandbox** — isolated subprocess execution with plugin hooks
- **Virtual filesystem** — path allowlisting, file mutation tracking, change detection
- **Shell/PTY** — interactive shell execution with PtyProcess
- **Git tool operations** — status, diff, log, commit, branch, checkout
- **MCP protocol** — Model Context Protocol server + client for external tool integration
- **Plugin host** — directory discovery, .py loading, event hook system
- **Config system** — JSON/YAML layered config with env var overrides
- **Credential store** — SQLite-backed persistent key/value store
- **Policy engine** — action/resource pattern matching, priority ordering, allow/deny/ask
- **Continuous learning loop** — collect feedback, store interactions, trigger retraining
- **FastAPI server** — multi-endpoint API (sessions, agents, providers, models, fs, codemode)
- **CLI + TUI** — non-interactive prompt mode, interactive REPL with rich markdown
- **Scout agent** — clone & inspect dependency repos, file/language/dependency analysis
- **Project scanner** — auto-generate AGENTS.md with language, build system, conventions
- **Rules system** — AGENTS.md + CLAUDE.md loading, global rules, instruction references
- **Custom commands** — named arguments, handlers, /cmd --key val parsing
- **Background jobs, OAuth, feature flags, snapshots, telemetry, skills, integrations**
- **Docker Compose** deployment with Prometheus monitoring

## Quick start

### 1. One-command install (recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/hayfordafriyie/EDSPiKE-AI-Model/Staging/scripts/install.sh | bash
```

### 2. Manual install
```bash
git clone https://github.com/hayfordafriyie/EDSPiKE-AI-Model.git
cd EDSPiKE-AI-Model

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

### 3. Run
```bash
# Check version
edspike --version

# Run tests
pytest

# Interactive mode (TUI)
edspike

# Non-interactive mode
edspike "your prompt here"

# Help
edspike --help
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

Generate (single):

```bash
curl http://localhost:8000/v1/generate \
  -H "Authorization: Bearer replace-me" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is our return policy?","max_tokens":128}'
```

Generate (batch):

```bash
curl http://localhost:8000/v1/generate \
  -H "Authorization: Bearer replace-me" \
  -H "Content-Type: application/json" \
  -d '{"prompts":["Question 1?","Question 2?"],"max_tokens":128}'
```

Generate (multi-agent, default — 5 agents + boss judge):

```bash
curl http://localhost:8000/v1/generate \
  -H "Authorization: Bearer replace-me" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is our return policy?","num_agents":5}'
```

For single direct response (no agents), set `num_agents: 1`. Operational endpoints are `GET /health` and `GET /metrics`.

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

Mount a compatible model at `./models/EDSPiKE`, set `INFERENCE_BACKEND=vllm`, then:

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

