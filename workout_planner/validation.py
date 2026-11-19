"""Reject inputs that must never be sent to Groq."""

from __future__ import annotations

from workout_planner.errors import (
    DAYS_MESSAGE,
    EQUIPMENT_CONFLICT_MESSAGE,
    EQUIPMENT_REQUIRED_MESSAGE,
    EQUIPMENT_UNKNOWN_MESSAGE,
    EXPERIENCE_MESSAGE,
    GOAL_MESSAGE,
    PlanGenerationError,
)

GOALS: tuple[str, ...] = (
    "Build muscle",
    "Lose fat",
    "General fitness",
    "Improve endurance",
)
EXPERIENCE_LEVELS: tuple[str, ...] = ("Beginner", "Intermediate", "Advanced")
EQUIPMENT_OPTIONS: tuple[str, ...] = ("No equipment", "Home dumbbells", "Full gym")


def validate_plan_inputs(
    goal: str,
    experience: str,
    days_per_week: int,
    equipment: list[str],
    injuries: str | None,
) -> str:
    """Return the injuries text to place in the prompt. Raise before any API call."""
    if goal not in GOALS:
        raise PlanGenerationError(GOAL_MESSAGE)
    if experience not in EXPERIENCE_LEVELS:
        raise PlanGenerationError(EXPERIENCE_MESSAGE)
    if isinstance(days_per_week, bool) or not isinstance(days_per_week, int):
        raise PlanGenerationError(DAYS_MESSAGE)
    if days_per_week < 1 or days_per_week > 7:
        raise PlanGenerationError(DAYS_MESSAGE)
    if not isinstance(equipment, list) or not equipment:
        raise PlanGenerationError(EQUIPMENT_REQUIRED_MESSAGE)
    if any(item not in EQUIPMENT_OPTIONS for item in equipment):
        raise PlanGenerationError(EQUIPMENT_UNKNOWN_MESSAGE)
    if "No equipment" in equipment and len(equipment) > 1:
        raise PlanGenerationError(EQUIPMENT_CONFLICT_MESSAGE)

    cleaned = (injuries or "").strip()
    return cleaned if cleaned else "None reported"
