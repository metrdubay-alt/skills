# video-analyzer — как устроена система и как её развернуть

Документ для передачи проекта. Описывает архитектуру, каждый этап пайплайна, форматы данных, зависимости и установку с нуля.

## Что делает система

На входе — видео (YouTube/URL или локальный файл): аналитика, подкасты, обзоры. На выходе — детальный Markdown-документ (что говорилось + что было на экране, с таймкодами) и JSON для поиска/RAG.

Главная идея: смысл таких видео разделён между **речью автора** и **данными на экране** (таблицы, дашборды, графики, интерфейсы). Поэтому пайплайн мультимодальный: речь распознаёт локальный Whisper, а экранный ряд разбирает LLM vision API (OpenAI по умолчанию, Anthropic опционально) — он за один проход делает OCR, понимает графики/интерфейсы и извлекает сущности (в классической архитектуре это три отдельных модуля: OCR + VLM + rule-based extraction).

## Архитектура: 6 этапов с кэшем

```
вход (URL | файл)
  1. ingest      → video.mp4, meta.json, audio.wav (16kHz mono)
  2. transcribe  → transcript.json, transcript.srt      [faster-whisper, локально]
  3. scenes      → scenes.json, frames/*.jpg            [PySceneDetect, локально]
  4. vision      → vision.json                          [OpenAI/Anthropic API]
  5. merge       → segments.json                        [чистая функция, локально]
  6. document    → document.md, analysis.json           [OpenAI/Anthropic API]
```

Каждый этап объявляет выходной артефакт-маркер ([pipeline.py](src/video_analyzer/pipeline.py)). Если файл уже существует — этап пропускается. Это дешёвая замена оркестратору: упавший прогон перезапускается с места остановки, а `--force <этап>` пересчитывает этап и всё после него (например, `--force document` перегенерирует только документ, не трогая транскрипцию).

### 1. ingest — [stages/ingest.py](src/video_analyzer/stages/ingest.py)

- URL → скачивание через `yt-dlp` (лучшее качество ≤1080p — выше не нужно для чтения экрана), плюс метаданные (название, канал, описание) и авто-субтитры, если есть (сохраняются как справка).
- Локальный файл → используется на месте, метаданные через `ffprobe`.
- Аудио: `ffmpeg -ac 1 -ar 16000` → `audio.wav` (формат, который ждёт Whisper).
- `video_id` (имя каталога в `output/`) — id ролика YouTube или имя файла.

### 2. transcribe — [stages/transcribe.py](src/video_analyzer/stages/transcribe.py)

- `faster-whisper` `large-v3`, авто-детекция языка (русский/английский работают отлично), VAD-фильтр пауз.
- Порядок загрузки: CUDA (`int8_float16`, влезает в 8 ГБ VRAM) → фолбэк на CPU (`int8`), если CUDA/cuDNN недоступны. На GPU 18-мин видео транскрибируется ~3 мин, на CPU в разы дольше.
- Выход: сегменты `{start, end, text, confidence}` + SRT-файл.

### 3. scenes — [stages/scenes.py](src/video_analyzer/stages/scenes.py)

- `PySceneDetect` `ContentDetector` (порог в конфиге, по умолчанию 27) режет видео на сцены.
- На сцену берётся кадр из середины; для сцен длиннее `max_frame_interval` (20 с) — равномерная сетка кадров.
- Дедуп через perceptual hash (`imagehash`, hamming ≤ 6): «говорящая голова» на 10 минут даёт один кадр, а не тридцать. Это главный механизм экономии на этапе vision.
- Кадры ресайзятся до 1568 px по ширине и сохраняются в `frames/`.

### 4. vision — [stages/vision.py](src/video_analyzer/stages/vision.py)

- Кадры уходят в LLM vision батчами по 5 сцен за вызов. В промпт каждой сцены вкладывается **фрагмент транскрипта этой сцены** — модель сразу связывает речь и экран.
- Structured output через JSON Schema — ответ должен быть валидным JSON, парсинг не ломается ([llm_client.py](src/video_analyzer/llm_client.py)).
- На сцену: `scene_type` (talking_head/slide/dashboard/chart/website/table/...), `description`, `screen_text[]` (дословный важный текст с экрана), `entities[]` (protocol/chain/pool/metric/strategy/risk/token с значениями вроде "APR 12.5%"), `notable`.
- Доменная модель сущностей заточена под DeFi, но промпт (константа `SYSTEM`) легко правится под другой домен.
- Стоимость и токены логируются и пишутся в `vision_usage.json`.

### 5. merge — [stages/merge.py](src/video_analyzer/stages/merge.py)

