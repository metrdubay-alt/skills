import sys
import types
from pathlib import Path

from video_analyzer.stages.ingest import _download, _resolve_tool


def test_download_does_not_request_subtitles(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(
        "video_analyzer.stages.ingest._resolve_tool",
        lambda name: f"C:/tools/{name}.exe",
    )

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
    assert Path(captured["ffmpeg_location"]) == Path("C:/tools")


def test_resolve_tool_falls_back_to_winget_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr("shutil.which", lambda _name: None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    ffmpeg = (
        tmp_path
        / "Microsoft"
        / "WinGet"
        / "Packages"
        / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
        / "ffmpeg-8.1.2-full_build"
        / "bin"
        / "ffmpeg.exe"
    )
    ffmpeg.parent.mkdir(parents=True)
    ffmpeg.write_text("")

    assert _resolve_tool("ffmpeg") == str(ffmpeg)
