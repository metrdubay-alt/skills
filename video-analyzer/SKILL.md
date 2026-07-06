---
name: video-analyzer
description: Analyze long videos into Markdown and JSON using local Whisper transcription, scene/frame extraction, and an LLM vision provider. Use when Codex needs to run, modify, or explain the bundled video-analyzer Python project, especially for OpenAI or Anthropic API-backed multimodal video analysis.
---

# Video Analyzer

Use the bundled Python project in this folder to convert a YouTube URL or local video file into:

- `document.md`: detailed Markdown summary with timeline, claims, entities, risks, and full transcript.
- `analysis.json`: structured segments for search/RAG.
- intermediate artifacts: transcript, scenes, frames, vision analysis, merged segments.

## Project

The runnable project is this skill folder itself:

```text
video-analyzer/
  pyproject.toml
  config.yaml.example
  src/video_analyzer/
  tests/
```

Read `HANDOVER.md` for architecture and operational details.

## Provider

The project supports:

- `provider: openai` with `OPENAI_API_KEY`
- `provider: anthropic` with `ANTHROPIC_API_KEY`

Default configuration uses OpenAI. A ChatGPT subscription is not the same as API access; running the LLM stages requires an API key with available API billing/credits.

## Run

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
copy .env.example .env
copy config.yaml.example config.yaml
.venv\Scripts\python -m pytest
.venv\Scripts\python -m video_analyzer "D:\videos\lecture.mp4" --doc-lang ru
```

On Linux/WSL, use `.venv/bin/python` and `.venv/bin/pip`.

