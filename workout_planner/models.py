"""Structured workout plan returned after a successful Groq response."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    name: str
    sets: int
    reps: str
    rest: str
    notes: str


@dataclass(frozen=True)
class TrainingDay:
    day: str
    focus: str
    warmup: str
    exercises: tuple[Exercise, ...]


@dataclass(frozen=True)
class WorkoutPlan:
    goal: str
    experience: str
    days_per_week: int
    equipment: tuple[str, ...]
    nutrition_note: str
    recovery_note: str
    days: tuple[TrainingDay, ...]
