from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Any

MODELS_CACHE: dict[str, Any] = {}
LOCK = threading.Lock()


@dataclass
class ModalityModels:
    vit_processor: Any = None
    vit_model: Any = None
    whisper_processor: Any = None
    whisper_model: Any = None
    device: str = "cpu"

    @property
    def ready(self) -> bool:
        return self.vit_model is not None or self.whisper_model is not None


def _get_device() -> str:
    return os.getenv("DEVICE", "cpu").lower()


def _load_vit() -> tuple[Any, Any]:
    from transformers import AutoProcessor, AutoModel
    model_name = os.getenv("VISION_MODEL", "openai/clip-vit-base-patch32")
    device = _get_device()
    dtype = {"device_map": None} if device == "cpu" else {}
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=False)
    model = AutoModel.from_pretrained(model_name, trust_remote_code=False, **dtype)
    model = model.to(device)
    model.eval()
    return processor, model


def _load_whisper() -> tuple[Any, Any]:
    from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
    model_name = os.getenv("AUDIO_MODEL", "openai/whisper-tiny.en")
    device = _get_device()
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=False)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_name,
        trust_remote_code=False,
        device_map=None if device == "cpu" else "auto",
        low_cpu_mem_usage=True,
    )
    if device == "cpu":
        model = model.to("cpu")
    model.eval()
    return processor, model


def get_modality_models() -> ModalityModels:
    with LOCK:
        if "modality_models" in MODELS_CACHE:
            return MODELS_CACHE["modality_models"]
        models = ModalityModels(device=_get_device())
        if os.getenv("ENABLE_VISION", "true").lower() == "true":
            try:
                models.vit_processor, models.vit_model = _load_vit()
            except Exception:
                pass
        if os.getenv("ENABLE_AUDIO", "true").lower() == "true":
            try:
                models.whisper_processor, models.whisper_model = _load_whisper()
            except Exception:
                pass
        MODELS_CACHE["modality_models"] = models
        return models
