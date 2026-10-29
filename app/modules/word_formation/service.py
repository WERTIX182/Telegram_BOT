from __future__ import annotations

import hashlib
import json
import random

from .content import TOTAL_CARDS, load_cards
from .schemas import WordFormationCard

def parse_card_set(raw: str) -> set[int]:
    try:
        values = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return set()
    if not isinstance(values, list):
        return set()
    result: set[int] = set()
    for value in values:
        if isinstance(value, int):
            result.add(value)
        elif isinstance(value, str) and value.isdigit():
            result.add(int(value))
    return result

def dump_card_set(values: set[int]) -> str:
    return json.dumps(sorted(values), ensure_ascii=False)

def first_uncompleted(completed: set[int]) -> int:
    for card in load_cards():
        if card.order not in completed:
            return card.order
    return TOTAL_CARDS

def progress_bar(completed_count: int, total: int = TOTAL_CARDS, width: int = 10) -> str:
    if total <= 0:
        return "░" * width
    ratio = max(0.0, min(1.0, completed_count / total))
    filled = round(ratio * width)
    return "▓" * filled + "░" * (width - filled)

def accuracy(correct: int, total: int) -> int:
    return round(correct / total * 100) if total else 0

def option_order(attempt_id: int, card: WordFormationCard) -> tuple[int, ...]:
    """Return a stable shuffled option order for one saved attempt."""
    seed_material = f"{attempt_id}:{card.id}:word-formation-v1".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    indices = list(range(len(card.quiz.options)))
    random.Random(seed).shuffle(indices)
    return tuple(indices)
