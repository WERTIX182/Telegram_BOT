from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from .schemas import CommonMistake, GrammarExample, GrammarQuiz, GrammarTopic

COURSE_ID = "grammar_c1_v1"
COURSE_VERSION = "2026-07-v1"
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILES = (DATA_DIR / "grammar_c1.json",)

@lru_cache(maxsize=1)
def load_topics() -> tuple[GrammarTopic, ...]:
    raw_items: list[dict] = []
    for path in DATA_FILES:
        with path.open("r", encoding="utf-8") as source:
            raw_items.extend(json.load(source))

    topics = tuple(_parse_topic(item) for item in raw_items)
    validate_topics(topics)
    return topics

def _parse_topic(item: dict) -> GrammarTopic:
    mistake = item["common_mistake"]
    return GrammarTopic(
        id=item["id"],
        order=item["order"],
        level=item["level"],
        category=item["category"],
        title_en=item["title_en"],
        title_ru=item["title_ru"],
        rule=item["rule"],
        forms=tuple(item["forms"]),
        examples=tuple(GrammarExample(**example) for example in item["examples"]),
        common_mistake=CommonMistake(**mistake),
        quizzes=tuple(
            GrammarQuiz(
                prompt=quiz["prompt"],
                options=tuple(quiz["options"]),
                correct_index=quiz["correct_index"],
                explanation=quiz["explanation"],
            )
            for quiz in item["quizzes"]
        ),
    )

def validate_topics(topics: tuple[GrammarTopic, ...]) -> None:
    if len(topics) != 70:
        raise ValueError("C1 grammar course must contain exactly 70 topics.")

    orders = [topic.order for topic in topics]
    if orders != list(range(1, 71)):
        raise ValueError("Topic orders must be continuous from 1 to 70.")

    ids = [topic.id for topic in topics]
    if len(ids) != len(set(ids)):
        raise ValueError("Topic IDs must be unique.")

    level_counts = {"C1": 0}
    for topic in topics:
        if topic.level not in level_counts:
            raise ValueError(f"Unsupported level: {topic.level}")
        level_counts[topic.level] += 1

        if len(topic.examples) != 3:
            raise ValueError(f"Topic {topic.id} must have exactly 3 examples.")
        if len(topic.quizzes) != 3:
            raise ValueError(f"Topic {topic.id} must have exactly 3 quizzes.")
        if not topic.forms:
            raise ValueError(f"Topic {topic.id} must have at least one form line.")

        for index, quiz in enumerate(topic.quizzes):
            if len(quiz.options) not in {3, 4}:
                raise ValueError(
                    f"Quiz {index} in {topic.id} must have 3 or 4 options."
                )
            if not 0 <= quiz.correct_index < len(quiz.options):
                raise ValueError(f"Invalid correct answer in {topic.id}, quiz {index}.")

    if level_counts != {"C1": 70}:
        raise ValueError("Course must contain exactly 70 C1 topics.")

def get_topic(order: int) -> GrammarTopic:
    topics = load_topics()
    if not 1 <= order <= len(topics):
        raise LookupError(f"Grammar topic order {order} does not exist.")
    return topics[order - 1]

def topics_for_level(level: str) -> tuple[GrammarTopic, ...]:
    normalized = level.upper()
    return tuple(topic for topic in load_topics() if topic.level == normalized)

def next_topic_order(order: int) -> int | None:
    return order + 1 if order < len(load_topics()) else None

def previous_topic_order(order: int) -> int | None:
    return order - 1 if order > 1 else None
