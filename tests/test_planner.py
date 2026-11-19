"""Planner behavior. These tests use a fake Groq client and never hit the network."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from workout_planner.errors import PlanGenerationError
from workout_planner.planner import build_workout_prompt, generate_workout_plan
from workout_planner.validation import validate_plan_inputs


def _client_with_content(content: str | None) -> MagicMock:
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = response
    return client


def _valid_payload(day_count: int = 2) -> dict[str, Any]:
    days = []
    for index in range(1, day_count + 1):
        days.append(
            {
                "day": f"Day {index}",
                "focus": "Full body",
                "warmup": "5 minutes of easy marching and arm circles",
                "exercises": [
                    {
                        "name": "Goblet squat",
                        "sets": 3,
                        "reps": "8-10",
                        "rest": "90s",
                        "notes": "Keep heels down",
                    }
                ],
            }
        )
    return {
        "nutrition_note": "Eat protein at each meal and drink water through the day.",
        "recovery_note": "Leave at least one rest day between hard sessions.",
        "weekly_plan": days,
    }


def test_zero_days_is_rejected_without_calling_groq() -> None:
    client = MagicMock()

    with pytest.raises(PlanGenerationError, match="1 and 7"):
        generate_workout_plan(
            goal="Build muscle",
            experience="Beginner",
            days_per_week=0,
            equipment=["Full gym"],
            injuries=None,
            client=client,
        )

    client.chat.completions.create.assert_not_called()


@pytest.mark.parametrize("days", [-1, 8, True, 3.5, "3"])
def test_days_outside_one_to_seven_are_rejected(days: object) -> None:
    with pytest.raises(PlanGenerationError, match="1 and 7"):
        validate_plan_inputs(
            goal="Lose fat",
            experience="Intermediate",
            days_per_week=days,  # type: ignore[arg-type]
            equipment=["No equipment"],
            injuries="",
        )


def test_empty_equipment_is_rejected_without_calling_groq() -> None:
    client = MagicMock()

    with pytest.raises(PlanGenerationError, match="at least one"):
        generate_workout_plan(
            goal="General fitness",
            experience="Beginner",
            days_per_week=3,
            equipment=[],
            injuries="",
            client=client,
        )

    client.chat.completions.create.assert_not_called()


def test_no_equipment_cannot_be_combined_with_gear() -> None:
    with pytest.raises(PlanGenerationError, match="No equipment"):
        validate_plan_inputs(
            goal="Improve endurance",
            experience="Advanced",
            days_per_week=4,
            equipment=["No equipment", "Home dumbbells"],
            injuries=None,
        )


def test_unknown_equipment_is_rejected() -> None:
    with pytest.raises(PlanGenerationError, match="equipment"):
        validate_plan_inputs(
            goal="Build muscle",
            experience="Beginner",
            days_per_week=2,
            equipment=["Kettlebells"],
            injuries=None,
        )


def test_unknown_goal_and_experience_are_rejected() -> None:
    with pytest.raises(PlanGenerationError, match="fitness goal"):
        validate_plan_inputs(
            goal="Get shredded",
            experience="Beginner",
            days_per_week=2,
            equipment=["Full gym"],
            injuries=None,
        )

    with pytest.raises(PlanGenerationError, match="experience"):
        validate_plan_inputs(
            goal="Build muscle",
            experience="Elite",
            days_per_week=2,
            equipment=["Full gym"],
            injuries=None,
        )


def test_prompt_includes_inputs_and_asks_for_json() -> None:
    prompt = build_workout_prompt(
        goal="Build muscle",
        experience="Beginner",
        days_per_week=3,
        equipment=["Home dumbbells", "Full gym"],
        injuries="bad knees",
    )

    assert "Build muscle" in prompt
    assert "Beginner" in prompt
    assert "3" in prompt
    assert "Home dumbbells" in prompt
    assert "Full gym" in prompt
    assert "bad knees" in prompt
    assert "JSON" in prompt
    assert "nutrition_note" in prompt
    assert "warmup" in prompt


def test_blank_injuries_are_described_as_none_reported() -> None:
    prompt = build_workout_prompt(
        goal="Lose fat",
        experience="Intermediate",
        days_per_week=2,
        equipment=["No equipment"],
        injuries="   ",
    )

    assert "None reported" in prompt


def test_generate_plan_parses_a_json_week() -> None:
    client = _client_with_content(json.dumps(_valid_payload(2)))

    plan = generate_workout_plan(
        goal="Build muscle",
        experience="Beginner",
        days_per_week=2,
        equipment=["Home dumbbells"],
        injuries="no overhead pressing",
        client=client,
    )

    assert plan.days_per_week == 2
    assert len(plan.days) == 2
    assert plan.days[0].focus == "Full body"
    assert plan.days[0].exercises[0].name == "Goblet squat"
    assert plan.days[0].exercises[0].sets == 3
    assert "protein" in plan.nutrition_note
    assert plan.recovery_note
    sent = client.chat.completions.create.call_args.kwargs
    assert sent["model"] == "openai/gpt-oss-20b"
    assert sent["response_format"] == {"type": "json_object"}


def test_system_prompt_blocks_medical_advice_and_caps_the_session() -> None:
    client = _client_with_content(json.dumps(_valid_payload(1)))

    generate_workout_plan(
        goal="General fitness",
        experience="Beginner",
        days_per_week=1,
        equipment=["No equipment"],
        injuries="bad knees",
        client=client,
    )

    system_message = client.chat.completions.create.call_args.kwargs["messages"][0]
    text = system_message["content"]
    lowered = text.lower()
    assert system_message["role"] == "system"
    assert "diagnos" in lowered
    assert "treatment" in lowered
    assert "medical" in lowered
    assert "4-6" in text
    assert "45-60" in text
    assert "limitation" in lowered


def test_json_wrapped_in_a_fence_still_parses() -> None:
    fenced = "```json\n" + json.dumps(_valid_payload(1)) + "\n```"
    client = _client_with_content(fenced)

    plan = generate_workout_plan(
        goal="General fitness",
        experience="Advanced",
        days_per_week=1,
        equipment=["Full gym"],
        injuries=None,
        client=client,
    )

    assert len(plan.days) == 1


def test_api_failure_is_a_friendly_message() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("invalid api key")

    with pytest.raises(PlanGenerationError, match="unavailable"):
        generate_workout_plan(
            goal="Lose fat",
            experience="Beginner",
            days_per_week=3,
            equipment=["No equipment"],
            injuries=None,
            client=client,
        )


def test_empty_model_response_is_a_friendly_fallback() -> None:
    client = _client_with_content("   ")

    with pytest.raises(PlanGenerationError, match="empty"):
        generate_workout_plan(
            goal="Lose fat",
            experience="Beginner",
            days_per_week=1,
            equipment=["No equipment"],
            injuries=None,
            client=client,
        )


def test_malformed_model_response_is_a_friendly_fallback() -> None:
    client = _client_with_content("this is not a week")

    with pytest.raises(PlanGenerationError, match="couldn't read"):
        generate_workout_plan(
            goal="Lose fat",
            experience="Beginner",
            days_per_week=1,
            equipment=["No equipment"],
            injuries=None,
            client=client,
        )


def test_wrong_day_count_is_treated_as_malformed() -> None:
    client = _client_with_content(json.dumps(_valid_payload(1)))

    with pytest.raises(PlanGenerationError, match="couldn't read"):
        generate_workout_plan(
            goal="Improve endurance",
            experience="Intermediate",
            days_per_week=3,
            equipment=["No equipment"],
            injuries=None,
            client=client,
        )


def test_missing_api_key_is_friendly_when_no_client_is_injected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(PlanGenerationError, match="API key"):
        generate_workout_plan(
            goal="General fitness",
            experience="Beginner",
            days_per_week=2,
            equipment=["No equipment"],
            injuries=None,
        )
