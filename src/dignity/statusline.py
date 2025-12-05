"""Status line rendering for Claude Code."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from dignity.tokens import get_token_metrics


@dataclass(frozen=True, kw_only=True)
class StatusLineInput:
    """Input data for status line rendering."""

    model_name: str
    current_dir: str
    transcript_path: str
    max_tokens: int


def get_git_branch(directory: Path) -> str | None:
    """Get current git branch for directory.

    Args:
        directory: Directory to check for git branch.

    Returns:
        Branch name if in git repo, None otherwise.
    """
    git_dir = directory / ".git"
    if not git_dir.is_dir():
        return None

    try:
        result = subprocess.run(
            ["git", "-c", "core.useBuiltinFSMonitor=false", "branch", "--show-current"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def render_statusline(input_data: StatusLineInput) -> str:
    """Render status line from input data.

    Args:
        input_data: Status line input data.

    Returns:
        Formatted status line string.
    """
    # Get directory basename
    dir_name = Path(input_data.current_dir).name if input_data.current_dir else "~"

    # Get git branch
    git_branch = None
    if input_data.current_dir:
        git_branch = get_git_branch(Path(input_data.current_dir))

    # Get token usage - call the lib directly
    used_tokens = 0
    if input_data.transcript_path:
        transcript_path = Path(input_data.transcript_path)
        metrics = get_token_metrics(transcript_path)
        used_tokens = metrics.context_length

    # Calculate percentage
    percentage = (
        round((used_tokens / input_data.max_tokens) * 100)
        if input_data.max_tokens > 0
        else 0
    )

    # Format output
    if git_branch:
        return f"{input_data.model_name} | {dir_name} | {git_branch} | {used_tokens}/{input_data.max_tokens} ({percentage}%)"
    else:
        return f"{input_data.model_name} | {dir_name} | {used_tokens}/{input_data.max_tokens} ({percentage}%)"
