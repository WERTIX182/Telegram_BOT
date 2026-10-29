from __future__ import annotations

import hashlib
import json
import random

from .schemas import ExtraQuestion


def practice_key(level_code: str, card_order: int) -> str:
    return f"{level_code}:{card_order}"


def parse_key_set(raw: str) -> set[str]:
    try:
        values = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return set()
    if not isinstance(values, list):
        return set()
    return {str(value) for value in values}


def dump_key_set(values: set[str]) -> str:
    return json.dumps(sorted(values), ensure_ascii=False)


def option_order(attempt_id: int, question: ExtraQuestion) -> tuple[int, ...]:
    seed_material = f"{attempt_id}:{question.id}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    order = list(range(len(question.options)))
    random.Random(seed).shuffle(order)
    return tuple(order)


def accuracy(correct: int, total: int) -> int:
    return 0 if total <= 0 else round(correct / total * 100)