- Чистая функция `build_segments` (покрыта тестами): транскрипт-сегменты раскладываются по сценам по середине интервала; речь вне сцен прижимается к ближайшей — ничего не теряется.
- Выход `segments.json` — единица хранения «сцена + речь + экран + сущности». Это готовый формат для чанков RAG-индекса.

### 6. document — [stages/document.py](src/video_analyzer/stages/document.py)

- Один вызов LLM со всеми сегментами → Markdown: метаданные, резюме, хронология с таймкодами, ключевые тезисы, таблица сущностей, риски + полный транскрипт в приложении.
- **Важная деталь**: таймкоды конвертируются в MM:SS в коде (поле `timecode`), модель их цитирует дословно — LLM-арифметика по секундам ненадёжна (проверено: без этого таймкоды уплывали за длительность видео).
- Язык документа — `doc_language` в конфиге (ru/en), термины и тикеры остаются в оригинале.
- Параллельно пишется `analysis.json` (segments + метаданные + usage) для индексации.

## Ключевые файлы

```
src/video_analyzer/
  __main__.py        CLI и список этапов
  pipeline.py        запуск этапов, кэш артефактов, --force
  config.py          дефолты + config.yaml + .env
  models.py          dataclasses всех структур данных
  llm_client.py      OpenAI/Anthropic SDK wrapper: vision blocks, structured output, usage
  stages/*.py        шесть этапов
tests/               юнит-тесты merge и scenes (pytest)
config.yaml.example  все настройки с комментариями
.env.example         шаблон для API-ключа
```

## Развёртывание с нуля

### Требования

1. **Python 3.11+**
2. **ffmpeg + ffprobe в PATH** — https://www.gyan.dev/ffmpeg/builds/ (Windows) или `apt install ffmpeg` / `brew install ffmpeg`
3. **API-ключ OpenAI** — https://platform.openai.com/api-keys. Нужен только этапам 4 и 6; без него работают транскрипция, сцены и кадры. Anthropic тоже поддерживается опционально через `ANTHROPIC_API_KEY`.
4. Опционально: **NVIDIA GPU** (от ~6 ГБ VRAM) — ускоряет транскрипцию в разы. Без GPU всё работает на CPU автоматически.
5. Опционально: **deno** (`winget install DenoLand.Deno` / `brew install deno`) — JS-рантайм для yt-dlp, надёжнее скачивает с YouTube. Для локальных файлов не нужен.

### Установка

```powershell
# распаковать архив, затем в каталоге проекта:
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"        # Linux/Mac: .venv/bin/pip

copy .env.example .env                        # вписать свой OPENAI_API_KEY
copy config.yaml.example config.yaml          # опционально: модель, пороги, язык

.venv\Scripts\python -m pytest                # проверка: 16 тестов должны пройти
```

Зависимости ставятся автоматически из `pyproject.toml`: `yt-dlp`, `faster-whisper`, `scenedetect[opencv]`, `opencv-python`, `imagehash`, `pillow`, `openai`, `anthropic`, `python-dotenv`, `pyyaml` (+ `pytest` для dev). Первый запуск транскрипции скачает модель Whisper (~3 ГБ для large-v3, кэшируется в `~/.cache/huggingface`).

### Запуск

```powershell
.venv\Scripts\python -m video_analyzer "https://www.youtube.com/watch?v=..."
.venv\Scripts\python -m video_analyzer "D:\videos\podcast.mp4" --doc-lang ru
.venv\Scripts\python -m video_analyzer <источник> --force vision   # пересчитать с этапа vision
```

Результат — в `output/<video_id>/document.md` (+ все промежуточные артефакты рядом).

### Стоимость и производительность (замер на реальном видео)

18.6-мин видео, RTX 3060 Ti: полный прогон ~10 минут. Стоимость зависит от выбранного провайдера и модели. Модель и провайдер меняются в `config.yaml` (`provider: openai|anthropic`, `model: ...`).

## Безопасность при передаче

- Ключ живёт **только** в `.env`, который в `.gitignore` и в архив не включён. В коде ключ нигде не захардкожен — SDK берёт `OPENAI_API_KEY` или `ANTHROPIC_API_KEY` из окружения (python-dotenv подгружает `.env`).
- `output/` может содержать кадры и транскрипты ваших видео — тоже не включён в архив.

## Куда развивать (заложено архитектурой)

- **Диаризация спикеров**: `pyannote.audio` добавляется шагом внутрь transcribe (для подкастов с несколькими участниками).
- **RAG-индекс**: `analysis.json.segments` — готовые чанки с таймкодами и сущностями; складываются в Qdrant/pgvector как есть.
- **Другой домен**: правится промпт `SYSTEM` и enum сущностей в `stages/vision.py` + структура документа в `stages/document.py`.
- **Батч-обработка**: кэш этапов уже делает пайплайн идемпотентным — очередь добавляется поверх без переписывания.
