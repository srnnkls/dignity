"""Tests for status line rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

import dignity.statusline as statusline_module
from dignity.statusline import StatusLineInput, render_statusline


def test_render_statusline_with_git_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test status line rendering with git branch."""

    # Mock get_git_branch to return "main"
    def mock_get_git_branch(directory: Path) -> str | None:
        return "main"

    monkeypatch.setattr(statusline_module, "get_git_branch", mock_get_git_branch)

    # Create empty transcript (will result in 0 tokens)
    transcript_path = tmp_path / "transcript.jsonl"
    transcript_path.write_text("", encoding="utf-8")

    input_data = StatusLineInput(
        model_name="Sonnet 4.5",
        current_dir=str(tmp_path / "dignity"),
        transcript_path=str(transcript_path),
        max_tokens=200000,
    )

    result = render_statusline(input_data)

    assert result == "Sonnet 4.5 | dignity | main | 0/200000 (0%)"


def test_render_statusline_without_git_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test status line rendering without git branch."""

    def mock_get_git_branch(directory: Path) -> str | None:
        return None

    monkeypatch.setattr(statusline_module, "get_git_branch", mock_get_git_branch)

    # Create empty transcript
    transcript_path = tmp_path / "transcript.jsonl"
    transcript_path.write_text("", encoding="utf-8")

    input_data = StatusLineInput(
        model_name="Sonnet 4.5",
        current_dir=str(tmp_path / "dignity"),
        transcript_path=str(transcript_path),
        max_tokens=200000,
    )

    result = render_statusline(input_data)

    assert result == "Sonnet 4.5 | dignity | 0/200000 (0%)"


def test_render_statusline_with_tokens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test status line rendering with non-zero tokens."""

    def mock_get_git_branch(directory: Path) -> str | None:
        return "feature-branch"

    monkeypatch.setattr(statusline_module, "get_git_branch", mock_get_git_branch)

    # Create transcript with token data
    transcript_path = tmp_path / "transcript.jsonl"
    transcript_content = '{"message": {"usage": {"input_tokens": 50000, "output_tokens": 10000}}, "timestamp": "2024-01-01T00:00:00"}'
    transcript_path.write_text(transcript_content, encoding="utf-8")

    input_data = StatusLineInput(
        model_name="Sonnet 4.5",
        current_dir=str(tmp_path / "myproject"),
        transcript_path=str(transcript_path),
        max_tokens=200000,
    )

    result = render_statusline(input_data)

    assert result == "Sonnet 4.5 | myproject | feature-branch | 50000/200000 (25%)"


def test_render_statusline_empty_current_dir(tmp_path: Path) -> None:
    """Test status line rendering with empty current directory."""
    # Create empty transcript
    transcript_path = tmp_path / "transcript.jsonl"
    transcript_path.write_text("", encoding="utf-8")

    input_data = StatusLineInput(
        model_name="Claude 3",
        current_dir="",
        transcript_path=str(transcript_path),
        max_tokens=100000,
    )

    result = render_statusline(input_data)

    assert result == "Claude 3 | ~ | 0/100000 (0%)"


def test_render_statusline_nonexistent_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test status line rendering with nonexistent transcript file."""

    def mock_get_git_branch(directory: Path) -> str | None:
        return "develop"

    monkeypatch.setattr(statusline_module, "get_git_branch", mock_get_git_branch)

    input_data = StatusLineInput(
        model_name="GPT-4",
        current_dir=str(tmp_path / "project"),
        transcript_path=str(tmp_path / "nonexistent.jsonl"),
        max_tokens=150000,
    )

    result = render_statusline(input_data)

    # Should handle nonexistent file gracefully with 0 tokens
    assert result == "GPT-4 | project | develop | 0/150000 (0%)"


def test_render_statusline_percentage_calculation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that percentage is calculated and rounded correctly."""

    def mock_get_git_branch(directory: Path) -> str | None:
        return "main"

    monkeypatch.setattr(statusline_module, "get_git_branch", mock_get_git_branch)

    # Create transcript with specific token count for percentage test
    transcript_path = tmp_path / "transcript.jsonl"
    # 33333 / 100000 = 33.333% -> rounds to 33%
    transcript_content = '{"message": {"usage": {"input_tokens": 33333, "output_tokens": 5000}}, "timestamp": "2024-01-01T00:00:00"}'
    transcript_path.write_text(transcript_content, encoding="utf-8")

    input_data = StatusLineInput(
        model_name="Test Model",
        current_dir=str(tmp_path / "test"),
        transcript_path=str(transcript_path),
        max_tokens=100000,
    )

    result = render_statusline(input_data)

    assert result == "Test Model | test | main | 33333/100000 (33%)"
