"""CLI: python -m video_analyzer <url|путь> [--force <stage>] [--doc-lang ru|en]"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import PROJECT_ROOT, load_config
from .pipeline import Stage, run_pipeline
from .stages import document, ingest, merge, scenes, transcribe, vision

STAGES = [
    Stage("ingest", "meta.json", ingest.run),
    Stage("transcribe", "transcript.json", transcribe.run),
    Stage("scenes", "scenes.json", scenes.run),
    Stage("vision", "vision.json", vision.run),
    Stage("merge", "segments.json", merge.run),
    Stage("document", "document.md", document.run),
]


def _prefer_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    _prefer_utf8_output()
    parser = argparse.ArgumentParser(
        prog="video-analyzer",
        description="Анализ видео: транскрипция + сцены + LLM vision -> детальный документ",
    )
    parser.add_argument("source", help="YouTube/URL или путь к локальному видеофайлу")
    parser.add_argument("--force", metavar="STAGE",
                        help=f"перезапустить этап и все последующие: {[s.name for s in STAGES]}")
    parser.add_argument("--doc-lang", choices=["ru", "en"], help="язык итогового документа")
    parser.add_argument("--lang", help="язык речи для whisper (по умолчанию авто)")
    parser.add_argument("--config", type=Path, help="путь к config.yaml")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    config = load_config(args.config)
    config["_source"] = args.source
    if args.doc_lang:
        config["doc_language"] = args.doc_lang
    if args.lang:
        config["whisper"]["language"] = args.lang

    from .stages.ingest import video_id_for

    video_id = video_id_for(args.source)
    workdir = PROJECT_ROOT / config["output_dir"] / video_id
    logging.info("video_id=%s, артефакты в %s", video_id, workdir)

    run_pipeline(STAGES, workdir, config, force_from=args.force)

    print(f"\nГотово. Документ: {workdir / 'document.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
