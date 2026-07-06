from video_analyzer.usage_tracker import LLMUsageTracker


def test_usage_tracker_counts_requests_tokens_cost_and_elapsed_time():
    tracker = LLMUsageTracker()

    tracker.record(
        provider="openai",
        model="gpt-5.5",
        input_tokens=1_000_000,
        output_tokens=100_000,
        operation="vision",
    )
    tracker.record(
        provider="openai",
        model="gpt-5.5",
        input_tokens=10,
        output_tokens=20,
        operation="document",
    )

    summary = tracker.summary(elapsed_seconds=125.4)

    assert summary["total_requests"] == 2
    assert summary["total_input_tokens"] == 1_000_010
    assert summary["total_output_tokens"] == 100_020
    assert summary["elapsed_seconds"] == 125.4
    assert summary["total_cost_usd"] == 8.00065
    assert summary["by_model"][0]["provider"] == "openai"
    assert summary["by_model"][0]["model"] == "gpt-5.5"
    assert summary["by_model"][0]["requests"] == 2


def test_usage_tracker_reports_unknown_model_cost_as_none():
    tracker = LLMUsageTracker()

    tracker.record(
        provider="openai",
        model="unknown-model",
        input_tokens=100,
        output_tokens=50,
        operation="document",
    )

    summary = tracker.summary(elapsed_seconds=1.0)

    assert summary["total_cost_usd"] is None
    assert summary["by_model"][0]["cost_usd"] is None
