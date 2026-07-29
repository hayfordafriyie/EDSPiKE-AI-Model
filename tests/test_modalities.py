from __future__ import annotations

import base64
import io

import pytest
from PIL import Image

from src.agents.worker import AGENT_PROFILES, build_agent_prompt

pytest.importorskip("PIL")

MULTIMODAL_AGENT_NAMES = {"Visual", "Auditory"}


def test_multimodal_agent_profiles_present():
    names = {p["name"] for p in AGENT_PROFILES}
    assert "Visual" in names
    assert "Auditory" in names


def test_agent_prompt_with_modality_context():
    profile = {"name": "Test", "system": "You are a test agent."}
    prompt = build_agent_prompt(profile, "What is this?", "Image: [photo]")
    assert "Image: [photo]" in prompt
    assert "What is this?" in prompt
    assert "You are a test agent." in prompt


def test_agent_prompt_without_modality_context():
    profile = {"name": "Test", "system": "You are a test agent."}
    prompt = build_agent_prompt(profile, "Hello")
    assert "Additional context" not in prompt


def test_agent_profiles_include_visual_and_auditory():
    visual = next(p for p in AGENT_PROFILES if p["name"] == "Visual")
    assert "visual" in visual["system"].lower()
    auditory = next(p for p in AGENT_PROFILES if p["name"] == "Auditory")
    assert "audio" in auditory["system"].lower()


def test_build_modality_context_empty():
    pytest.importorskip("dotenv")
    from src.deployment.inference_server import _build_modality_context

    class FakeRequest:
        images = None
        audio = None
        video = None
    ctx = _build_modality_context(FakeRequest())
    assert ctx == ""


def test_vision_describe_empty_models(monkeypatch):
    monkeypatch.setenv("ENABLE_VISION", "false")
    monkeypatch.setenv("ENABLE_AUDIO", "false")
    from src.modalities.vision import describe_image
    img = Image.new("RGB", (100, 100), color="red")
    result = describe_image(img)
    assert result == ""


def test_vision_analyze_empty_models(monkeypatch):
    monkeypatch.setenv("ENABLE_VISION", "false")
    monkeypatch.setenv("ENABLE_AUDIO", "false")
    from src.modalities.vision import analyze_image
    img = Image.new("RGB", (100, 100), color="blue")
    result = analyze_image(img)
    assert result == ""
