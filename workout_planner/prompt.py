"""Prompt text for a single JSON workout week."""

from __future__ import annotations


def build_workout_prompt(
    goal: str,
    experience: str,
    days_per_week: int,
    equipment: list[str],
    injuries: str | None,
) -> str:
    """Describe the user and the exact JSON object the model must return."""
    limitation = (injuries or "").strip() or "None reported"
    gear = ", ".join(equipment)
    return f"""Create a {days_per_week}-day workout plan as JSON.

Person:
- Fitness goal: {goal}
- Experience: {experience}
- Training days this week: {days_per_week}
- Equipment: {gear}
- Injuries or limitations: {limitation}

Rules:
- Return one JSON object and no other text.
- weekly_plan must contain exactly {days_per_week} training days, labeled Day 1 onward.
- Use only the equipment listed. If equipment is "No equipment", use bodyweight movements.
- Honor every injury or limitation. Swap or shorten movements instead of ignoring them.
- Match volume and complexity to the experience level.
- Each day needs a short warmup, then exercises with sets, reps, rest, and notes.
- Add one brief nutrition_note for the goal and one brief recovery_note. Do not write a full meal plan.

JSON shape:
{{
  "nutrition_note": "string",
  "recovery_note": "string",
  "weekly_plan": [
    {{
      "day": "Day 1",
      "focus": "string",
      "warmup": "string",
      "exercises": [
        {{
          "name": "string",
          "sets": 3,
          "reps": "8-10",
          "rest": "90s",
          "notes": "string"
        }}
      ]
    }}
  ]
}}
"""
