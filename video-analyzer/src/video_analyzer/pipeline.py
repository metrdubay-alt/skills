"""Pipeline runner with artifact-based stage caching."""
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
    artifact: str | tuple[str, ...]
    run: Callable[[Path, dict[str, Any]], None]


def _artifact_names(stage: Stage) -> tuple[str, ...]:
    if isinstance(stage.artifact, str):
        return (stage.artifact,)
    return stage.artifact


def run_pipeline(
    stages: list[Stage],
    workdir: Path,
    config: dict[str, Any],
    force_from: str | None = None,
) -> None:
    workdir.mkdir(parents=True, exist_ok=True)
    stage_names = [s.name for s in stages]
    if force_from is not None and force_from not in stage_names:
        raise ValueError(f"Unknown stage '{force_from}'. Available: {stage_names}")

    forcing = False
    for stage in stages:
        if stage.name == force_from:
            forcing = True

        artifact_names = _artifact_names(stage)
        artifact_paths = [workdir / artifact for artifact in artifact_names]
        if all(path.exists() for path in artifact_paths) and not forcing:
            log.info("[%s] skipped - artifact(s) %s already exist", stage.name, artifact_names)
            continue

        log.info("[%s] start...", stage.name)
        t0 = time.monotonic()
        stage.run(workdir, config)
        missing = [name for name, path in zip(artifact_names, artifact_paths) if not path.exists()]
        if missing:
            raise RuntimeError(f"Stage '{stage.name}' finished but artifact(s) {missing} were not created")
        log.info("[%s] done in %.1f s", stage.name, time.monotonic() - t0)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
