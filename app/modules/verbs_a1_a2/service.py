from __future__ import annotations

import json

from app.quiz_utils import stable_option_order

from .content import load_cards
from .schemas import VerbCard

def option_order(attempt_id: int, card: VerbCard) -> tuple[int, ...]:
    return stable_option_order(
        attempt_id=attempt_id,
        item_id=card.id,
        question_index=0,
        option_count=len(card.quiz.options),
    )

def parse_card_set(raw: str) -> set[int]:
    try:
        values = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return set()
    if not isinstance(values, list):
        return set()
    return {int(value) for value in values if isinstance(value, int) or str(value).isdigit()}

def dump_card_set(values: set[int]) -> str:
    return json.dumps(sorted(values), ensure_ascii=False)

def first_uncompleted(completed: set[int]) -> int:
    for card in load_cards():
        if card.order not in completed:
            return card.order
    return len(load_cards())

def progress_bar(completed_count: int, total: int = 50, width: int = 10) -> str:
    if total <= 0:
        return "░" * width
    ratio = max(0.0, min(1.0, completed_count / total))
    filled = round(ratio * width)
    return "▓" * filled + "░" * (width - filled)

def accuracy(correct: int, total: int) -> int:
    return round(correct / total * 100) if total else 0
