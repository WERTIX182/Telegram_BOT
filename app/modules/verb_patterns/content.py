from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from .schemas import CommonMistake, PatternExample, PatternQuiz, VerbPatternTopic

COURSE_ID = "verb_patterns_v1"
COURSE_VERSION = "2026-07-v1.1"
TOTAL_TOPICS = 35
QUIZZES_PER_TOPIC = 2
DATA_FILE = Path(__file__).resolve().parent / "data" / "verb_patterns.json"
SUPPORTED_LEVELS = ("A2-B1", "B1-B2", "B2-C1")
SUPPORTED_CATEGORIES = ("CORE", "MEANING", "COMPLEX", "ADVANCED")


@lru_cache(maxsize=1)
def load_topics() -> tuple[VerbPatternTopic, ...]:
    with DATA_FILE.open("r", encoding="utf-8") as source:
        raw_items = json.load(source)
    topics = tuple(_parse_topic(item) for item in raw_items)
    validate_topics(topics)
    return topics


def _parse_topic(item: dict) -> VerbPatternTopic:
    mistake = item["common_mistake"]
    return VerbPatternTopic(
        id=item["id"], order=item["order"], level=item["level"], category=item["category"],
        title_en=item["title_en"], title_ru=item["title_ru"], rule=item["rule"],
        patterns=tuple(item["patterns"]),
        examples=tuple(PatternExample(**example) for example in item["examples"]),
        common_mistake=CommonMistake(**mistake),
        quizzes=tuple(PatternQuiz(prompt=q["prompt"], options=tuple(q["options"]), correct_index=q["correct_index"], explanation=q["explanation"]) for q in item["quizzes"]),
    )


def validate_topics(topics: tuple[VerbPatternTopic, ...]) -> None:
    if len(topics) != TOTAL_TOPICS:
        raise ValueError(f"Verb-pattern course must contain exactly {TOTAL_TOPICS} topics.")
    if [topic.order for topic in topics] != list(range(1, TOTAL_TOPICS + 1)):
        raise ValueError("Topic orders must be continuous from 1 to 35.")
    if len({topic.id for topic in topics}) != TOTAL_TOPICS:
        raise ValueError("Topic IDs must be unique.")
    if len({topic.title_en for topic in topics}) != TOTAL_TOPICS:
        raise ValueError("English titles must be unique.")
    prompts = []
    positions = []
    for topic in topics:
        if topic.level not in SUPPORTED_LEVELS:
            raise ValueError(f"Unsupported level: {topic.level}")
        if topic.category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported category: {topic.category}")
        if len(topic.patterns) < 1:
            raise ValueError(f"Topic {topic.id} must contain at least one pattern.")
        if len(topic.examples) != 3:
            raise ValueError(f"Topic {topic.id} must have exactly three examples.")
        if len(topic.quizzes) != QUIZZES_PER_TOPIC:
            raise ValueError(f"Topic {topic.id} must have exactly two quizzes.")
        if not all((topic.rule, topic.common_mistake.wrong, topic.common_mistake.right, topic.common_mistake.note)):
            raise ValueError(f"Topic {topic.id} contains an empty required field.")
        for quiz in topic.quizzes:
            if len(quiz.options) != 4 or len(set(quiz.options)) != 4:
                raise ValueError(f"Each quiz in {topic.id} must have four unique options.")
            if not 0 <= quiz.correct_index < 4:
                raise ValueError(f"Invalid correct answer in {topic.id}.")
            if not quiz.prompt.strip() or not quiz.explanation.strip():
                raise ValueError(f"Quiz text is incomplete in {topic.id}.")
            prompts.append(quiz.prompt.strip())
            positions.append(quiz.correct_index)
    if len(set(prompts)) != len(prompts):
        raise ValueError("Quiz prompts must be unique.")
    distribution = Counter(positions)
    if max(distribution.values()) - min(distribution.values()) > 1:
        raise ValueError(f"Correct-answer positions are unbalanced: {distribution}")


def get_topic(order: int) -> VerbPatternTopic:
    topics = load_topics()
    if not 1 <= order <= len(topics):
        raise LookupError(f"Verb-pattern topic order {order} does not exist.")
    return topics[order - 1]


def topics_for_level(level: str) -> tuple[VerbPatternTopic, ...]:
    return tuple(topic for topic in load_topics() if topic.level == level.upper())


def topics_for_category(category: str) -> tuple[VerbPatternTopic, ...]:
    return tuple(topic for topic in load_topics() if topic.category == category.upper())
