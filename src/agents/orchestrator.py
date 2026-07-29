from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

BOSS_SYSTEM_PROMPT = """You are the Boss Judge. Your job is to evaluate multiple answers to a question and select the best one.

Evaluate each answer on:
1. Accuracy — is it factually correct?
2. Completeness — does it fully address the question?
3. Clarity — is it well-structured and easy to understand?
4. Relevance — does it stay on topic?

Return ONLY a JSON object with these fields:
- "best_agent": the name of the agent with the best answer
- "reasoning": a brief explanation of why this answer was chosen
- "final_answer": the complete best answer text (use it verbatim or a slightly polished version)
- "runner_up": the name of the second-best agent

Do NOT include any text outside the JSON object."""


def build_judge_prompt(question: str, agent_answers: list[dict[str, Any]]) -> str:
    parts = [f"Question: {question}\n"]
    parts.append("Here are the answers from each agent:\n")
    for a in agent_answers:
        parts.append(f"--- Agent: {a['agent']} (temperature={a['temperature']}) ---\n{a['answer']}\n")
    parts.append("\nEvaluate each answer and select the best one. Return your verdict as JSON.")
    return "\n".join(parts)


def judge(
    generate_fn: callable,
    question: str,
    agent_answers: list[dict[str, Any]],
    max_tokens: int = 1024,
) -> dict[str, Any]:
    judge_prompt = f"{BOSS_SYSTEM_PROMPT}\n\n{build_judge_prompt(question, agent_answers)}"
    responses, counts = generate_fn(
        [judge_prompt],
        max_tokens=max_tokens,
        temperature=0.2,
        top_p=0.9,
    )
    raw = responses[0].strip()
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        result = {
            "best_agent": "unknown",
            "reasoning": "Could not parse judge response. Returning first agent answer.",
            "final_answer": agent_answers[0]["answer"] if agent_answers else "No answers available.",
            "runner_up": agent_answers[1]["agent"] if len(agent_answers) > 1 else "none",
        }
    result["all_answers"] = agent_answers
    result["judge_raw"] = raw
    return result


def multi_agent_generate(
    generate_fn: callable,
    question: str,
    profiles: list[dict[str, Any]] | None = None,
    max_worker_tokens: int = 512,
    max_judge_tokens: int = 1024,
    max_workers: int = 5,
    modality_context: str = "",
) -> dict[str, Any]:
    from .worker import run_workers

    agent_answers = run_workers(
        generate_fn, question, profiles, max_worker_tokens, max_workers, modality_context,
    )
    verdict = judge(generate_fn, question, agent_answers, max_judge_tokens)
    return {
        "question": question,
        "final_answer": verdict.get("final_answer", agent_answers[0]["answer"]),
        "best_agent": verdict.get("best_agent", "unknown"),
        "reasoning": verdict.get("reasoning", ""),
        "agent_answers": agent_answers,
        "num_agents": len(agent_answers),
        "has_modality": bool(modality_context),
    }
