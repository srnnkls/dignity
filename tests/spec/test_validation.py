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


# validate_spec_name valid cases


def test_validate_spec_name_single_word_valid() -> None:
    """Single lowercase word is valid."""
    validate_spec_name("dispatch")


def test_validate_spec_name_two_word_kebab_valid() -> None:
    """Two-word kebab-case is valid."""
    validate_spec_name("hook-migration")


def test_validate_spec_name_three_word_kebab_valid() -> None:
    """Three-word kebab-case is valid."""
    validate_spec_name("focus-state-dispatch")


def test_validate_spec_name_word_with_numbers_valid() -> None:
    """Words with numbers are valid."""
    validate_spec_name("api2-client")


def test_validate_spec_name_numbers_in_middle_valid() -> None:
    """Numbers in middle of word are valid."""
    validate_spec_name("spec-v2-migration")


def test_validate_spec_name_numbers_at_end_valid() -> None:
    """Numbers at end of segment are valid."""
    validate_spec_name("feature-123")


def test_validate_spec_name_long_name_valid() -> None:
    """Long multi-word names are valid."""
    validate_spec_name("this-is-a-very-long-spec-name")


# validate_spec_name invalid cases


def test_validate_spec_name_uppercase_rejected() -> None:
    """Uppercase letters are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("FocusState")


def test_validate_spec_name_mixed_case_rejected() -> None:
    """Mixed case names are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("focus-State-dispatch")


def test_validate_spec_name_underscore_rejected() -> None:
    """Underscores are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("focus_state")


def test_validate_spec_name_space_rejected() -> None:
    """Spaces are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("focus state")


def test_validate_spec_name_leading_hyphen_rejected() -> None:
    """Leading hyphen is rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("-dispatch")


def test_validate_spec_name_trailing_hyphen_rejected() -> None:
    """Trailing hyphen is rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("dispatch-")


def test_validate_spec_name_double_hyphen_rejected() -> None:
    """Double hyphens are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("focus--dispatch")


def test_validate_spec_name_leading_number_rejected() -> None:
    """Leading number is rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("2fast")


def test_validate_spec_name_number_after_hyphen_valid() -> None:
    """Number immediately after hyphen is valid (segment can start with number)."""
    validate_spec_name("focus-2")


def test_validate_spec_name_special_char_rejected() -> None:
    """Special characters are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("focus@dispatch")


def test_validate_spec_name_period_rejected() -> None:
    """Periods are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("focus.dispatch")


def test_validate_spec_name_slash_rejected() -> None:
    """Slashes are rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("focus/dispatch")


# validate_spec_name edge cases


def test_validate_spec_name_empty_string_rejected() -> None:
    """Empty string is rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("")


def test_validate_spec_name_single_letter_valid() -> None:
    """Single letter is valid."""
    validate_spec_name("a")


def test_validate_spec_name_only_hyphen_rejected() -> None:
    """Only hyphen is rejected."""
    with pytest.raises(ValueError, match="Invalid spec name"):
        validate_spec_name("-")


# generate_code valid cases


def test_generate_code_single_word_code() -> None:
    """Single word produces single letter code."""
    assert generate_code("dispatch") == "D"


def test_generate_code_two_word_code() -> None:
    """Two words produce two letter code."""
    assert generate_code("hook-migration") == "HM"


def test_generate_code_three_word_code() -> None:
    """Three words produce three letter code."""
    assert generate_code("focus-state-dispatch") == "FSD"


def test_generate_code_many_word_code() -> None:
    """Many words produce many letter code."""
    assert generate_code("this-is-a-long-name") == "TIALN"


def test_generate_code_word_with_number_code() -> None:
    """Word with number extracts first char."""
    assert generate_code("api2-client") == "AC"


def test_generate_code_number_segment_code() -> None:
    """Number-only segment extracts first digit."""
    assert generate_code("version-2") == "V2"


# generate_code edge cases


def test_generate_code_single_letter_code() -> None:
    """Single letter word produces single letter code."""
    assert generate_code("a") == "A"


def test_generate_code_uppercase_output() -> None:
    """Output is always uppercase."""
    assert generate_code("test") == "T"
    assert generate_code("test").isupper()


# make_code_unique no collision cases


def test_make_code_unique_unique_code_unchanged() -> None:
    """Unique code is returned as-is."""
    assert make_code_unique("FSD", set()) == "FSD"


def test_make_code_unique_unique_code_with_existing() -> None:
    """Unique code unaffected by other existing codes."""
    existing = {"HM", "D", "ABC"}
    assert make_code_unique("FSD", existing) == "FSD"


# make_code_unique single collision cases


def test_make_code_unique_single_collision_adds_2() -> None:
    """First collision appends 2."""
    existing = {"FSD"}
    assert make_code_unique("FSD", existing) == "FSD2"


def test_make_code_unique_single_collision_case_sensitive() -> None:
    """Collision is case-sensitive."""
    existing = {"fsd"}
    assert make_code_unique("FSD", existing) == "FSD"


# make_code_unique multiple collision cases


def test_make_code_unique_double_collision_adds_3() -> None:
    """Double collision appends 3."""
    existing = {"FSD", "FSD2"}
    assert make_code_unique("FSD", existing) == "FSD3"


def test_make_code_unique_many_collisions() -> None:
    """Many collisions increment correctly."""
    existing = {"FSD", "FSD2", "FSD3", "FSD4", "FSD5"}
    assert make_code_unique("FSD", existing) == "FSD6"


def test_make_code_unique_gap_in_collisions() -> None:
    """Finds next available even with gaps."""
    existing = {"FSD", "FSD2", "FSD4"}
    assert make_code_unique("FSD", existing) == "FSD3"


# make_code_unique edge cases


def test_make_code_unique_empty_existing_set() -> None:
    """Empty existing set returns code unchanged."""
    assert make_code_unique("ABC", set()) == "ABC"


def test_make_code_unique_single_letter_collision() -> None:
    """Single letter codes handle collisions."""
    existing = {"D"}
    assert make_code_unique("D", existing) == "D2"


def test_make_code_unique_frozenset_existing() -> None:
    """Works with frozenset for existing codes."""
    existing = frozenset({"FSD"})
    assert make_code_unique("FSD", existing) == "FSD2"


def test_make_code_unique_code_with_number_collision() -> None:
    """Code already containing numbers handles collisions."""
    existing = {"V2"}
    assert make_code_unique("V2", existing) == "V22"


def test_make_code_unique_high_collision_count() -> None:
    """Handles high collision counts correctly."""
    existing = {f"X{i}" if i > 1 else "X" for i in range(1, 100)}
    assert make_code_unique("X", existing) == "X100"
