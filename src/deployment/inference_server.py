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

logger = logging.getLogger(__name__)


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)
    max_tokens: int = Field(default=256, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.95, gt=0, le=1)


class BatchRequest(BaseModel):
    prompts: list[str]
    max_tokens: int = Field(default=256, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.95, gt=0, le=1)

    @field_validator("prompts")
    @classmethod
    def validate_prompts(cls, value: list[str]) -> list[str]:
        maximum = int(os.getenv("MAX_BATCH_SIZE", "64"))
        if not value or len(value) > maximum:
            raise ValueError(f"prompts must contain 1 to {maximum} values")
        if any(not prompt.strip() or len(prompt) > 20000 for prompt in value):
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
        if request.url.path in {"/v1/generate", "/v1/generate-batch"}:
            LATENCY.observe(time.perf_counter() - started)


def engine(request: Request) -> InferenceEngine:
    if request.app.state.engine is None:
        raise HTTPException(status_code=503, detail=request.app.state.error or "Model is not loaded")
    return request.app.state.engine


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
    ready = request.app.state.engine is not None
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "error": request.app.state.error},
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/generate", dependencies=[Depends(require_api_key)])
def generate(payload: GenerationRequest, model: Annotated[InferenceEngine, Depends(engine)]):
    responses, counts, elapsed, throughput = run_generation(
        model, [payload.prompt], payload.max_tokens, payload.temperature, payload.top_p,
    )
    return {
        "response": responses[0], "tokens_generated": counts[0],
        "latency_ms": elapsed * 1000, "throughput_tokens_per_second": throughput,
        "model": model.model_name,
    }


@app.post("/v1/generate-batch", dependencies=[Depends(require_api_key)])
def generate_batch(payload: BatchRequest, model: Annotated[InferenceEngine, Depends(engine)]):
    responses, counts, elapsed, throughput = run_generation(
        model, payload.prompts, payload.max_tokens, payload.temperature, payload.top_p,
    )
    return {
        "responses": responses, "tokens_generated": sum(counts),
        "latency_ms": elapsed * 1000, "throughput_tokens_per_second": throughput,
        "model": model.model_name,
    }

