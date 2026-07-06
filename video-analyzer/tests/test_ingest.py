import sys
import types

from video_analyzer.stages.ingest import _download


def test_download_does_not_request_subtitles(monkeypatch, tmp_path):
    captured = {}

    class FakeYoutubeDL:
        def __init__(self, opts):
            captured.update(opts)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, source, download):
            (tmp_path / "video.mp4").write_bytes(b"fake video")
            return {"id": "abc", "title": "Demo", "webpage_url": source}

    monkeypatch.setitem(
        sys.modules,
        "yt_dlp",
        types.SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )

    _download("https://youtu.be/demo", tmp_path)

    assert captured["writesubtitles"] is False
    assert captured["writeautomaticsub"] is False
