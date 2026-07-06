"""Этап 4: анализ ключевых кадров через LLM vision.

Батчами по N кадров; в промпт передаётся фрагмент транскрипта каждой сцены,
чтобы модель сразу связывала речь и экран. Артефакт: vision.json.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..llm_client import LLMClient, image_block
from ..models import Scene, Transcript
from ..pipeline import read_json, write_json

log = logging.getLogger("video_analyzer")

VISION_SCHEMA = {
    "type": "object",
    "properties": {
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_id": {"type": "integer"},
                    "scene_type": {
                        "type": "string",
                        "enum": ["talking_head", "slide", "dashboard", "chart",
                                 "website", "table", "code", "mixed", "other"],
                    },
                    "description": {"type": "string"},
                    "screen_text": {"type": "array", "items": {"type": "string"}},
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["protocol", "chain", "pool", "metric",
                                             "strategy", "risk", "token", "other"],
                                },
                                "name": {"type": "string"},
                                "value": {"type": ["string", "null"]},
                            },
                            "required": ["type", "name", "value"],
                            "additionalProperties": False,
                        },
                    },
                    "notable": {"type": ["string", "null"]},
                },
                "required": ["scene_id", "scene_type", "description",
                             "screen_text", "entities", "notable"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["scenes"],
    "additionalProperties": False,
}

SYSTEM = """Ты анализируешь ключевые кадры из аналитического видео (DeFi, крипто, финансы, подкасты).
Для каждой сцены извлеки максимум фактов с экрана:
- scene_type: тип сцены;
- description: что на экране (1-3 предложения, конкретно: названия, цифры);
- screen_text: важный текст с экрана дословно (заголовки, метрики, названия пулов, APR/APY/TVL, тикеры). Не переписывай весь UI — только информативное;
- entities: нормализованные сущности (protocol/chain/pool/metric/strategy/risk/token). Для metric указывай value ("APR 12.5%", "TVL $4.2M");
- notable: что здесь важно в контексте речи автора (или null).
Для talking_head без полезного экранного контента: короткое description, пустые списки.
Отвечай на языке транскрипта."""


def speech_for_scene(transcript: Transcript, start: float, end: float, limit: int = 1500) -> str:
    parts = [
        s.text for s in transcript.segments
        if start <= (s.start + s.end) / 2 < end
    ]
    text = " ".join(parts)
    return text[:limit]


def run(workdir: Path, config: dict[str, Any]) -> None:
    scenes = [Scene.from_dict(d) for d in read_json(workdir / "scenes.json")]
    transcript = Transcript.from_dict(read_json(workdir / "transcript.json"))
    client = LLMClient(config["provider"], config["model"])
    batch_size = config["vision"]["batch_size"]

    # сцены с кадрами; сцены без кадров (дедуп убрал все) пропускаем
    scenes_with_frames = [s for s in scenes if s.frames]
    results: list[dict[str, Any]] = []

    for i in range(0, len(scenes_with_frames), batch_size):
        batch = scenes_with_frames[i:i + batch_size]
        content: list[dict[str, Any]] = []
        for scene in batch:
            speech = speech_for_scene(transcript, scene.start, scene.end)
            content.append({
                "type": "text",
                "text": (
                    f"--- Сцена {scene.scene_id} "
                    f"({scene.start:.0f}s–{scene.end:.0f}s) ---\n"
                    f"Речь автора в этой сцене: {speech or '(нет речи)'}\n"
                    f"Кадры сцены ({len(scene.frames)}):"
                ),
            })
            for frame in scene.frames:
                content.append(image_block(workdir / frame.path))
        content.append({
            "type": "text",
            "text": "Проанализируй каждую сцену выше и верни результат по схеме.",
        })

        result = client.structured(
            content,
            VISION_SCHEMA,
            system=SYSTEM,
            max_tokens=8000,
            schema_name="vision_scenes",
        )
        results.extend(result["scenes"])
        log.info(
            "vision: сцены %s обработаны (%d/%d), стоимость %s",
            [s.scene_id for s in batch], min(i + batch_size, len(scenes_with_frames)),
            len(scenes_with_frames), client.cost_label,
        )

    log.info(
        "vision итог: %d сцен, %d in / %d out токенов, стоимость %s",
        len(results), client.input_tokens, client.output_tokens, client.cost_label,
    )
    write_json(workdir / "vision.json", results)
    write_json(workdir / "vision_usage.json", {
        "input_tokens": client.input_tokens,
        "output_tokens": client.output_tokens,
        "cost_usd": None if client.cost_usd is None else round(client.cost_usd, 4),
    })
