import pytest

from src.speech import SpeechEngine, VoiceProfile


class TestSpeech:
    def test_speak_no_tts(self):
        engine = SpeechEngine()
        if not engine._tts_available:
            result = engine.speak("hello")
            assert "available" in result.lower() or "error" in result.lower()
        else:
            result = engine.speak("hello")
            assert isinstance(result, str)

    def test_set_profile(self):
        engine = SpeechEngine()
        profile = VoiceProfile(name="test", lang="fr-FR", speed=1.5)
        engine.set_profile(profile)
        assert engine._profile.name == "test"
