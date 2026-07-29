from __future__ import annotations

import base64
import io
import logging
import os
from typing import Any

import numpy as np

from .models import get_modality_models

logger = logging.getLogger(__name__)

MAX_AUDIO_SEC = int(os.getenv("MAX_AUDIO_SECONDS", "30"))


def _load_audio(source: str | bytes | np.ndarray) -> tuple[np.ndarray, int]:
    if isinstance(source, np.ndarray):
        return source, 16000
    if isinstance(source, bytes):
        import soundfile as sf
        audio, sr = sf.read(io.BytesIO(source))
        return audio, sr
    if source.startswith(("http://", "https://")):
        import requests
        resp = requests.get(source, timeout=60)
        resp.raise_for_status()
        import soundfile as sf
        audio, sr = sf.read(io.BytesIO(resp.content))
        return audio, sr
    import soundfile as sf
    audio, sr = sf.read(source)
    return audio, sr


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    import torchaudio.functional as F
    import torch
    tensor = torch.from_numpy(audio).float()
    resampled = F.resample(tensor, orig_sr, target_sr)
    return resampled.numpy()


def _to_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim > 1:
        return audio.mean(axis=1)
    return audio


def _decode_base64(data: str) -> bytes:
    return base64.b64decode(data)


def transcribe_audio(source: str | bytes | np.ndarray) -> str:
    models = get_modality_models()
    if models.whisper_model is None:
        return ""
    audio_array, sr = _load_audio(source)
    audio_array = _to_mono(audio_array)
    if sr != 16000:
        audio_array = _resample(audio_array, sr, 16000)
    max_samples = MAX_AUDIO_SEC * 16000
    if len(audio_array) > max_samples:
        audio_array = audio_array[:max_samples]

    import torch
    inputs = models.whisper_processor(
        audio_array, sampling_rate=16000, return_tensors="pt"
    )
    input_features = inputs.input_features.to(models.device)
    with torch.inference_mode():
        predicted_ids = models.whisper_model.generate(input_features)
    transcription = models.whisper_processor.batch_decode(
        predicted_ids, skip_special_tokens=True
    )[0]
    return transcription.strip()
