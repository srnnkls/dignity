"""Token metrics calculation from transcript files."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache directory for storing last successful metrics
CACHE_DIR = Path.home() / ".cache" / "dignity"


def _get_cache_path(transcript_path: Path) -> Path:
    """Get cache file path for a transcript file."""
    # Use hash of transcript path to create unique cache file
    path_hash = hashlib.md5(str(transcript_path).encode()).hexdigest()[:16]
    return CACHE_DIR / f"{path_hash}.json"


def _read_cached_metrics(transcript_path: Path) -> TokenMetrics | None:
    """Read cached metrics for a transcript file."""
    cache_path = _get_cache_path(transcript_path)
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text())
        return TokenMetrics(
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"],
            cached_tokens=data["cached_tokens"],
            total_tokens=data["total_tokens"],
            context_length=data["context_length"],
        )
    except Exception:
        return None


def _write_cached_metrics(transcript_path: Path, metrics: TokenMetrics) -> None:
    """Write metrics to cache file."""
    cache_path = _get_cache_path(transcript_path)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "input_tokens": metrics.input_tokens,
                    "output_tokens": metrics.output_tokens,
                    "cached_tokens": metrics.cached_tokens,
                    "total_tokens": metrics.total_tokens,
                    "context_length": metrics.context_length,
                }
            )
        )
    except Exception:
        pass  # Cache write failures are non-critical


@dataclass(frozen=True)
class TokenMetrics:
    """Token usage metrics from transcript."""

    input_tokens: int
    output_tokens: int
    cached_tokens: int
    total_tokens: int
    context_length: int


_ZERO_METRICS = TokenMetrics(
    input_tokens=0,
    output_tokens=0,
    cached_tokens=0,
    total_tokens=0,
    context_length=0,
)

# Retry configuration for transient read errors
_MAX_RETRIES = 2
_RETRY_DELAY_MS = 10


def _parse_transcript(transcript_path: Path) -> TokenMetrics:
    """Parse transcript file and calculate metrics.

    Args:
        transcript_path: Path to the transcript JSONL file

    Returns:
        TokenMetrics with aggregated usage data

    Raises:
        Exception: If file cannot be read or parsed
    """
    total_input = 0
    total_output = 0
    total_cached = 0
    messages_for_context: list[dict[str, int | str]] = []

    content = transcript_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        if not line.strip():
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            # Skip invalid JSON lines (common during file writes)
            continue

        # Extract usage data
        message = data.get("message", {})
        usage = message.get("usage", {})

        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_creation = usage.get("cache_creation_input_tokens", 0)

        # Accumulate totals
        total_input += input_tokens
        total_output += output_tokens
        total_cached += cache_read + cache_creation

        # Track for context calculation
        # Exclude sidechain and API error messages
        is_sidechain = data.get("isSidechain", False)
        is_api_error = data.get("isApiErrorMessage", False)
        has_timestamp = "timestamp" in data

        if has_timestamp and not is_sidechain and not is_api_error:
            messages_for_context.append(
                {
                    "timestamp": data["timestamp"],
                    "input_tokens": input_tokens,
                    "cache_read": cache_read,
                    "cache_creation": cache_creation,
                }
            )

    # Calculate context length from most recent message
    context_length = 0
    if messages_for_context:
        most_recent = max(messages_for_context, key=lambda m: m["timestamp"])
        context_length = (
            int(most_recent["input_tokens"])
            + int(most_recent["cache_read"])
            + int(most_recent["cache_creation"])
        )

    total_tokens = total_input + total_output + total_cached

    return TokenMetrics(
        input_tokens=total_input,
        output_tokens=total_output,
        cached_tokens=total_cached,
        total_tokens=total_tokens,
        context_length=context_length,
    )


def get_token_metrics(transcript_path: Path) -> TokenMetrics:
    """Calculate token metrics from a transcript file.

    Uses retry logic for transient read errors (e.g., file being written to)
    and falls back to cached metrics if parsing fails or returns zeros.

    Args:
        transcript_path: Path to the transcript JSONL file

    Returns:
        TokenMetrics with aggregated usage data. On read failure or zero result,
        returns cached metrics from last successful read if available.
    """
    if not transcript_path.exists():
        return _ZERO_METRICS

    # Try to read with retries for transient errors
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            metrics = _parse_transcript(transcript_path)
            if metrics.context_length > 0:
                # Success with real data - cache and return
                _write_cached_metrics(transcript_path, metrics)
                return metrics
            # Got zeros - might be transient (file being written), retry
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_MS / 1000)
        except Exception as e:
            last_error = e
            if attempt < _MAX_RETRIES:
                # Brief delay before retry (file might be mid-write)
                time.sleep(_RETRY_DELAY_MS / 1000)

    # All retries returned zeros or failed - try cached metrics
    cached = _read_cached_metrics(transcript_path)
    if cached is not None and cached.context_length > 0:
        if last_error:
            logger.debug(
                "Read failed after %d attempts (%s), using cached metrics",
                _MAX_RETRIES + 1,
                last_error,
            )
        else:
            logger.debug(
                "Got zero metrics after %d attempts, using cached metrics",
                _MAX_RETRIES + 1,
            )
        return cached

    # No useful cache - return zeros (or last parsed zeros)
    return _ZERO_METRICS
