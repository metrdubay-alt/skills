"""Track LLM API usage for one analyzer run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# USD per 1M tokens: (input, output).
PRICE_PER_MILLION: dict[tuple[str, str], tuple[float, float]] = {
    ("openai", "gpt-5.5"): (5.0, 30.0),
    ("openai", "gpt-5.4"): (2.5, 15.0),
    ("openai", "gpt-5.4-mini"): (0.75, 4.5),
    ("openai", "gpt-5.3-codex-spark"): (0.25, 2.0),
    # Introductory Claude Sonnet 5 pricing is active through 2026-08-31.
    ("anthropic", "claude-sonnet-5"): (2.0, 10.0),
    ("anthropic", "claude-haiku-4-5"): (1.0, 5.0),
    ("anthropic", "claude-opus-4-8"): (5.0, 25.0),
    ("anthropic", "claude-fable-5"): (10.0, 50.0),
}


@dataclass
class LLMUsageEntry:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    operation: str

    @property
    def cost_usd(self) -> float | None:
        prices = price_for(self.provider, self.model)
        if prices is None:
            return None
        in_price, out_price = prices
        return (self.input_tokens * in_price + self.output_tokens * out_price) / 1_000_000


def price_for(provider: str, model: str) -> tuple[float, float] | None:
    provider_key = provider.lower()
    model_key = model.lower()
    exact = PRICE_PER_MILLION.get((provider_key, model_key))
    if exact is not None:
        return exact

    for (known_provider, known_model), prices in PRICE_PER_MILLION.items():
        if provider_key == known_provider and model_key.startswith(known_model):
            return prices
    return None


class LLMUsageTracker:
    def __init__(self) -> None:
        self.entries: list[LLMUsageEntry] = []

    def record(
        self,
        *,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str,
    ) -> None:
        self.entries.append(
            LLMUsageEntry(
                provider=provider.lower(),
                model=model,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                operation=operation,
            )
        )

    def summary(self, elapsed_seconds: float | None = None) -> dict[str, Any]:
        by_model: dict[tuple[str, str], dict[str, Any]] = {}
        total_cost = 0.0
        has_unknown_cost = False

        for entry in self.entries:
            key = (entry.provider, entry.model)
            row = by_model.setdefault(
                key,
                {
                    "provider": entry.provider,
                    "model": entry.model,
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                },
            )
            row["requests"] += 1
            row["input_tokens"] += entry.input_tokens
            row["output_tokens"] += entry.output_tokens
            cost = entry.cost_usd
            if cost is None:
                row["cost_usd"] = None
                has_unknown_cost = True
            elif row["cost_usd"] is not None:
                row["cost_usd"] += cost
                total_cost += cost

        rows = list(by_model.values())
        for row in rows:
            if row["cost_usd"] is not None:
                row["cost_usd"] = round(row["cost_usd"], 6)

        return {
            "elapsed_seconds": None if elapsed_seconds is None else round(elapsed_seconds, 1),
            "total_requests": len(self.entries),
            "total_input_tokens": sum(entry.input_tokens for entry in self.entries),
            "total_output_tokens": sum(entry.output_tokens for entry in self.entries),
            "total_cost_usd": None if has_unknown_cost else round(total_cost, 6),
            "by_model": rows,
        }


SESSION_USAGE = LLMUsageTracker()


def reset_session_usage() -> None:
    SESSION_USAGE.entries.clear()


def format_usage_summary(summary: dict[str, Any]) -> str:
    elapsed = summary["elapsed_seconds"]
    elapsed_label = "n/a" if elapsed is None else _format_elapsed(elapsed)
    total_cost = summary["total_cost_usd"]
    cost_label = "n/a" if total_cost is None else f"${total_cost:.4f}"
    lines = [
        "LLM usage summary:",
        f"- elapsed: {elapsed_label}",
        f"- requests: {summary['total_requests']}",
        f"- tokens: {summary['total_input_tokens']} input / {summary['total_output_tokens']} output",
        f"- estimated cost: {cost_label}",
    ]
    for row in summary["by_model"]:
        row_cost = "n/a" if row["cost_usd"] is None else f"${row['cost_usd']:.4f}"
        lines.append(
            f"- {row['provider']} {row['model']}: {row['requests']} request(s), "
            f"{row['input_tokens']} input / {row['output_tokens']} output, {row_cost}"
        )
    return "\n".join(lines)


def _format_elapsed(seconds: float) -> str:
    seconds_int = int(round(seconds))
    minutes, sec = divmod(seconds_int, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"
