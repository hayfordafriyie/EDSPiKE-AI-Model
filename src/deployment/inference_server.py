from __future__ import annotations

import hmac
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

load_dotenv(Path(__file__).parents[2] / ".env")

from .engine import InferenceEngine, create_engine
from .prometheus_metrics import LATENCY, MODEL_READY, REQUESTS, THROUGHPUT, TOKENS
from src.agents.orchestrator import multi_agent_generate
from src.agents.worker import AGENT_PROFILES

logger = logging.getLogger(__name__)

MAX_BATCH = int(os.getenv("MAX_BATCH_SIZE", "64"))


class GenerateRequest(BaseModel):
    prompt: str | None = Field(default=None, min_length=1, max_length=20000)
    prompts: list[str] | None = Field(default=None)
    max_tokens: int = Field(default=256, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.95, gt=0, le=1)
    num_agents: int = Field(default=5, ge=1, le=10)
    max_worker_tokens: int | None = Field(default=None, ge=64, le=2048)
    max_judge_tokens: int | None = Field(default=None, ge=128, le=4096)

    @field_validator("prompt")
    @classmethod
    def check_prompt(cls, value: str | None) -> str | None:
        return value

    @field_validator("prompts")
    @classmethod
    def check_prompts(cls, value: list[str] | None) -> list[str] | None:
        if value is not None:
            if not value or len(value) > MAX_BATCH:
                raise ValueError(f"prompts must contain 1 to {MAX_BATCH} values")
            if any(not p.strip() or len(p) > 20000 for p in value):
                raise ValueError("each prompt must contain 1 to 20,000 characters")
        return value


def require_api_key(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("EDSPIKE_API_KEY", "")
    if not expected:
        return
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = None
    app.state.error = None
    device = os.getenv("DEVICE", "auto").lower()
    if device == "cpu":
        logger.info("Running in CPU mode — model will use device_map='cpu' with low_cpu_mem_usage=True")
    if os.getenv("SKIP_MODEL_LOAD", "false").lower() != "true":
        try:
            app.state.engine = create_engine()
            MODEL_READY.set(1)
        except Exception as exc:
            app.state.error = str(exc)
            MODEL_READY.set(0)
            logger.exception("Model initialization failed")
    yield


app = FastAPI(
    title="EDSPiKE AI Model API",
    version="1.0.0",
    description="Authenticated business-domain inference API with continuous learning",
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    started = time.perf_counter()
    status = "500"
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        REQUESTS.labels(request.url.path, status).inc()
        if request.url.path == "/v1/generate":
            LATENCY.observe(time.perf_counter() - started)


def engine(request: Request) -> InferenceEngine:
    eng = getattr(request.app.state, "engine", None)
    if eng is None:
        raise HTTPException(status_code=503, detail=request.app.state.error or "Model is not loaded")
    return eng


def run_generation(model: InferenceEngine, prompts: list[str], max_tokens: int, temperature: float, top_p: float):
    started = time.perf_counter()
    responses, counts = model.generate_batch(prompts, max_tokens, temperature, top_p)
    elapsed = time.perf_counter() - started
    total = sum(counts)
    throughput = total / elapsed if elapsed else 0
    TOKENS.inc(total)
    THROUGHPUT.set(throughput)
    return responses, counts, elapsed, throughput


@app.get("/health")
def health(request: Request):
    ready = getattr(request.app.state, "engine", None) is not None
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "error": getattr(request.app.state, "error", None)},
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/generate", dependencies=[Depends(require_api_key)])
def generate(payload: GenerateRequest, model: Annotated[InferenceEngine, Depends(engine)]):
    started = time.perf_counter()
    prompts = payload.prompts if payload.prompts else [payload.prompt]
    is_batch = payload.prompts is not None

    if payload.num_agents <= 1:
        responses, counts, elapsed, throughput = run_generation(
            model, prompts, payload.max_tokens, payload.temperature, payload.top_p,
        )
        if is_batch:
            result = {
                "responses": responses, "tokens_generated": sum(counts),
                "latency_ms": elapsed * 1000, "throughput_tokens_per_second": throughput,
                "model": model.model_name,
            }
        else:
            result = {
                "response": responses[0], "tokens_generated": counts[0],
                "latency_ms": elapsed * 1000, "throughput_tokens_per_second": throughput,
                "model": model.model_name,
            }
    else:
        profiles = AGENT_PROFILES[:payload.num_agents]
        result = multi_agent_generate(
            generate_fn=model.generate_batch,
            question=payload.prompt or prompts[0],
            profiles=profiles,
            max_worker_tokens=payload.max_worker_tokens or payload.max_tokens,
            max_judge_tokens=payload.max_judge_tokens or payload.max_tokens * 2,
            max_workers=payload.num_agents,
        )
        elapsed = time.perf_counter() - started
        result["latency_ms"] = elapsed * 1000
        result["model"] = model.model_name
    return result
