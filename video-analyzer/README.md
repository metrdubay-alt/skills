# video-analyzer

Мультимодальный анализ видео: речь (faster-whisper) + сцены (PySceneDetect) + визуальный слой (OpenAI/Anthropic vision) → детальный Markdown-документ и JSON для поиска/RAG.

## Установка

```powershell
python -m venv .venv
.venv\Scripts\pip install -e .[dev]
copy .env.example .env       # вписать OPENAI_API_KEY
copy config.yaml.example config.yaml   # опционально, настроить под себя
```

Требуется `ffmpeg`/`ffprobe` в PATH. GPU (CUDA) используется автоматически, с фолбэком на CPU.
По умолчанию используется `provider: openai`. Для Anthropic укажите `provider: anthropic`, модель Claude и `ANTHROPIC_API_KEY`.

## Использование

```powershell
.venv\Scripts\python -m video_analyzer "https://www.youtube.com/watch?v=..."
.venv\Scripts\python -m video_analyzer "D:\videos\lecture.mp4" --doc-lang ru
```

Результат в `output/<video_id>/`:

| Файл | Что это |
|---|---|
| `document.md` | Итоговый документ: резюме, хронология, тезисы, сущности, риски, транскрипт |
| `analysis.json` | Сегменты + сущности для индексации и RAG |
| `transcript.json` / `.srt` | Транскрипт с таймкодами |
| `scenes.json`, `frames/` | Сцены и ключевые кадры |
| `vision.json` | Разбор кадров LLM vision |
| `segments.json` | Речь + экран, выровненные по времени |

## Кэш этапов

Пайплайн: `ingest → transcribe → scenes → vision → merge → document`. Каждый этап пишет артефакт; при повторном запуске готовые этапы пропускаются. Перезапустить с этапа: `--force vision` (перезапустит vision, merge, document).

Без API-ключа выбранного LLM-провайдера работают этапы 1–3 (транскрипт, сцены, кадры).

## Тесты

```powershell
.venv\Scripts\python -m pytest
```
