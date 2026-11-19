"""One-page workout planner. Streamlit collects inputs and renders the week."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from workout_planner.disclaimer import injury_disclaimer
from workout_planner.errors import PlanGenerationError
from workout_planner.models import WorkoutPlan
from workout_planner.planner import DEFAULT_MODEL, generate_workout_plan
from workout_planner.validation import EQUIPMENT_OPTIONS, EXPERIENCE_LEVELS, GOALS


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Workout Planner", page_icon="🏋️", layout="centered")
    _apply_styles()
    st.title("Workout Planner")
    st.caption("A week of training from your goal, schedule, and equipment.")

    goal = st.selectbox("Fitness goal", GOALS)
    experience = st.selectbox("Experience level", EXPERIENCE_LEVELS)
    days_per_week = st.number_input(
        "Days available per week",
        min_value=0,
        max_value=7,
        value=3,
        step=1,
        help="Use 0 only to see the validation message. Plans need 1 to 7 days.",
    )
    equipment = st.multiselect("Equipment access", EQUIPMENT_OPTIONS, default=["No equipment"])
    injuries = st.text_area(
        "Injuries or limitations (optional)",
        placeholder="bad knees, no overhead pressing",
    )

    if st.button("Generate Plan", type="primary"):
        _show_plan(
            goal=str(goal),
            experience=str(experience),
            days_per_week=int(days_per_week),
            equipment=list(equipment),
            injuries=injuries,
        )


def _show_plan(
    goal: str,
    experience: str,
    days_per_week: int,
    equipment: list[str],
    injuries: str,
) -> None:
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    with st.spinner("Building your week..."):
        try:
            plan = generate_workout_plan(
                goal=goal,
                experience=experience,
                days_per_week=days_per_week,
                equipment=equipment,
                injuries=injuries,
                model=model,
            )
        except PlanGenerationError as error:
            st.error(error.message)
            return
    _render_plan(plan, injuries)


def _render_plan(plan: WorkoutPlan, injuries: str) -> None:
    st.subheader("Your week")
    disclaimer = injury_disclaimer(injuries)
    if disclaimer is not None:
        st.caption(disclaimer)
    st.markdown(f"**Goal:** {plan.goal}  ·  **Level:** {plan.experience}")
    gear = ", ".join(plan.equipment)
    st.markdown(f"**Equipment:** {gear}")
    st.info(plan.nutrition_note)
    st.warning(plan.recovery_note)
    for training_day in plan.days:
        with st.expander(f"{training_day.day} — {training_day.focus}", expanded=True):
            st.markdown(f"**Warm-up.** {training_day.warmup}")
            for exercise in training_day.exercises:
                rest = f", rest {exercise.rest}" if exercise.rest else ""
                st.markdown(
                    f"- **{exercise.name}** — {exercise.sets} sets × {exercise.reps}{rest}"
                )
                if exercise.notes:
                    st.caption(exercise.notes)


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
          h1 {
            letter-spacing: -0.03em;
          }
          div[data-testid="stExpander"] {
            background: #fffdf8;
            border: 1px solid #e2d8c8;
            border-radius: 12px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
