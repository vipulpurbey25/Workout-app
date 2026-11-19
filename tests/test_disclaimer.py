"""The injury disclaimer is fixed copy. The model does not write it."""

from __future__ import annotations

from workout_planner.disclaimer import injury_disclaimer


def test_injuries_show_a_fixed_non_medical_disclaimer() -> None:
    text = injury_disclaimer("bad knees")

    assert text is not None
    assert "not medical advice" in text.lower()
    assert text == injury_disclaimer("no overhead pressing")


def test_blank_injuries_do_not_show_a_disclaimer() -> None:
    assert injury_disclaimer(None) is None
    assert injury_disclaimer("   ") is None
    assert injury_disclaimer("") is None
