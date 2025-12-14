"""State management backend for declarative hook dispatch.

Simple file-based storage following the todos pattern.
Location: ~/.claude/state/{session_id}-{key}

Operations:
- get(session_id, key) -> str | None
- set(session_id, key, value)
- clear(session_id, key)
- exists(session_id, key) -> bool

Fails loudly on permission/directory errors.
No locking (session-scoped files).
"""

from __future__ import annotations

from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "state"


def _get_state_path(session_id: str, key: str) -> Path:
    """Get file path for a state key."""
    return STATE_DIR / f"{session_id}-{key}"


def get(session_id: str, key: str) -> str | None:
    """Get state value for key.

    Args:
        session_id: Session identifier
        key: State key

    Returns:
        State value if exists, None otherwise
    """
    path = _get_state_path(session_id, key)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def set(session_id: str, key: str, value: str) -> None:
    """Set state value for key.

    Creates state directory if it doesn't exist.
    Overwrites existing value.

    Args:
        session_id: Session identifier
        key: State key
        value: State value

    Raises:
        PermissionError: If directory cannot be created or file cannot be written
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = _get_state_path(session_id, key)
    path.write_text(value, encoding="utf-8")


def clear(session_id: str, key: str) -> None:
    """Clear state value for key.

    Succeeds silently if key doesn't exist.

    Args:
        session_id: Session identifier
        key: State key
    """
    path = _get_state_path(session_id, key)
    path.unlink(missing_ok=True)


def exists(session_id: str, key: str) -> bool:
    """Check if state key exists.

    Args:
        session_id: Session identifier
        key: State key

    Returns:
        True if key exists, False otherwise
    """
    path = _get_state_path(session_id, key)
    return path.exists()
