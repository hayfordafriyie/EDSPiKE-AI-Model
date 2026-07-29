from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VoiceProfile:
    name: str
    lang: str = "en-US"
    speed: float = 1.0
    pitch: float = 1.0


class SpeechEngine:
    def __init__(self):
        self._profile = VoiceProfile(name="default")
        self._tts_available = self._check_tts()
        self._stt_available = self._check_stt()

    def _check_tts(self) -> bool:
        for cmd in ["espeak", "say", "festival"]:
            try:
                subprocess.run([cmd, "--version"], capture_output=True, timeout=2)
                return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return False

    def _check_stt(self) -> bool:
        try:
            import speech_recognition
            return True
        except ImportError:
            return False

    def speak(self, text: str, profile: VoiceProfile | None = None) -> str:
        p = profile or self._profile
        if not self._tts_available:
            return "TTS not available. Install espeak, say (macOS), or festival."

        try:
            if subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
                result = subprocess.run(
                    ["espeak", "-s", str(int(p.speed * 175)), text],
                    capture_output=True, text=True, timeout=30,
                )
            elif subprocess.run(["which", "say"], capture_output=True).returncode == 0:
                result = subprocess.run(["say", text], capture_output=True, text=True, timeout=30)
            else:
                return "No TTS engine found"
            return f"Spoken: {text}" if result.returncode == 0 else f"TTS error: {result.stderr}"
        except Exception as e:
            return f"TTS error: {e}"

    def listen(self, timeout: float = 5.0) -> str:
        if not self._stt_available:
            return "STT not available. Install speech_recognition: pip install SpeechRecognition"
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=timeout)
            return r.recognize_google(audio)
        except ImportError:
            return "speech_recognition not installed"
        except Exception as e:
            return f"STT error: {e}"

    def set_profile(self, profile: VoiceProfile) -> None:
        self._profile = profile
