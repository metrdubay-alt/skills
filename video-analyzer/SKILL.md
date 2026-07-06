---
name: video-analyzer
description: Use when the user asks to analyze a video, runs /va with a YouTube URL or local video path, or needs to run, modify, or explain the bundled OpenAI/Anthropic video-analyzer Python project.
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

## Codex Shortcut

When the user writes:

```text
/va <YouTube URL or local video path>
```

Run the analyzer from this skill folder with the local virtual environment:

```powershell
cd "<installed video-analyzer skill folder>"
.\.venv\Scripts\python.exe -m video_analyzer "<source>" --doc-lang ru
```

Replace `<source>` with the text after `/va`. Do not ask for API keys in chat; use the local `.env`.
If the run completes, report the generated `document.md` and `document.docx` paths plus the final LLM usage summary and elapsed processing time. If it fails, summarize the error and the next fix.

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
