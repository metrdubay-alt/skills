"""Этап 6: генерация итогового документа.

LLM получает segments.json целиком и собирает детальный Markdown-документ.
Артефакты: document.md, analysis.json.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..llm_client import LLMClient
from ..docx_export import markdown_to_docx
from ..pipeline import read_json, write_json

log = logging.getLogger("video_analyzer")

DOC_SYSTEM_RU = """Ты — аналитик, который превращает данные видеоанализа в детальный рабочий документ.
Вход: сегменты видео (речь автора + данные с экрана + сущности), метаданные.
Собери Markdown-документ со структурой:

# <Название видео>
## Метаданные
## Краткое резюме (5-10 предложений: о чём видео и главные выводы)
## Хронология
Для каждого содержательного отрезка: `**MM:SS–MM:SS**` — что говорит автор, что на экране (конкретные цифры и названия), почему это важно. Соседние сегменты с одной темой объединяй. Таймкоды бери ДОСЛОВНО из поля `timecode` сегментов — не пересчитывай их сам.
## Ключевые тезисы и стратегии
Пронумерованный список главных утверждений автора с таймкодами и экранными подтверждениями.
## Сущности и цифры
Таблица: тип | название | значение | таймкод.
## Риски и оговорки
Что автор называет рисками, где он не уверен, что противоречиво.

Правила: пиши на русском, но термины, тикеры, названия протоколов — в оригинале. Не выдумывай факты, которых нет в данных. Если экранные данные противоречат речи — отметь это. Сохраняй ВСЕ конкретные цифры (APR, TVL, цены, проценты)."""

DOC_SYSTEM_EN = DOC_SYSTEM_RU + "\n\nOVERRIDE: write the document in English."


def _fmt_ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def run(workdir: Path, config: dict[str, Any]) -> None:
    meta = read_json(workdir / "meta.json")
    segments = read_json(workdir / "segments.json")
    transcript = read_json(workdir / "transcript.json")

    client = LLMClient(config["provider"], config["model"])
    system = DOC_SYSTEM_EN if config.get("doc_language") == "en" else DOC_SYSTEM_RU

    # таймкоды конвертируются в MM:SS здесь — LLM-арифметика по секундам ненадёжна
    payload_segments = [
        {**seg, "timecode": f"{_fmt_ts(seg['start'])}–{_fmt_ts(seg['end'])}"}
        for seg in segments
    ]
    for seg in payload_segments:
        seg.pop("start", None)
        seg.pop("end", None)
        seg.pop("frame_refs", None)

    payload = {
        "metadata": meta["source_meta"],
        "segments": payload_segments,
    }
    content = [{
        "type": "text",
        "text": (
            "Данные анализа видео (JSON):\n\n"
            + json.dumps(payload, ensure_ascii=False)
            + "\n\nСобери итоговый документ по инструкции."
        ),
    }]
    body = client.generate(content, system=system, max_tokens=32000)
    log.info(
        "document: %d in / %d out токенов, стоимость %s",
        client.input_tokens, client.output_tokens, client.cost_label,
    )

    # приложение: полный транскрипт
    appendix_lines = ["", "---", "", "## Приложение: полный транскрипт", ""]
    for seg in transcript["segments"]:
        appendix_lines.append(f"`{_fmt_ts(seg['start'])}` {seg['text']}")
    document = body + "\n".join(appendix_lines) + "\n"

    (workdir / "document.md").write_text(document, encoding="utf-8")
    markdown_to_docx(document, workdir / "document.docx")
    write_json(workdir / "analysis.json", {
        "video_id": meta["video_id"],
        "source": meta["source"],
        "metadata": meta["source_meta"],
        "language": transcript["language"],
        "segments": segments,
        "usage": {
            "document_input_tokens": client.input_tokens,
            "document_output_tokens": client.output_tokens,
            "document_cost_usd": None if client.cost_usd is None else round(client.cost_usd, 4),
        },
    })
