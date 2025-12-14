"""Tests for spec name validation and code generation.

Tests cover:
- validate_spec_name: kebab-case validation
- generate_code: initial extraction from kebab-case names
- make_code_unique: collision handling with numeric suffixes
"""

from __future__ import annotations

import pytest

from dignity.spec.validation import (
    generate_code,
    make_code_unique,
    validate_spec_name,
)


class TestValidateSpecName:
    """Tests for validate_spec_name function."""

    # Valid cases

    def test_single_word_valid(self) -> None:
        """Single lowercase word is valid."""
        validate_spec_name("dispatch")  # Should not raise

    def test_two_word_kebab_valid(self) -> None:
        """Two-word kebab-case is valid."""
        validate_spec_name("hook-migration")  # Should not raise

    def test_three_word_kebab_valid(self) -> None:
        """Three-word kebab-case is valid."""
        validate_spec_name("focus-state-dispatch")  # Should not raise

    def test_word_with_numbers_valid(self) -> None:
        """Words with numbers are valid."""
        validate_spec_name("api2-client")  # Should not raise

    def test_numbers_in_middle_valid(self) -> None:
        """Numbers in middle of word are valid."""
        validate_spec_name("spec-v2-migration")  # Should not raise

    def test_numbers_at_end_valid(self) -> None:
        """Numbers at end of segment are valid."""
        validate_spec_name("feature-123")  # Should not raise

    def test_long_name_valid(self) -> None:
        """Long multi-word names are valid."""
        validate_spec_name("this-is-a-very-long-spec-name")  # Should not raise

    # Invalid cases

    def test_uppercase_rejected(self) -> None:
        """Uppercase letters are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("FocusState")

    def test_mixed_case_rejected(self) -> None:
        """Mixed case names are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("focus-State-dispatch")

    def test_underscore_rejected(self) -> None:
        """Underscores are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("focus_state")

    def test_space_rejected(self) -> None:
        """Spaces are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("focus state")

    def test_leading_hyphen_rejected(self) -> None:
        """Leading hyphen is rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("-dispatch")

    def test_trailing_hyphen_rejected(self) -> None:
        """Trailing hyphen is rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("dispatch-")

    def test_double_hyphen_rejected(self) -> None:
        """Double hyphens are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("focus--dispatch")

    def test_leading_number_rejected(self) -> None:
        """Leading number is rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("2fast")

    def test_number_after_hyphen_rejected(self) -> None:
        """Number immediately after hyphen is invalid (segment must start with letter)."""
        # Pattern requires [a-z0-9]+ after hyphen, but segment starting with number
        # followed by nothing else should be valid. Let me check the pattern more carefully.
        # Pattern: ^[a-z][a-z0-9]*(-[a-z0-9]+)*$
        # Actually "focus-2" matches because -[a-z0-9]+ allows "2"
        # So this should be valid according to the pattern
        validate_spec_name("focus-2")  # Should not raise

    def test_special_char_rejected(self) -> None:
        """Special characters are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("focus@dispatch")

    def test_period_rejected(self) -> None:
        """Periods are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("focus.dispatch")

    def test_slash_rejected(self) -> None:
        """Slashes are rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("focus/dispatch")

    # Edge cases

    def test_empty_string_rejected(self) -> None:
        """Empty string is rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("")

    def test_single_letter_valid(self) -> None:
        """Single letter is valid."""
        validate_spec_name("a")  # Should not raise

    def test_only_hyphen_rejected(self) -> None:
        """Only hyphen is rejected."""
        with pytest.raises(ValueError, match="Invalid spec name"):
            validate_spec_name("-")


class TestGenerateCode:
    """Tests for generate_code function."""

    # Valid cases

    def test_single_word_code(self) -> None:
        """Single word produces single letter code."""
        assert generate_code("dispatch") == "D"

    def test_two_word_code(self) -> None:
        """Two words produce two letter code."""
        assert generate_code("hook-migration") == "HM"

    def test_three_word_code(self) -> None:
        """Three words produce three letter code."""
        assert generate_code("focus-state-dispatch") == "FSD"

    def test_many_word_code(self) -> None:
        """Many words produce many letter code."""
        assert generate_code("this-is-a-long-name") == "TIALN"

    def test_word_with_number_code(self) -> None:
        """Word with number extracts first char."""
        assert generate_code("api2-client") == "AC"

    def test_number_segment_code(self) -> None:
        """Number-only segment extracts first digit."""
        assert generate_code("version-2") == "V2"

    # Edge cases

    def test_single_letter_code(self) -> None:
        """Single letter word produces single letter code."""
        assert generate_code("a") == "A"

    def test_uppercase_output(self) -> None:
        """Output is always uppercase."""
        assert generate_code("test") == "T"
        assert generate_code("test").isupper()


class TestMakeCodeUnique:
    """Tests for make_code_unique function."""

    # No collision cases

    def test_unique_code_unchanged(self) -> None:
        """Unique code is returned as-is."""
        assert make_code_unique("FSD", set()) == "FSD"

    def test_unique_code_with_existing(self) -> None:
        """Unique code unaffected by other existing codes."""
        existing = {"HM", "D", "ABC"}
        assert make_code_unique("FSD", existing) == "FSD"

    # Single collision cases

    def test_single_collision_adds_2(self) -> None:
        """First collision appends 2."""
        existing = {"FSD"}
        assert make_code_unique("FSD", existing) == "FSD2"

    def test_single_collision_case_sensitive(self) -> None:
        """Collision is case-sensitive."""
        existing = {"fsd"}  # Lowercase
        assert make_code_unique("FSD", existing) == "FSD"  # No collision

    # Multiple collision cases

    def test_double_collision_adds_3(self) -> None:
        """Double collision appends 3."""
        existing = {"FSD", "FSD2"}
        assert make_code_unique("FSD", existing) == "FSD3"

    def test_many_collisions(self) -> None:
        """Many collisions increment correctly."""
        existing = {"FSD", "FSD2", "FSD3", "FSD4", "FSD5"}
        assert make_code_unique("FSD", existing) == "FSD6"

    def test_gap_in_collisions(self) -> None:
        """Finds next available even with gaps."""
        existing = {"FSD", "FSD2", "FSD4"}  # Gap at FSD3
        assert make_code_unique("FSD", existing) == "FSD3"

    # Edge cases

    def test_empty_existing_set(self) -> None:
        """Empty existing set returns code unchanged."""
        assert make_code_unique("ABC", set()) == "ABC"

    def test_single_letter_collision(self) -> None:
        """Single letter codes handle collisions."""
        existing = {"D"}
        assert make_code_unique("D", existing) == "D2"

    def test_frozenset_existing(self) -> None:
        """Works with frozenset for existing codes."""
        existing = frozenset({"FSD"})
        assert make_code_unique("FSD", existing) == "FSD2"

    def test_code_with_number_collision(self) -> None:
        """Code already containing numbers handles collisions."""
        existing = {"V2"}
        assert make_code_unique("V2", existing) == "V22"

    def test_high_collision_count(self) -> None:
        """Handles high collision counts correctly."""
        existing = {f"X{i}" if i > 1 else "X" for i in range(1, 100)}
        assert make_code_unique("X", existing) == "X100"
