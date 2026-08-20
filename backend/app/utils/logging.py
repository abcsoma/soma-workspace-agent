"""Structured logging scaffold for LLM call observability.

Records every LLM call as a JSONL line with:
  model, input_tokens, output_tokens, latency_ms, cost, timestamp, ...

This is the foundation for all future optimization work (EDD / cost
engineering / latency analysis).  In W5+ the same data will be pushed to
Langfuse, but for now we write to a local file so there is zero external
dependency.

Usage::

    from app.utils.logging import log_llm_call, LLMCallRecord

    record = LLMCallRecord(
        model="deepseek-v4-flash",
        input_tokens=150,
        output_tokens=80,
        latency_ms=1200,
    )
    log_llm_call(record)
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, computed_field

from app.core.config import get_settings

# ── DeepSeek pricing (per 1M tokens, in CNY) ────────────────────
# Source: DeepSeek API docs.  Cache-hit price is 1/10 of standard.
# Update these when pricing changes.
_PRICING_CNY_PER_M: dict[str, dict[str, float]] = {
    "deepseek-v4-flash": {"input": 0.5, "output": 2.0, "cached_input": 0.05},
    "deepseek-v4-pro": {"input": 4.0, "output": 16.0, "cached_input": 0.4},
    # fallback for unknown models
    "_default": {"input": 1.0, "output": 4.0, "cached_input": 0.1},
}


class LLMCallRecord(BaseModel):
    """A single LLM API call record for structured logging."""

    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cached_input_tokens: int = 0
    # Optional context
    session_id: str | None = None
    agent_name: str | None = None
    tool_calls: int = 0
    success: bool = True
    error: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)."""
        return self.input_tokens + self.output_tokens

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_cny(self) -> float:
        """Estimate cost in CNY based on current pricing."""
        rates = _PRICING_CNY_PER_M.get(self.model, _PRICING_CNY_PER_M["_default"])
        input_cost = (self.input_tokens - self.cached_input_tokens) * rates["input"] / 1_000_000
        cached_cost = self.cached_input_tokens * rates["cached_input"] / 1_000_000
        output_cost = self.output_tokens * rates["output"] / 1_000_000
        return round(input_cost + cached_cost + output_cost, 6)


def _log_file_path() -> Path:
    """Return the log file path from settings."""
    return Path(get_settings().log_file)


def log_llm_call(record: LLMCallRecord) -> None:
    """Append a single LLM call record as a JSONL line.

    The file is created if it does not exist.  Each line is a complete
    JSON object, so the file can be parsed with ``json.loads`` line by
    line or loaded into pandas for analysis.
    """
    path = _log_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(record.model_dump_json() + "\n")


@contextmanager
def track_llm_call(
    model: str,
    session_id: str | None = None,
    agent_name: str | None = None,
):
    """Context manager that auto-records timing for an LLM call.

    Usage::

        with track_llm_call("deepseek-v4-flash", agent_name="router") as tracker:
            response = client.chat.completions.create(...)
            tracker.input_tokens = response.usage.prompt_tokens
            tracker.output_tokens = response.usage.completion_tokens

    On exception, ``success=False`` and the error message are recorded.
    """
    start = time.perf_counter()
    record = LLMCallRecord(
        model=model,
        session_id=session_id,
        agent_name=agent_name,
        success=True,
    )
    try:
        yield record
    except Exception as exc:
        record.success = False
        record.error = str(exc)
        raise
    finally:
        record.latency_ms = round((time.perf_counter() - start) * 1000, 2)
        log_llm_call(record)


def read_log_summary() -> dict[str, Any]:
    """Read the JSONL log and return a summary (total calls, tokens, cost).

    Useful for quick CLI inspection during development.
    """
    path = _log_file_path()
    if not path.exists():
        return {"total_calls": 0, "total_tokens": 0, "total_cost_cny": 0.0}

    total_calls = 0
    total_tokens = 0
    total_cost = 0.0
    by_model: dict[str, dict[str, Any]] = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        total_calls += 1
        total_tokens += data.get("total_tokens", 0)
        cost = data.get("cost_cny", 0)
        total_cost += cost
        model = data.get("model", "unknown")
        if model not in by_model:
            by_model[model] = {"calls": 0, "tokens": 0, "cost_cny": 0.0}
        by_model[model]["calls"] += 1
        by_model[model]["tokens"] += data.get("total_tokens", 0)
        by_model[model]["cost_cny"] += cost

    return {
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_cost_cny": round(total_cost, 4),
        "by_model": by_model,
    }
