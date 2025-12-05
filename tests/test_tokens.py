"""Tests for token metrics calculation from transcript files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from dignity.tokens import TokenMetrics, get_token_metrics


@dataclass(frozen=True)
class TranscriptTestCase:
    """Test case for token metrics calculation."""

    content: str
    expected: TokenMetrics
    description: str


TRANSCRIPT_CASES = [
    TranscriptTestCase(
        content="",
        expected=TokenMetrics(
            input_tokens=0,
            output_tokens=0,
            cached_tokens=0,
            total_tokens=0,
            context_length=0,
        ),
        description="empty file",
    ),
    TranscriptTestCase(
        content='{"message": {"usage": {"input_tokens": 100, "output_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
        expected=TokenMetrics(
            input_tokens=100,
            output_tokens=50,
            cached_tokens=0,
            total_tokens=150,
            context_length=100,
        ),
        description="single message without cache",
    ),
    TranscriptTestCase(
        content='{"message": {"usage": {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 200, "cache_creation_input_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
        expected=TokenMetrics(
            input_tokens=100,
            output_tokens=50,
            cached_tokens=250,
            total_tokens=400,
            context_length=350,
        ),
        description="single message with cache",
    ),
    TranscriptTestCase(
        content="\n".join(
            [
                '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
                '{"message": {"usage": {"input_tokens": 200, "output_tokens": 75}}, "timestamp": "2024-01-01T00:01:00"}',
            ]
        ),
        expected=TokenMetrics(
            input_tokens=300,
            output_tokens=125,
            cached_tokens=0,
            total_tokens=425,
            context_length=200,  # Most recent message
        ),
        description="multiple messages - uses most recent for context",
    ),
    TranscriptTestCase(
        content="\n".join(
            [
                '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 300}}, "timestamp": "2024-01-01T00:00:00"}',
                '{"message": {"usage": {"input_tokens": 200, "output_tokens": 75, "cache_read_input_tokens": 500}}, "timestamp": "2024-01-01T00:01:00"}',
            ]
        ),
        expected=TokenMetrics(
            input_tokens=300,
            output_tokens=125,
            cached_tokens=800,
            total_tokens=1225,
            context_length=700,  # Most recent: 200 + 500
        ),
        description="multiple messages with cache",
    ),
    TranscriptTestCase(
        content="\n".join(
            [
                '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
                '{"message": {"usage": {"input_tokens": 200, "output_tokens": 75}}, "timestamp": "2024-01-01T00:01:00", "isSidechain": true}',
            ]
        ),
        expected=TokenMetrics(
            input_tokens=300,
            output_tokens=125,
            cached_tokens=0,
            total_tokens=425,
            context_length=100,  # Sidechain excluded from context
        ),
        description="sidechain message excluded from context",
    ),
    TranscriptTestCase(
        content="\n".join(
            [
                '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
                '{"message": {"usage": {"input_tokens": 0, "output_tokens": 0}}, "timestamp": "2024-01-01T00:01:00", "isApiErrorMessage": true}',
            ]
        ),
        expected=TokenMetrics(
            input_tokens=100,
            output_tokens=50,
            cached_tokens=0,
            total_tokens=150,
            context_length=100,  # API error excluded from context
        ),
        description="API error message excluded from context",
    ),
    TranscriptTestCase(
        content="\n".join(
            [
                '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
                "invalid json line",
                '{"message": {"usage": {"input_tokens": 200, "output_tokens": 75}}, "timestamp": "2024-01-01T00:01:00"}',
            ]
        ),
        expected=TokenMetrics(
            input_tokens=300,
            output_tokens=125,
            cached_tokens=0,
            total_tokens=425,
            context_length=200,
        ),
        description="invalid JSON lines skipped",
    ),
    TranscriptTestCase(
        content="\n".join(
            [
                '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50, "cache_creation_input_tokens": 25}}, "timestamp": "2024-01-01T00:00:00"}',
                '{"message": {"usage": {"input_tokens": 200, "output_tokens": 75, "cache_read_input_tokens": 150}}, "timestamp": "2024-01-01T00:01:00"}',
            ]
        ),
        expected=TokenMetrics(
            input_tokens=300,
            output_tokens=125,
            cached_tokens=175,  # 25 + 150
            total_tokens=600,
            context_length=350,  # Most recent: 200 + 150
        ),
        description="mixed cache read and creation tokens",
    ),
]


@pytest.mark.parametrize("case", TRANSCRIPT_CASES, ids=lambda c: c.description)
def test_get_token_metrics(case: TranscriptTestCase, tmp_path: Path) -> None:
    """Test token metrics calculation from various transcript formats."""
    transcript_path = tmp_path / "transcript.jsonl"
    transcript_path.write_text(case.content, encoding="utf-8")

    result = get_token_metrics(transcript_path)

    assert result == case.expected


def test_get_token_metrics_nonexistent_file(tmp_path: Path) -> None:
    """Test handling of nonexistent transcript file."""
    nonexistent = tmp_path / "does_not_exist.jsonl"

    result = get_token_metrics(nonexistent)

    assert result == TokenMetrics(
        input_tokens=0,
        output_tokens=0,
        cached_tokens=0,
        total_tokens=0,
        context_length=0,
    )


def test_get_token_metrics_message_without_timestamp() -> None:
    """Test that messages without timestamps are excluded from context calculation."""
    content = "\n".join(
        [
            '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
            '{"message": {"usage": {"input_tokens": 200, "output_tokens": 75}}}',  # No timestamp
        ]
    )

    transcript_path = Path("test_transcript.jsonl")
    try:
        transcript_path.write_text(content, encoding="utf-8")
        result = get_token_metrics(transcript_path)

        assert result.input_tokens == 300
        assert result.output_tokens == 125
        assert result.total_tokens == 425
        assert result.context_length == 100  # Uses timestamped message
    finally:
        if transcript_path.exists():
            transcript_path.unlink()


def test_get_token_metrics_ordering() -> None:
    """Test that context is calculated from truly most recent message by timestamp."""
    content = "\n".join(
        [
            '{"message": {"usage": {"input_tokens": 300, "output_tokens": 100}}, "timestamp": "2024-01-01T00:02:00"}',
            '{"message": {"usage": {"input_tokens": 100, "output_tokens": 50}}, "timestamp": "2024-01-01T00:00:00"}',
            '{"message": {"usage": {"input_tokens": 200, "output_tokens": 75}}, "timestamp": "2024-01-01T00:01:00"}',
        ]
    )

    transcript_path = Path("test_transcript.jsonl")
    try:
        transcript_path.write_text(content, encoding="utf-8")
        result = get_token_metrics(transcript_path)

        assert result.input_tokens == 600
        assert result.output_tokens == 225
        assert result.context_length == 300  # Most recent by timestamp, not file order
    finally:
        if transcript_path.exists():
            transcript_path.unlink()
