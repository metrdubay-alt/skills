"""Загрузка конфигурации: config.yaml поверх дефолтов, API keys из .env."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

DEFAULTS: dict[str, Any] = {
    "provider": "openai",
    "model": "gpt-5.5",
    "doc_language": "ru",
    "whisper": {"model": "tiny", "device": "cpu", "language": None, "vad_filter": False},
    "scenes": {"detect": False, "threshold": 27.0, "max_frame_interval": 20.0, "phash_distance": 6},
    "vision": {"batch_size": 5, "max_frame_width": 1568},
    "output_dir": "output",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    load_dotenv(PROJECT_ROOT / ".env")
    path = config_path or PROJECT_ROOT / "config.yaml"
    if path.exists():
        user_cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return _deep_merge(DEFAULTS, user_cfg)
    return copy.deepcopy(DEFAULTS)
