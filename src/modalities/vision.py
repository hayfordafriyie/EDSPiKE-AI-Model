from __future__ import annotations

import base64
import io
import logging
import os
from typing import Any

import numpy as np
from PIL import Image

from .models import get_modality_models

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "1024"))


def _load_image(source: str | bytes | Image.Image) -> Image.Image:
    if isinstance(source, Image.Image):
        return source
    if isinstance(source, bytes):
        return Image.open(io.BytesIO(source))
    if source.startswith(("http://", "https://")):
        import requests
        resp = requests.get(source, timeout=30)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content))
    return Image.open(source)


def _resize(image: Image.Image) -> Image.Image:
    w, h = image.size
    if max(w, h) > MAX_IMAGE_SIZE:
        ratio = MAX_IMAGE_SIZE / max(w, h)
        image = image.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    return image


def _decode_base64(data: str) -> bytes:
    return base64.b64decode(data)


def describe_image(source: str | bytes | Image.Image) -> str:
    models = get_modality_models()
    if models.vit_model is None:
        return ""
    image = _load_image(source)
    image = _resize(image)
    import torch
    inputs = models.vit_processor(images=image, return_tensors="pt").to(models.device)
    with torch.inference_mode():
        outputs = models.vit_model.get_image_features(**inputs)
    return _image_to_text(outputs, image)


def _image_to_text(features: Any, image: Image.Image) -> str:
    w, h = image.size
    mean = features.cpu().float().mean().item()
    std = features.cpu().float().std().item()
    return (
        f"[Image: {w}x{h}px, visual complexity={mean:.2f}, "
        f"feature variance={std:.2f}]"
    )


def analyze_image(source: str | bytes | Image.Image, question: str = "") -> str:
    models = get_modality_models()
    if models.vit_model is None:
        return ""
    image = _load_image(source)
    image = _resize(image)
    import torch
    inputs = models.vit_processor(
        text=question if question else "Describe this image",
        images=image,
        return_tensors="pt",
        padding=True,
    ).to(models.device)
    with torch.inference_mode():
        outputs = models.vit_model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=-1)
    values, indices = torch.topk(probs, k=min(5, probs.size(-1)))
    concepts = [f"concept_{i}: {v:.3f}" for i, v in zip(indices[0].tolist(), values[0].tolist())]
    w, h = image.size
    return (
        f"[Image Analysis: {w}x{h}px, top concepts: {', '.join(concepts)}]"
    )
