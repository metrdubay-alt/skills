"""CLI: python -m video_analyzer <url|path> [--force <stage>] [--doc-lang ru|en]."""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from .config import PROJECT_ROOT, load_config
from .pipeline import Stage, run_pipeline
from .stages import document, ingest, merge, scenes, transcribe, vision
from .usage_tracker import SESSION_USAGE, format_usage_summary, reset_session_usage

STAGES = [
    Stage("ingest", "meta.json", ingest.run),
    Stage("transcribe", "transcript.json", transcribe.run),
    Stage("scenes", "scenes.json", scenes.run),
    Stage("vision", "vision.json", vision.run),
    Stage("merge", "segments.json", merge.run),
    Stage("document", ("document.md", "document.docx", "analysis.json"), document.run),
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
        description="Analyze video: transcription + scenes + LLM vision -> detailed document",
    )
    parser.add_argument("source", help="YouTube/URL or local video file path")
    parser.add_argument(
        "--force",
        metavar="STAGE",
        help=f"rerun stage and all following stages: {[s.name for s in STAGES]}",
    )
    parser.add_argument("--doc-lang", choices=["ru", "en"], help="final document language")
    parser.add_argument("--lang", help="speech language for whisper; default is auto")
    parser.add_argument("--config", type=Path, help="path to config.yaml")
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
    logging.info("video_id=%s, artifacts in %s", video_id, workdir)

    reset_session_usage()
    started_at = time.monotonic()
    run_pipeline(STAGES, workdir, config, force_from=args.force)
    elapsed_seconds = time.monotonic() - started_at
    usage_summary = SESSION_USAGE.summary(elapsed_seconds=elapsed_seconds)
    usage_text = format_usage_summary(usage_summary)
    logging.info("\n%s", usage_text)

    print(f"\nDone. Markdown: {workdir / 'document.md'}")
    print(f"Word: {workdir / 'document.docx'}")
    print(usage_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
