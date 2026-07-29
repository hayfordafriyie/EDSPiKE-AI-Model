from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .definitions import AGENT_DEFINITIONS, AgentDefinition

logger = logging.getLogger(__name__)


def _profile_from_def(defn: AgentDefinition) -> dict[str, Any]:
    return {
        "name": defn.name,
        "system": defn.system_prompt,
        "temperature": defn.temperature,
        "top_p": defn.top_p,
        "tools_enabled": defn.tools_enabled,
    }


def get_default_profiles() -> list[dict[str, Any]]:
    return [_profile_from_def(a) for a in AGENT_DEFINITIONS.values()]


def build_agent_prompt(
    profile: dict[str, Any], question: str, modality_context: str = "",
) -> str:
    parts = [profile["system"]]
    if modality_context:
        parts.append(f"\nAdditional context from uploaded files:\n{modality_context}")
    parts.append(f"\nQuestion: {question}\n\nAnswer:")
    return "\n".join(parts)


def generate_worker_answer(
    generate_fn: callable,
    profile: dict[str, Any],
    question: str,
    max_tokens: int = 512,
    modality_context: str = "",
) -> dict[str, Any]:
    prompt = build_agent_prompt(profile, question, modality_context)
    responses, counts = generate_fn(
        [prompt],
        max_tokens=max_tokens,
        temperature=profile["temperature"],
        top_p=profile["top_p"],
    )
    return {
        "agent": profile["name"],
        "answer": responses[0],
        "tokens": counts[0],
        "temperature": profile["temperature"],
        "tools_enabled": profile.get("tools_enabled", False),
    }


def run_workers(
    generate_fn: callable,
    question: str,
    profiles: list[dict[str, Any]] | None = None,
    max_tokens: int = 512,
    max_workers: int = 5,
    modality_context: str = "",
) -> list[dict[str, Any]]:
    if profiles is None:
        profiles = get_default_profiles()
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                generate_worker_answer, generate_fn, p, question, max_tokens, modality_context,
            ): p["name"]
            for p in profiles
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                name = futures[future]
                logger.error("Agent %s failed: %s", name, exc)
                results.append({"agent": name, "answer": f"[Agent error: {exc}]", "tokens": 0, "temperature": 0, "tools_enabled": False})
    results.sort(key=lambda r: r["agent"])
    return results
