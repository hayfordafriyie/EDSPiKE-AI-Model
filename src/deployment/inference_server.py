from __future__ import annotations

import base64
import hmac
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

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
from src.tools import ReActLoop, ToolExecutor
from src.tools.permissions import ApprovalDecision, ApprovalManager
from src.providers import get_provider, SUPPORTED_PROVIDERS

logger = logging.getLogger(__name__)

_approval_manager = ApprovalManager()

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
    images: list[str] | None = Field(default=None)
    audio: list[str] | None = Field(default=None)
    video: list[str] | None = Field(default=None)
    use_tools: bool = Field(default=False)
    approval_mode: str = Field(default="auto")
    workspace_root: str | None = Field(default=None)
    provider: str = Field(default="local")
    api_key: str | None = Field(default=None)
    model: str | None = Field(default=None)

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


class ApproveRequest(BaseModel):
    session_id: str = Field(...)
    action: str = Field(..., pattern=r"^(approve_one|approve_all|reject)$")
    index: int | None = Field(default=None)


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


def _run_generation(gen_fn: callable, prompts: list[str], max_tokens: int, temperature: float, top_p: float):
    started = time.perf_counter()
    responses, counts = gen_fn(prompts, max_tokens, temperature, top_p)
    elapsed = time.perf_counter() - started
    total = sum(counts)
    throughput = total / elapsed if elapsed else 0
    TOKENS.inc(total)
    THROUGHPUT.set(throughput)
    return responses, counts, elapsed, throughput


def _build_modality_context(payload: GenerateRequest) -> str:
    context_parts: list[str] = []
    images = getattr(payload, "images", None)
    audio = getattr(payload, "audio", None)
    video = getattr(payload, "video", None)
    if not any([images, audio, video]):
        return ""
    try:
        from src.modalities import describe_image, transcribe_audio, process_video
    except ImportError:
        logger.warning("modalities module not available")
        return ""
    if images:
        for i, img in enumerate(images):
            try:
                raw = base64.b64decode(img)
                desc = describe_image(raw)
                context_parts.append(f"Image {i + 1}: {desc}")
            except Exception:
                logger.exception("Failed to process image %d", i)
    if audio:
        for i, aud in enumerate(audio):
            try:
                raw = base64.b64decode(aud)
                text = transcribe_audio(raw)
                context_parts.append(f"Audio {i + 1} transcription: {text}")
            except Exception:
                logger.exception("Failed to process audio %d", i)
    if video:
        for i, vid in enumerate(video):
            try:
                raw = base64.b64decode(vid)
                analysis = process_video(raw)
                context_parts.append(f"Video {i + 1}: {analysis}")
            except Exception:
                logger.exception("Failed to process video %d", i)
    return "\n".join(context_parts)


def _resolve_gen_fn(payload: GenerateRequest, local_engine: InferenceEngine | None):
    if payload.provider == "local":
        if local_engine is None:
            raise HTTPException(status_code=503, detail="Local model is not loaded")
        return local_engine.generate_batch, getattr(local_engine, "model_name", "local")
    prov = get_provider(
        provider=payload.provider,
        api_key=payload.api_key or os.getenv(f"{payload.provider.upper()}_API_KEY"),
        model=payload.model,
    )
    return prov.generate_batch, prov.model_name


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
def generate(payload: GenerateRequest, local_engine: Annotated[InferenceEngine | None, Depends(engine)] = None):
    started = time.perf_counter()
    prompts = payload.prompts if payload.prompts else [payload.prompt]
    is_batch = payload.prompts is not None

    gen_fn, model_name = _resolve_gen_fn(payload, local_engine)

    if payload.use_tools and not is_batch and payload.prompt:
        exec_roots = [payload.workspace_root] if payload.workspace_root else None
        executor = ToolExecutor(allowed_roots=exec_roots)

        if payload.approval_mode == "manual":
            schemas = json.dumps([{
                "name": t.name, "description": t.description, "parameters": t.parameters,
            } for t in __import__("src.tools.registry", fromlist=[""]).BUILTIN_TOOLS])
            system = (
                f"You are an AI coding agent with access to tools.\n\n"
                f"## Available Tools\n{schemas}\n\n"
                f"## How to use tools\n"
                f'<tool_call>\n{{"name": "tool_name", "arguments": {{...}}}}\n</tool_call>\n\n'
                f"Workspace: {payload.workspace_root or '.'}\n\nBegin."
            )
            messages = [system, f"## Task\n{payload.prompt}"]
            sid = _approval_manager.create_session(
                generate_fn=gen_fn, executor=executor, messages=messages,
                max_tokens=payload.max_tokens * 4, temperature=payload.temperature,
            )
            result = _approval_manager._run_next_turn(_approval_manager._sessions[sid])
            result["model"] = model_name
            result["provider"] = payload.provider
            return result

        loop = ReActLoop(generate_fn=gen_fn, executor=executor, workspace=payload.workspace_root or ".")
        react_result = loop.run(
            question=payload.prompt, max_tokens=payload.max_tokens * 4, temperature=payload.temperature,
        )
        return {
            "response": react_result.final_answer,
            "tokens_generated": react_result.total_tokens,
            "latency_ms": (time.perf_counter() - started) * 1000,
            "model": model_name, "provider": payload.provider,
            "mode": "tool_react", "turns": len(react_result.turns),
        }

    modality_context = _build_modality_context(payload)

    if payload.num_agents <= 1:
        if modality_context and prompts:
            prompts = [f"{p}\n\n{modality_context}" for p in prompts]
        responses, counts, elapsed, throughput = _run_generation(gen_fn, prompts, payload.max_tokens, payload.temperature, payload.top_p)
        result = {
            "latency_ms": elapsed * 1000, "throughput_tokens_per_second": throughput,
            "model": model_name, "provider": payload.provider,
        }
        if is_batch:
            result["responses"] = responses
            result["tokens_generated"] = sum(counts)
        else:
            result["response"] = responses[0]
            result["tokens_generated"] = counts[0]
    else:
        result = multi_agent_generate(
            generate_fn=gen_fn, question=payload.prompt or prompts[0],
            profiles=AGENT_PROFILES[:payload.num_agents],
            max_worker_tokens=payload.max_worker_tokens or payload.max_tokens,
            max_judge_tokens=payload.max_judge_tokens or payload.max_tokens * 2,
            max_workers=payload.num_agents, modality_context=modality_context,
        )
        result["latency_ms"] = (time.perf_counter() - started) * 1000
        result["model"] = model_name
        result["provider"] = payload.provider
    return result


@app.post("/v1/approve", dependencies=[Depends(require_api_key)])
def approve(payload: ApproveRequest):
    decision = ApprovalDecision(payload.action)
    result = _approval_manager.decide(payload.session_id, decision, payload.index)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
