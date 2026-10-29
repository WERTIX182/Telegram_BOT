from __future__ import annotations

from .callbacks import ExtraPracticeActionCallback

def extra_practice_callback(level_code: str, card_order: int) -> str:
    """Return callback data for the add-on's two-question collocation practice."""
    normalized = level_code.lower()
    if normalized not in {"i", "a"}:
        raise ValueError("level_code must be 'i' (Intermediate) or 'a' (Advanced).")
    if not 1 <= card_order <= 54:
        raise ValueError("card_order must be between 1 and 54.")
    return ExtraPracticeActionCallback(
        action="start", level_code=normalized, card_order=card_order
    ).pack()
