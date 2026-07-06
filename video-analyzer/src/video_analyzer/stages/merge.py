"""Этап 5: merge — выравнивание транскрипта, сцен и vision-результатов по времени.

Артефакт: segments.json. Чистая логика в build_segments (покрыта тестами).
"""
from __future__ import annotations

import bisect
from pathlib import Path
from typing import Any

from ..models import Scene, SceneVision, Segment, Transcript
from ..pipeline import read_json, write_json


def build_segments(
    transcript: Transcript,
    scenes: list[Scene],
    visions: list[SceneVision],
) -> list[Segment]:
    """Один Segment на сцену: речь распределяется по середине транскрипт-сегмента,
    речь вне сцен прижимается к ближайшей."""
    vision_by_scene = {v.scene_id: v for v in visions}
    scene_starts = [s.start for s in scenes]

    speech_parts: dict[int, list[str]] = {s.scene_id: [] for s in scenes}
    for ts in transcript.segments:
        midpoint = (ts.start + ts.end) / 2
        idx = bisect.bisect_right(scene_starts, midpoint) - 1
        idx = max(0, min(idx, len(scenes) - 1))
        speech_parts[scenes[idx].scene_id].append(ts.text)

    segments: list[Segment] = []
    for scene in scenes:
        v = vision_by_scene.get(scene.scene_id)
        segments.append(Segment(
            segment_id=scene.scene_id,
            start=scene.start,
            end=scene.end,
            speech=" ".join(speech_parts[scene.scene_id]),
            scene_type=v.scene_type if v else None,
            screen_summary=v.description if v else None,
            screen_text=list(v.screen_text) if v else [],
            entities=list(v.entities) if v else [],
            notable=v.notable if v else None,
            frame_refs=[f.path for f in scene.frames],
        ))
    return segments


def run(workdir: Path, config: dict[str, Any]) -> None:
    transcript = Transcript.from_dict(read_json(workdir / "transcript.json"))
    scenes = [Scene.from_dict(d) for d in read_json(workdir / "scenes.json")]
    visions = [SceneVision.from_dict(d) for d in read_json(workdir / "vision.json")]
    segments = build_segments(transcript, scenes, visions)
    write_json(workdir / "segments.json", [s.to_dict() for s in segments])
