"""Fixed injury disclaimer. The model is not asked to write this sentence."""

from __future__ import annotations

INJURY_DISCLAIMER = (
    "This plan is general training guidance, not medical advice. "
    "Stop if pain increases, and check with a clinician before training through an injury."
)


def injury_disclaimer(injuries: str | None) -> str | None:
    """Return the fixed disclaimer when the user reported a limitation."""
    if injuries is None or not injuries.strip():
        return None
    return INJURY_DISCLAIMER
