import io
import sys

import pytest

from video_analyzer.__main__ import main


def test_help_prints_with_legacy_console_encoding(monkeypatch):
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "argv", ["video-analyzer", "--help"])
    monkeypatch.setattr(sys, "stdout", stdout)

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
