"""User-facing failures. The page shows `message` and does not render a traceback."""

from __future__ import annotations


class PlanGenerationError(Exception):
    """Raised when a plan cannot be generated. `message` is safe to show."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


DAYS_MESSAGE = "Choose between 1 and 7 training days before generating a plan."
EQUIPMENT_REQUIRED_MESSAGE = "Select at least one equipment option."
EQUIPMENT_UNKNOWN_MESSAGE = (
    "Choose equipment from the list: No equipment, Home dumbbells, or Full gym."
)
EQUIPMENT_CONFLICT_MESSAGE = (
    "Choose either No equipment or the gear you have, not both."
)
GOAL_MESSAGE = "Choose a fitness goal from the list."
EXPERIENCE_MESSAGE = "Choose an experience level from the list."
API_MESSAGE = (
    "The plan service is unavailable right now. Check your connection and API key, "
    "then try again."
)
MISSING_KEY_MESSAGE = "Add your Groq API key to the .env file and restart the app."
EMPTY_MESSAGE = "The planner returned an empty plan. Please try again."
MALFORMED_MESSAGE = "The planner returned a plan we couldn't read. Please try again."
