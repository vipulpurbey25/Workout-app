"""Validate inputs, call Groq, and parse a weekly plan."""

from __future__ import annotations

import json
import os
from typing import Any

from groq import Groq

from workout_planner.errors import (
    API_MESSAGE,
    EMPTY_MESSAGE,
    MALFORMED_MESSAGE,
    MISSING_KEY_MESSAGE,
    PlanGenerationError,
)
from workout_planner.models import Exercise, TrainingDay, WorkoutPlan
from workout_planner.prompt import build_workout_prompt
from workout_planner.validation import validate_plan_inputs

DEFAULT_MODEL = "openai/gpt-oss-20b"
SYSTEM_PROMPT = (
    "You are a careful strength coach. Respond with a single JSON object that "
    "matches the requested shape. Do not include markdown. "
    "Do not diagnose injuries, prescribe treatment, or make medical claims. "
    "When a limitation is reported, name that limitation in the notes of each affected exercise. "
    "Keep each training day to 4-6 exercises and about 45-60 minutes."
)


def generate_workout_plan(
    goal: str,
    experience: str,
    days_per_week: int,
    equipment: list[str],
    injuries: str | None = None,
    *,
    client: Any = None,
    model: str = DEFAULT_MODEL,
) -> WorkoutPlan:
    """Build a prompt, call Groq, and return a parsed plan.

    Invalid inputs and API or parse failures raise PlanGenerationError with a
    message that can be shown directly. Validation runs before any network call.
    """
    limitation = validate_plan_inputs(
        goal=goal,
        experience=experience,
        days_per_week=days_per_week,
        equipment=equipment,
        injuries=injuries,
    )
    prompt = build_workout_prompt(
        goal=goal,
        experience=experience,
        days_per_week=days_per_week,
        equipment=equipment,
        injuries=limitation,
    )
    groq_client = client if client is not None else _build_client()
    try:
        raw = _request_completion(groq_client, model, prompt)
        return _parse_workout_plan(
            raw,
            goal=goal,
            experience=experience,
            days_per_week=days_per_week,
            equipment=tuple(equipment),
        )
    except PlanGenerationError:
        raise
    except Exception as exc:
        raise PlanGenerationError(API_MESSAGE) from exc


def _build_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise PlanGenerationError(MISSING_KEY_MESSAGE)
    return Groq(api_key=api_key)


def _request_completion(client: Any, model: str, prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
    except Exception as exc:
        raise PlanGenerationError(API_MESSAGE) from exc

    choices = getattr(response, "choices", None) or []
    if not choices:
        raise PlanGenerationError(EMPTY_MESSAGE)
    content = getattr(choices[0].message, "content", None)
    if content is None or not str(content).strip():
        raise PlanGenerationError(EMPTY_MESSAGE)
    return str(content)


def _parse_workout_plan(
    raw: str,
    *,
    goal: str,
    experience: str,
    days_per_week: int,
    equipment: tuple[str, ...],
) -> WorkoutPlan:
    try:
        payload = json.loads(_strip_json_fence(raw))
        plan = _plan_from_payload(
            payload,
            goal=goal,
            experience=experience,
            days_per_week=days_per_week,
            equipment=equipment,
        )
    except PlanGenerationError:
        raise
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise PlanGenerationError(MALFORMED_MESSAGE) from exc
    return plan


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _plan_from_payload(
    payload: object,
    *,
    goal: str,
    experience: str,
    days_per_week: int,
    equipment: tuple[str, ...],
) -> WorkoutPlan:
    if not isinstance(payload, dict):
        raise PlanGenerationError(MALFORMED_MESSAGE)

    nutrition = _required_text(payload.get("nutrition_note"))
    recovery = _required_text(payload.get("recovery_note"))
    weekly = payload.get("weekly_plan")
    if not isinstance(weekly, list) or len(weekly) != days_per_week:
        raise PlanGenerationError(MALFORMED_MESSAGE)

    days = tuple(_parse_day(item) for item in weekly)
    return WorkoutPlan(
        goal=goal,
        experience=experience,
        days_per_week=days_per_week,
        equipment=equipment,
        nutrition_note=nutrition,
        recovery_note=recovery,
        days=days,
    )


def _parse_day(item: object) -> TrainingDay:
    if not isinstance(item, dict):
        raise PlanGenerationError(MALFORMED_MESSAGE)
    exercises_raw = item.get("exercises")
    if not isinstance(exercises_raw, list) or not exercises_raw:
        raise PlanGenerationError(MALFORMED_MESSAGE)
    return TrainingDay(
        day=_required_text(item.get("day")),
        focus=_required_text(item.get("focus")),
        warmup=_required_text(item.get("warmup")),
        exercises=tuple(_parse_exercise(exercise) for exercise in exercises_raw),
    )


def _parse_exercise(item: object) -> Exercise:
    if not isinstance(item, dict):
        raise PlanGenerationError(MALFORMED_MESSAGE)
    return Exercise(
        name=_required_text(item.get("name")),
        sets=_required_sets(item.get("sets")),
        reps=_required_text(item.get("reps")),
        rest=_optional_text(item.get("rest")),
        notes=_optional_text(item.get("notes")),
    )


def _required_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PlanGenerationError(MALFORMED_MESSAGE)
    return value.strip()


def _optional_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise PlanGenerationError(MALFORMED_MESSAGE)
    return value.strip()


def _required_sets(value: object) -> int:
    if isinstance(value, bool):
        raise PlanGenerationError(MALFORMED_MESSAGE)
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit() and int(value.strip()) > 0:
        return int(value.strip())
    raise PlanGenerationError(MALFORMED_MESSAGE)
