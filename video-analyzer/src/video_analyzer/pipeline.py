"""Запуск этапов пайплайна с кэшированием артефактов.

Каждый этап объявляет свой выходной артефакт. Если файл уже существует —
этап пропускается. `--force <stage>` перезапускает этап и все последующие.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("video_analyzer")


@dataclass
class Stage:
    name: str
    artifact: str                                   # имя файла-маркера готовности этапа
    run: Callable[[Path, dict[str, Any]], None]     # (workdir, config) -> None


def run_pipeline(
    stages: list[Stage],
    workdir: Path,
    config: dict[str, Any],
    force_from: str | None = None,
) -> None:
    workdir.mkdir(parents=True, exist_ok=True)
    stage_names = [s.name for s in stages]
    if force_from is not None and force_from not in stage_names:
        raise ValueError(f"Неизвестный этап '{force_from}'. Доступные: {stage_names}")

    forcing = False
    for stage in stages:
        if stage.name == force_from:
            forcing = True
        artifact_path = workdir / stage.artifact
        if artifact_path.exists() and not forcing:
            log.info("[%s] пропущен — артефакт %s уже есть", stage.name, stage.artifact)
            continue
        log.info("[%s] запуск...", stage.name)
        t0 = time.monotonic()
        stage.run(workdir, config)
        if not artifact_path.exists():
            raise RuntimeError(
                f"Этап '{stage.name}' завершился, но артефакт {stage.artifact} не создан"
            )
        log.info("[%s] готово за %.1f c", stage.name, time.monotonic() - t0)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
