from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logger = logging.getLogger(__name__)

AGENT_PROFILES = [
    {
        "name": "Analytical",
        "system": "You are a precise, logical analyst. Reason step-by-step and cite evidence. Be concise and factual.",
        "temperature": 0.3,
        "top_p": 0.9,
    },
    {
        "name": "Creative",
        "system": "You are a creative thinker. Explore multiple angles, use analogies, and think outside the box.",
        "temperature": 0.9,
        "top_p": 0.95,
    },
    {
        "name": "Technical",
        "system": "You are a technical expert. Provide detailed, precise answers with examples, data, and references where relevant.",
        "temperature": 0.4,
        "top_p": 0.9,
    },
    {
        "name": "Practical",
        "system": "You are a pragmatic problem-solver. Focus on actionable, real-world solutions and keep explanations simple.",
        "temperature": 0.5,
        "top_p": 0.92,
    },
    {
        "name": "Critical",
        "system": "You are a critical reviewer. Challenge assumptions, identify weaknesses, and provide balanced counterpoints.",
        "temperature": 0.7,
        "top_p": 0.93,
    },
    {
        "name": "Visual",
        "system": "You specialize in visual understanding. Analyze images, diagrams, and visual data to extract insights and patterns.",
        "temperature": 0.4,
        "top_p": 0.92,
    },
    {
        "name": "Auditory",
        "system": "You specialize in audio understanding. Process speech, sound patterns, and auditory information with precision.",
        "temperature": 0.4,
        "top_p": 0.92,
    },
]


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
        profiles = AGENT_PROFILES
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
                results.append({"agent": name, "answer": f"[Agent error: {exc}]", "tokens": 0, "temperature": 0})
    results.sort(key=lambda r: r["agent"])
    return results
