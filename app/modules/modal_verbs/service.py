from __future__ import annotations

import hashlib
import json
import random

from .content import TOTAL_TOPICS, load_topics
from .schemas import ModalVerbTopic

MASTERY_THRESHOLD = 2

def parse_topic_set(raw: str) -> set[int]:
    try:
        values = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return set()
    if not isinstance(values, list):
        return set()
    return {int(value) for value in values if isinstance(value, int) or str(value).isdigit()}

def dump_topic_set(values: set[int]) -> str:
    return json.dumps(sorted(values), ensure_ascii=False)

def first_uncompleted(completed: set[int]) -> int:
    for topic in load_topics():
        if topic.order not in completed:
            return topic.order
    return TOTAL_TOPICS

def progress_bar(completed_count: int, total: int = TOTAL_TOPICS, width: int = 10) -> str:
    if total <= 0:
        return "░" * width
    ratio = max(0.0, min(1.0, completed_count / total))
    filled = round(ratio * width)
    return "▓" * filled + "░" * (width - filled)

def accuracy(correct: int, total: int) -> int:
    return round(correct / total * 100) if total else 0

def option_order(attempt_id: int, topic: ModalVerbTopic, quiz_index: int) -> tuple[int, ...]:
    """Stable shuffled order for one attempt and one quiz."""
    quiz = topic.quizzes[quiz_index]
    seed_material = f"{attempt_id}:{topic.id}:{quiz_index}:modal-verbs-v1".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    indices = list(range(len(quiz.options)))
    random.Random(seed).shuffle(indices)
    return tuple(indices)
