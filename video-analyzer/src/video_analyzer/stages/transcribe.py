"""Этап 2: транскрипция через faster-whisper.

Артефакты: transcript.json, transcript.srt.
GPU (cuda) с автоматическим фолбэком на CPU, если CUDA/cuDNN недоступны.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..models import Transcript, TranscriptSegment
from ..pipeline import write_json

log = logging.getLogger("video_analyzer")


def _load_model(model_name: str, device: str):
    from faster_whisper import WhisperModel

    attempts = (
        [("cuda", "int8_float16"), ("cpu", "int8")] if device in ("auto", "cuda")
        else [("cpu", "int8")]
    )
    last_error: Exception | None = None
    for dev, compute_type in attempts:
        try:
            model = WhisperModel(model_name, device=dev, compute_type=compute_type)
            log.info("whisper %s загружен на %s (%s)", model_name, dev, compute_type)
            return model
        except Exception as e:  # ctranslate2 кидает RuntimeError при проблемах с CUDA
            log.warning("не удалось загрузить whisper на %s: %s", dev, e)
            last_error = e
    raise RuntimeError(f"Не удалось загрузить модель whisper: {last_error}")


def _format_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(transcript: Transcript) -> str:
    lines = []
    for i, seg in enumerate(transcript.segments, 1):
        lines.append(str(i))
        lines.append(f"{_format_ts(seg.start)} --> {_format_ts(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def run(workdir: Path, config: dict[str, Any]) -> None:
    wcfg = config["whisper"]
    model = _load_model(wcfg["model"], wcfg["device"])

    segments_iter, info = model.transcribe(
        str(workdir / "audio.wav"),
        language=wcfg.get("language"),
        word_timestamps=False,
        vad_filter=True,
    )

    segments = [
        TranscriptSegment(
            start=round(s.start, 2),
            end=round(s.end, 2),
            text=s.text.strip(),
            confidence=round(float(s.avg_logprob), 3) if s.avg_logprob is not None else None,
        )
        for s in segments_iter
        if s.text.strip()
    ]
    transcript = Transcript(language=info.language, segments=segments)
    log.info("транскрипция: язык=%s, сегментов=%d", info.language, len(segments))

    write_json(workdir / "transcript.json", transcript.to_dict())
    (workdir / "transcript.srt").write_text(to_srt(transcript), encoding="utf-8")
