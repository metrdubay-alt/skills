"""Модели данных пайплайна. Все сериализуются в JSON-артефакты между этапами."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float | None = None


@dataclass
class Transcript:
    language: str
    segments: list[TranscriptSegment]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Transcript":
        return cls(
            language=d["language"],
            segments=[TranscriptSegment(**s) for s in d["segments"]],
        )


@dataclass
class Frame:
    path: str          # относительный путь внутри output/<video_id>/
    timestamp: float


@dataclass
class Scene:
    scene_id: int
    start: float
    end: float
    frames: list[Frame] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Scene":
        return cls(
            scene_id=d["scene_id"],
            start=d["start"],
            end=d["end"],
            frames=[Frame(**f) for f in d.get("frames", [])],
        )


@dataclass
class Entity:
    type: str                    # protocol | chain | pool | metric | strategy | risk | other
    name: str
    value: str | None = None     # для metric: "12.5% APR", "TVL $4.2M" и т.п.


@dataclass
class SceneVision:
    scene_id: int
    scene_type: str              # talking_head | slide | dashboard | chart | website | table | mixed
    description: str
    screen_text: list[str] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    notable: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SceneVision":
        return cls(
            scene_id=d["scene_id"],
            scene_type=d["scene_type"],
            description=d["description"],
            screen_text=d.get("screen_text", []),
            entities=[Entity(**e) for e in d.get("entities", [])],
            notable=d.get("notable"),
        )


@dataclass
class Segment:
    """Единица итогового представления: сцена + речь + экран."""
    segment_id: int
    start: float
    end: float
    speech: str
    scene_type: str | None = None
    screen_summary: str | None = None
    screen_text: list[str] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    notable: str | None = None
    frame_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
