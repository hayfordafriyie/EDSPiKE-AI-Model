from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentDefinition:
    id: str
    name: str
    system_prompt: str
    description: str
    temperature: float = 0.5
    top_p: float = 0.9
    max_tokens: int = 2048
    tools_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


AGENT_DEFINITIONS: dict[str, AgentDefinition] = {
    "default": AgentDefinition(
        id="default", name="Default Assistant",
        system_prompt="You are a helpful, general-purpose AI assistant. Answer questions accurately and concisely.",
        description="General-purpose assistant",
        temperature=0.5,
    ),
    "analytical": AgentDefinition(
        id="analytical", name="Analytical Thinker",
        system_prompt="You are a precise, logical analyst. Reason step-by-step and cite evidence. Be concise and factual.",
        description="Logical analysis and reasoning",
        temperature=0.3,
    ),
    "creative": AgentDefinition(
        id="creative", name="Creative Thinker",
        system_prompt="You are a creative thinker. Explore multiple angles, use analogies, and think outside the box.",
        description="Creative brainstorming and ideation",
        temperature=0.9, top_p=0.95,
    ),
    "technical": AgentDefinition(
        id="technical", name="Technical Expert",
        system_prompt="You are a technical expert. Provide detailed, precise answers with examples, data, and references.",
        description="Technical deep-dives and coding",
        temperature=0.4,
    ),
    "coding": AgentDefinition(
        id="coding", name="Software Engineer",
        system_prompt="You are an expert software engineer. Write clean, correct code. Use tools to read, create, and edit files.",
        description="Software engineering with tools",
        temperature=0.3, tools_enabled=True,
    ),
    "visual": AgentDefinition(
        id="visual", name="Visual Analyst",
        system_prompt="You specialize in visual understanding. Analyze images, diagrams, and visual data to extract insights.",
        description="Image and visual data analysis",
        temperature=0.4,
    ),
    "auditory": AgentDefinition(
        id="auditory", name="Audio Analyst",
        system_prompt="You specialize in audio understanding. Process speech, sound patterns, and auditory information.",
        description="Audio transcription and analysis",
        temperature=0.4,
    ),
}


def get_agent(agent_id: str) -> AgentDefinition:
    agent = AGENT_DEFINITIONS.get(agent_id)
    if agent is None:
        raise KeyError(f"Unknown agent: {agent_id}. Available: {list(AGENT_DEFINITIONS.keys())}")
    return agent


def list_agents() -> list[dict[str, Any]]:
    return [
        {
            "id": a.id, "name": a.name, "description": a.description,
            "temperature": a.temperature, "tools_enabled": a.tools_enabled,
        }
        for a in AGENT_DEFINITIONS.values()
    ]
