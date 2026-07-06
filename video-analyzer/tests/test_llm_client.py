import sys
import types
from types import SimpleNamespace

from video_analyzer.llm_client import LLMClient


class _FakeResponses:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            output_text='{"ok": true}',
            usage=SimpleNamespace(input_tokens=12, output_tokens=3),
        )


class _FakeOpenAI:
    last_instance = None

    def __init__(self, max_retries):
        self.max_retries = max_retries
        self.responses = _FakeResponses()
        _FakeOpenAI.last_instance = self


def test_openai_structured_omits_empty_instructions(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "openai",
        types.SimpleNamespace(OpenAI=_FakeOpenAI),
    )

    client = LLMClient("openai", "gpt-5.5")
    result = client.structured(
        [{"type": "text", "text": "return ok"}],
        {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        },
        system=None,
        schema_name="unit_result",
    )

    kwargs = _FakeOpenAI.last_instance.responses.kwargs
    assert result == {"ok": True}
    assert "instructions" not in kwargs
    assert kwargs["input"] == [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "return ok"}],
        }
    ]
    assert kwargs["text"]["format"] == {
        "type": "json_schema",
        "name": "unit_result",
        "schema": {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        },
        "strict": True,
    }
    assert client.input_tokens == 12
    assert client.output_tokens == 3
