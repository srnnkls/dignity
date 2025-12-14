"""Tests for state management backend."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dignity import state


@pytest.fixture
def session_id() -> str:
    """Test session ID."""
    return "test-session-12345"


@pytest.fixture
def state_dir() -> Path:
    """State directory for testing."""
    return Path.home() / ".claude" / "state"


@pytest.fixture(autouse=True)
def cleanup_test_state(session_id: str, state_dir: Path) -> None:
    """Clean up test state files after each test."""
    yield
    # Clean up any test state files
    if state_dir.exists():
        for file in state_dir.glob(f"{session_id}-*"):
            file.unlink(missing_ok=True)


class TestStateGet:
    """Tests for state.get()."""

    def test_get_nonexistent_key(self, session_id: str) -> None:
        """get() returns None for nonexistent key."""
        result = state.get(session_id, "nonexistent")
        assert result is None

    def test_get_existing_key(self, session_id: str) -> None:
        """get() returns value for existing key."""
        state.set(session_id, "test-key", "test-value")
        result = state.get(session_id, "test-key")
        assert result == "test-value"

    def test_get_empty_value(self, session_id: str) -> None:
        """get() returns empty string for empty value."""
        state.set(session_id, "empty-key", "")
        result = state.get(session_id, "empty-key")
        assert result == ""


class TestStateSet:
    """Tests for state.set()."""

    def test_set_creates_file(self, session_id: str, state_dir: Path) -> None:
        """set() creates state file."""
        state.set(session_id, "new-key", "new-value")
        file_path = state_dir / f"{session_id}-new-key"
        assert file_path.exists()

    def test_set_writes_content(self, session_id: str) -> None:
        """set() writes value to file."""
        state.set(session_id, "content-key", "content-value")
        result = state.get(session_id, "content-key")
        assert result == "content-value"

    def test_set_overwrites_existing(self, session_id: str) -> None:
        """set() overwrites existing value."""
        state.set(session_id, "overwrite-key", "old-value")
        state.set(session_id, "overwrite-key", "new-value")
        result = state.get(session_id, "overwrite-key")
        assert result == "new-value"

    def test_set_multiline_value(self, session_id: str) -> None:
        """set() handles multiline values."""
        multiline = "line1\nline2\nline3"
        state.set(session_id, "multiline-key", multiline)
        result = state.get(session_id, "multiline-key")
        assert result == multiline

    def test_set_creates_directory_if_missing(self, session_id: str, state_dir: Path) -> None:
        """set() creates state directory if it doesn't exist."""
        # Remove directory to test creation
        if state_dir.exists():
            for file in state_dir.glob("*"):
                file.unlink()
            state_dir.rmdir()

        state.set(session_id, "test-key", "test-value")
        assert state_dir.exists()
        assert state_dir.is_dir()


class TestStateClear:
    """Tests for state.clear()."""

    def test_clear_existing_key(self, session_id: str, state_dir: Path) -> None:
        """clear() removes existing key."""
        state.set(session_id, "clear-key", "clear-value")
        state.clear(session_id, "clear-key")

        file_path = state_dir / f"{session_id}-clear-key"
        assert not file_path.exists()

    def test_clear_nonexistent_key(self, session_id: str) -> None:
        """clear() succeeds silently for nonexistent key."""
        # Should not raise an error
        state.clear(session_id, "nonexistent-key")

    def test_clear_makes_get_return_none(self, session_id: str) -> None:
        """clear() makes get() return None."""
        state.set(session_id, "temp-key", "temp-value")
        state.clear(session_id, "temp-key")
        result = state.get(session_id, "temp-key")
        assert result is None


class TestStateExists:
    """Tests for state.exists()."""

    def test_exists_for_existing_key(self, session_id: str) -> None:
        """exists() returns True for existing key."""
        state.set(session_id, "exists-key", "exists-value")
        assert state.exists(session_id, "exists-key") is True

    def test_exists_for_nonexistent_key(self, session_id: str) -> None:
        """exists() returns False for nonexistent key."""
        assert state.exists(session_id, "nonexistent-key") is False

    def test_exists_after_clear(self, session_id: str) -> None:
        """exists() returns False after clear()."""
        state.set(session_id, "temp-key", "temp-value")
        state.clear(session_id, "temp-key")
        assert state.exists(session_id, "temp-key") is False

    def test_exists_for_empty_value(self, session_id: str) -> None:
        """exists() returns True for empty value."""
        state.set(session_id, "empty-key", "")
        assert state.exists(session_id, "empty-key") is True


class TestStatePermissions:
    """Tests for permission and error handling."""

    def test_fails_on_permission_error(self, session_id: str, state_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """set() raises on permission error."""
        # Make state directory read-only
        original_mode = state_dir.stat().st_mode if state_dir.exists() else None

        try:
            state_dir.mkdir(parents=True, exist_ok=True)
            state_dir.chmod(0o444)  # Read-only

            with pytest.raises(PermissionError):
                state.set(session_id, "perm-key", "perm-value")
        finally:
            # Restore permissions
            if original_mode:
                state_dir.chmod(original_mode)
            else:
                state_dir.chmod(0o755)


class TestStateIsolation:
    """Tests for session isolation."""

    def test_different_sessions_isolated(self) -> None:
        """Different sessions have isolated state."""
        session1 = "session-1"
        session2 = "session-2"

        state.set(session1, "shared-key", "value-1")
        state.set(session2, "shared-key", "value-2")

        assert state.get(session1, "shared-key") == "value-1"
        assert state.get(session2, "shared-key") == "value-2"

        # Cleanup
        state.clear(session1, "shared-key")
        state.clear(session2, "shared-key")
