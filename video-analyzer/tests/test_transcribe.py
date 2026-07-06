import sys
import types
from types import SimpleNamespace

from video_analyzer.stages import transcribe


def test_transcribe_disables_vad_by_default(monkeypatch, tmp_path):
    captured = {}

    class FakeWhisperModel:
        def __init__(self, model_name, device, compute_type):
            pass

        def transcribe(self, audio_path, language, word_timestamps, vad_filter):
            captured["vad_filter"] = vad_filter
            segment = SimpleNamespace(
                start=0.0,
                end=1.0,
                text=" hello ",
                avg_logprob=-0.1,
            )
            info = SimpleNamespace(language="en")
            return [segment], info

    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        types.SimpleNamespace(WhisperModel=FakeWhisperModel),
    )
    (tmp_path / "audio.wav").write_bytes(b"fake audio")

    transcribe.run(tmp_path, {"whisper": {"model": "tiny", "device": "cpu"}})

    assert captured["vad_filter"] is False
