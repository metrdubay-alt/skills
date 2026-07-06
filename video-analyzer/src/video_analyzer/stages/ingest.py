"""Этап 1: ingest. URL -> скачивание через yt-dlp; локальный файл -> как есть.

Артефакты: meta.json (id, источник, метаданные, ffprobe), audio.wav (16kHz mono).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from ..pipeline import write_json

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v"}


def is_url(source: str) -> bool:
    return source.startswith(("http://", "https://"))


def video_id_for(source: str) -> str:
    """Стабильный идентификатор видео -> имя каталога в output/."""
    if is_url(source):
        import yt_dlp

        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(source, download=False)
        return sanitize_id(info["id"])
    return sanitize_id(Path(source).stem)


def sanitize_id(raw: str) -> str:
    return re.sub(r"[^\w\-]+", "_", raw).strip("_") or "video"


def ffprobe_meta(video_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(video_path),
        ],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    return json.loads(result.stdout)


def extract_audio(video_path: Path, audio_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", str(audio_path),
        ],
        check=True,
    )


def _download(source: str, workdir: Path) -> tuple[Path, dict[str, Any]]:
    import yt_dlp

    opts = {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "outtmpl": str(workdir / "video.%(ext)s"),
        "merge_output_format": "mp4",
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["ru", "en"],
        "subtitlesformat": "vtt",
        "quiet": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(source, download=True)

    video_path = workdir / "video.mp4"
    if not video_path.exists():
        candidates = [p for p in workdir.glob("video.*") if p.suffix.lower() in VIDEO_EXTS]
        if not candidates:
            raise RuntimeError("yt-dlp завершился, но видеофайл не найден")
        video_path = candidates[0]

    source_meta = {
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "description": (info.get("description") or "")[:2000],
        "url": info.get("webpage_url") or source,
    }
    return video_path, source_meta


def run(workdir: Path, config: dict[str, Any]) -> None:
    source: str = config["_source"]

    if is_url(source):
        video_path, source_meta = _download(source, workdir)
    else:
        video_path = Path(source).resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Видеофайл не найден: {video_path}")
        source_meta = {"title": video_path.stem, "url": None, "local_path": str(video_path)}

    audio_path = workdir / "audio.wav"
    extract_audio(video_path, audio_path)

    meta = {
        "video_id": workdir.name,
        "source": source,
        "video_path": str(video_path),
        "source_meta": source_meta,
        "ffprobe": ffprobe_meta(video_path),
    }
    write_json(workdir / "meta.json", meta)
