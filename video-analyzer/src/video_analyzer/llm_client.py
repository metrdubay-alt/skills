"""LLM provider wrapper for OpenAI and Anthropic multimodal calls."""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("video_analyzer")

# USD per 1M tokens (input, output). Unknown models report cost as None.
PRICES = {
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


class LLMClient:
    def __init__(self, provider: str, model: str):
        self.provider = provider.lower()
        self.model = model
        self.input_tokens = 0
        self.output_tokens = 0

        if self.provider == "anthropic":
            import anthropic

            self._anthropic = anthropic
            self.client = anthropic.Anthropic(max_retries=3)
        elif self.provider == "openai":
            from openai import OpenAI

            self.client = OpenAI(max_retries=3)
            self._anthropic = None
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _track(self, usage: Any) -> None:
        if not usage:
            return
        self.input_tokens += int(getattr(usage, "input_tokens", 0) or 0)
        self.output_tokens += int(getattr(usage, "output_tokens", 0) or 0)

    @property
    def cost_usd(self) -> float | None:
        prices = PRICES.get(self.model)
        if not prices:
            return None
        in_price, out_price = prices
        return (self.input_tokens * in_price + self.output_tokens * out_price) / 1_000_000

    @property
    def cost_label(self) -> str:
        return "n/a" if self.cost_usd is None else f"${self.cost_usd:.3f}"

    def structured(
        self,
        content: list[dict[str, Any]],
        schema: dict[str, Any],
        system: str | None = None,
        max_tokens: int = 8000,
        schema_name: str = "structured_result",
    ) -> Any:
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system or self._anthropic.NOT_GIVEN,
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
            self._track(response.usage)
            text = next(b.text for b in response.content if b.type == "text")
            return json.loads(text)

        request: dict[str, Any] = {
            "model": self.model,
            "input": [{"role": "user", "content": _to_openai_content(content)}],
            "max_output_tokens": max_tokens,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        if system is not None:
            request["instructions"] = system
        response = self.client.responses.create(**request)
        self._track(response.usage)
        return json.loads(response.output_text)

    def generate(
        self,
        content: list[dict[str, Any]],
        system: str | None = None,
        max_tokens: int = 32000,
    ) -> str:
        if self.provider == "anthropic":
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=system or self._anthropic.NOT_GIVEN,
                messages=[{"role": "user", "content": content}],
            ) as stream:
                response = stream.get_final_message()
            self._track(response.usage)
            return "".join(b.text for b in response.content if b.type == "text")

        request: dict[str, Any] = {
            "model": self.model,
            "input": [{"role": "user", "content": _to_openai_content(content)}],
            "max_output_tokens": max_tokens,
        }
        if system is not None:
            request["instructions"] = system
        response = self.client.responses.create(**request)
        self._track(response.usage)
        return response.output_text


def image_block(image_path: Path) -> dict[str, Any]:
    data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    media_type = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }


def _to_openai_content(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for item in content:
        if item.get("type") == "text":
            converted.append({"type": "input_text", "text": item["text"]})
        elif item.get("type") == "image":
            source = item["source"]
            converted.append({
                "type": "input_image",
                "image_url": f"data:{source['media_type']};base64,{source['data']}",
                "detail": "high",
            })
        else:
            raise ValueError(f"Unsupported content block: {item.get('type')}")
    return converted
