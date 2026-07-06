"""Этап 3: детекция сцен (PySceneDetect) + ключевые кадры с дедупом по phash.

Артефакты: scenes.json, frames/*.jpg.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from ..models import Frame, Scene
from ..pipeline import write_json

log = logging.getLogger("video_analyzer")


def frame_timestamps(start: float, end: float, max_interval: float) -> list[float]:
    """Таймстампы ключевых кадров сцены: середина для коротких сцен,
    равномерная сетка для длинных."""
    duration = end - start
    if duration <= 0:
        return [start]
    n = max(1, math.ceil(duration / max_interval))
    return [round(start + duration * (i + 0.5) / n, 2) for i in range(n)]


def _hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def dedupe_hashes(hashes: list[str], max_distance: int) -> list[int]:
    """Индексы кадров, которые стоит оставить: кадр выбрасывается, если его
    phash ближе max_distance к любому уже оставленному."""
    kept: list[int] = []
    for i, h in enumerate(hashes):
        if all(_hamming(h, hashes[k]) > max_distance for k in kept):
            kept.append(i)
    return kept


def scene_boundaries(video_path: str, scfg: dict[str, Any], duration: float) -> list[tuple[float, float]]:
    if not scfg.get("detect", True):
        return [(0.0, duration)]

    from scenedetect import ContentDetector, detect

    scene_list = detect(str(video_path), ContentDetector(threshold=scfg["threshold"]))
    if not scene_list:
        return [(0.0, duration)]
    return [(s.get_seconds(), e.get_seconds()) for s, e in scene_list]


def run(workdir: Path, config: dict[str, Any]) -> None:
    import cv2
    import imagehash
    from PIL import Image
    from scenedetect import ContentDetector, detect
    from ..pipeline import read_json

    scfg = config["scenes"]
    video_path = Path(read_json(workdir / "meta.json")["video_path"])

    if not scfg.get("detect", True):
        duration = float(read_json(workdir / "meta.json")["ffprobe"]["format"]["duration"])
        boundaries = scene_boundaries(str(video_path), scfg, duration)
        log.info("fast scene sampling: %d scene(s)", len(boundaries))

        frames_dir = workdir / "frames"
        frames_dir.mkdir(exist_ok=True)
        cap = cv2.VideoCapture(str(video_path))
        scenes = [Scene(scene_id=i, start=round(s, 2), end=round(e, 2)) for i, (s, e) in enumerate(boundaries)]
        try:
            max_width = config["vision"]["max_frame_width"]
            for scene_idx, (start, end) in enumerate(boundaries):
                for ts in frame_timestamps(start, end, scfg["max_frame_interval"]):
                    cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
                    ok, frame = cap.read()
                    if not ok:
                        continue
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    if img.width > max_width:
                        img = img.resize((max_width, int(img.height * max_width / img.width)))
                    rel_path = f"frames/scene{scene_idx:04d}_{int(ts * 1000):09d}.jpg"
                    img.save(workdir / rel_path, quality=85)
                    scenes[scene_idx].frames.append(Frame(path=rel_path, timestamp=ts))
        finally:
            cap.release()

        total_frames = sum(len(s.frames) for s in scenes)
        log.info("fast scene frames: %d", total_frames)
        write_json(workdir / "scenes.json", [s.to_dict() for s in scenes])
        return

    scene_list = detect(str(video_path), ContentDetector(threshold=scfg["threshold"]))
    if not scene_list:
        # видео без монтажных склеек (одна статичная сцена) — берём всё видео целиком
        duration = float(read_json(workdir / "meta.json")["ffprobe"]["format"]["duration"])
        boundaries = [(0.0, duration)]
    else:
        boundaries = [(s.get_seconds(), e.get_seconds()) for s, e in scene_list]
    log.info("сцен обнаружено: %d", len(boundaries))

    frames_dir = workdir / "frames"
    frames_dir.mkdir(exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    try:
        # собираем кандидатов по всем сценам, затем глобальный дедуп по phash
        candidates: list[tuple[int, float]] = []  # (scene_idx, timestamp)
        for idx, (start, end) in enumerate(boundaries):
            for ts in frame_timestamps(start, end, scfg["max_frame_interval"]):
                candidates.append((idx, ts))

        hashes: list[str] = []
        images: list[Image.Image | None] = []
        for _, ts in candidates:
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
            ok, frame = cap.read()
            if not ok:
                hashes.append("f" * 16)  # маркер битого кадра — гарантированно уникален редко
                images.append(None)
                continue
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            hashes.append(str(imagehash.phash(img)))
            images.append(img)

        kept = set(dedupe_hashes(hashes, scfg["phash_distance"]))

        max_width = config["vision"]["max_frame_width"]
        scenes = [Scene(scene_id=i, start=round(s, 2), end=round(e, 2)) for i, (s, e) in enumerate(boundaries)]
        for ci, (scene_idx, ts) in enumerate(candidates):
            img = images[ci]
            if ci not in kept or img is None:
                continue
            if img.width > max_width:
                img = img.resize((max_width, int(img.height * max_width / img.width)))
            rel_path = f"frames/scene{scene_idx:04d}_{int(ts * 1000):09d}.jpg"
            img.save(workdir / rel_path, quality=85)
            scenes[scene_idx].frames.append(Frame(path=rel_path, timestamp=ts))
    finally:
        cap.release()

    total_frames = sum(len(s.frames) for s in scenes)
    log.info("ключевых кадров после дедупа: %d (из %d кандидатов)", total_frames, len(candidates))
    write_json(workdir / "scenes.json", [s.to_dict() for s in scenes])
