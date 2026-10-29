from __future__ import annotations

import json

from app.quiz_utils import stable_option_order

from .content import load_topics
from .schemas import GrammarTopic

MASTERY_THRESHOLD = 2

def option_order(attempt_id: int, topic: GrammarTopic, quiz_index: int) -> tuple[int, ...]:
    quiz = topic.quizzes[quiz_index]
    return stable_option_order(
        attempt_id=attempt_id,
        item_id=topic.id,
        question_index=quiz_index,
        option_count=len(quiz.options),
    )

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
    return len(load_topics())

def progress_bar(completed_count: int, total: int = 70, width: int = 10) -> str:
    if total <= 0:
        return "░" * width
    ratio = max(0.0, min(1.0, completed_count / total))
    filled = round(ratio * width)
    return "▓" * filled + "░" * (width - filled)

def accuracy(correct: int, total: int) -> int:
    return round(correct / total * 100) if total else 0
