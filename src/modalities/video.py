from __future__ import annotations

import base64
import io
import logging
import os
import tempfile
from typing import Any

import numpy as np

from .vision import describe_image, analyze_image

logger = logging.getLogger(__name__)

MAX_VIDEO_SEC = int(os.getenv("MAX_VIDEO_SECONDS", "30"))
FRAME_INTERVAL_SEC = int(os.getenv("FRAME_INTERVAL_SECONDS", "5"))
MAX_FRAMES = int(os.getenv("MAX_VIDEO_FRAMES", "6"))


def _decode_base64(data: str) -> bytes:
    return base64.b64decode(data)


def _extract_frames(source: str | bytes, interval_sec: int = FRAME_INTERVAL_SEC) -> list[bytes]:
    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV not installed, cannot process video")
        return []

    if isinstance(source, bytes):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(source)
            tmp_path = tmp.name
    else:
        tmp_path = source

    frames: list[bytes] = []
    try:
        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        frame_skip = int(fps * interval_sec)
        count = 0
        while len(frames) < MAX_FRAMES:
            ret, frame = cap.read()
            if not ret:
                break
            if count % frame_skip == 0:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                frames.append(buf.tobytes())
            count += 1
        cap.release()
    finally:
        if isinstance(source, bytes):
            os.unlink(tmp_path)

    return frames


def process_video(source: str | bytes, question: str = "") -> str:
    frames = _extract_frames(source)
    if not frames:
        return "[Video: could not extract frames]"

    descriptions: list[str] = []
    for i, frame_bytes in enumerate(frames):
        desc = describe_image(frame_bytes)
        descriptions.append(f"  Frame {i + 1}: {desc}")

    return (
        f"[Video Analysis: {len(frames)} frames extracted]\n"
        + "\n".join(descriptions)
    )
