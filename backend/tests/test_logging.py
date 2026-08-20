"""Tests for structured logging scaffold (W1 depth task)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from app.utils.logging import LLMCallRecord, log_llm_call, track_llm_call

if TYPE_CHECKING:
    from pathlib import Path


class TestLLMCallRecord:
    """Tests for LLMCallRecord model."""

    def test_record_creation(self) -> None:
        record = LLMCallRecord(
            model="deepseek-v4-flash",
            input_tokens=100,
            output_tokens=50,
            latency_ms=800.0,
        )
        assert record.total_tokens == 150
        assert record.cost_cny > 0

    def test_cached_input_reduces_cost(self) -> None:
        """Cached input tokens should be cheaper than regular input."""
        regular = LLMCallRecord(
            model="deepseek-v4-flash",
            input_tokens=1000,
            output_tokens=0,
        )
        cached = LLMCallRecord(
            model="deepseek-v4-flash",
            input_tokens=1000,
            cached_input_tokens=800,
            output_tokens=0,
        )
        assert cached.cost_cny < regular.cost_cny

    def test_unknown_model_uses_default_pricing(self) -> None:
        record = LLMCallRecord(
            model="some-unknown-model",
            input_tokens=1000,
            output_tokens=500,
        )
        assert record.cost_cny > 0

    def test_serialization_includes_computed_fields(self) -> None:
        """total_tokens and cost_cny should be in JSON output."""
        record = LLMCallRecord(
            model="deepseek-v4-flash",
            input_tokens=100,
            output_tokens=50,
        )
        data = json.loads(record.model_dump_json())
        assert data["total_tokens"] == 150
        assert "cost_cny" in data
        assert data["cost_cny"] > 0


class TestLoggingFunctions:
    """Tests for log writing and reading."""

    def test_log_llm_call_writes_jsonl(self, tmp_path: Path, monkeypatch) -> None:
        """log_llm_call should append a valid JSON line."""
        log_file = tmp_path / "test_log.jsonl"
        log_path = str(log_file)

        class MockSettings:
            log_file = log_path

        monkeypatch.setattr("app.utils.logging.get_settings", lambda: MockSettings())

        record = LLMCallRecord(
            model="deepseek-v4-flash",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500.0,
        )
        log_llm_call(record)

        assert log_file.exists()
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["model"] == "deepseek-v4-flash"
        assert data["input_tokens"] == 100
        assert data["output_tokens"] == 50
        assert data["latency_ms"] == 500.0
        assert data["total_tokens"] == 150
        assert "cost_cny" in data

    def test_track_llm_call_records_timing(self, tmp_path: Path, monkeypatch) -> None:
        """track_llm_call context manager should record latency."""
        log_file = tmp_path / "test_track.jsonl"
        log_path = str(log_file)

        class MockSettings:
            log_file = log_path

        monkeypatch.setattr("app.utils.logging.get_settings", lambda: MockSettings())

        with track_llm_call("deepseek-v4-flash", agent_name="test") as tracker:
            tracker.input_tokens = 50
            tracker.output_tokens = 25

        assert tracker.latency_ms > 0
        assert tracker.success is True

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["agent_name"] == "test"
        assert data["input_tokens"] == 50

    def test_track_llm_call_records_error(self, tmp_path: Path, monkeypatch) -> None:
        """track_llm_call should record errors when exceptions occur."""
        log_file = tmp_path / "test_error.jsonl"
        log_path = str(log_file)

        class MockSettings:
            log_file = log_path

        monkeypatch.setattr("app.utils.logging.get_settings", lambda: MockSettings())

        with (
            pytest.raises(ValueError, match="simulated"),
            track_llm_call("deepseek-v4-flash") as tracker,
        ):
            raise ValueError("simulated error")

        assert tracker.success is False
        assert "simulated error" in (tracker.error or "")
