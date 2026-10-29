from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from .schemas import CommonMistake, IrregularVerbCard, IrregularVerbExample, IrregularVerbQuiz


COURSE_ID = "irregular_verbs_v1"
COURSE_VERSION = "2026-07-v1"
TOTAL_CARDS = 100
DATA_FILE = Path(__file__).resolve().parent / "data" / "irregular_verbs.json"
SUPPORTED_LEVELS = ("A1-A2", "B1", "B2-C1")
SUPPORTED_PATTERNS = ("AAA", "ABB", "ABA", "ABC", "SPECIAL")


@lru_cache(maxsize=1)
def load_cards() -> tuple[IrregularVerbCard, ...]:
    with DATA_FILE.open("r", encoding="utf-8") as source:
        raw_items = json.load(source)
    cards = tuple(_parse_card(item) for item in raw_items)
    validate_cards(cards)
    return cards


def _parse_card(item: dict) -> IrregularVerbCard:
    mistake = item["common_mistake"]
    quiz = item["quiz"]
    return IrregularVerbCard(
        id=item["id"],
        order=item["order"],
        level=item["level"],
        pattern=item["pattern"],
        infinitive=item["infinitive"],
        past_simple=item["past_simple"],
        past_participle=item["past_participle"],
        translation=item["translation"],
        note=item["note"],
        examples=tuple(IrregularVerbExample(**example) for example in item["examples"]),
        common_mistake=CommonMistake(**mistake),
        quiz=IrregularVerbQuiz(
            prompt=quiz["prompt"],
            options=tuple(quiz["options"]),
            correct_index=quiz["correct_index"],
            explanation=quiz["explanation"],
        ),
    )


def validate_cards(cards: tuple[IrregularVerbCard, ...]) -> None:
    if len(cards) != TOTAL_CARDS:
        raise ValueError(f"Irregular verb course must contain exactly {TOTAL_CARDS} cards.")
    if [card.order for card in cards] != list(range(1, TOTAL_CARDS + 1)):
        raise ValueError("Card orders must be continuous from 1 to 100.")
    if len({card.id for card in cards}) != TOTAL_CARDS:
        raise ValueError("Card IDs must be unique.")
    if len({card.infinitive for card in cards}) != TOTAL_CARDS:
        raise ValueError("Infinitives must be unique.")
    distribution = Counter(card.quiz.correct_index for card in cards)
    if distribution != Counter({0: 25, 1: 25, 2: 25, 3: 25}):
        raise ValueError("Canonical correct-answer positions must be evenly distributed.")
    for card in cards:
        if card.level not in SUPPORTED_LEVELS:
            raise ValueError(f"Unsupported level: {card.level}")
        if card.pattern not in SUPPORTED_PATTERNS:
            raise ValueError(f"Unsupported pattern: {card.pattern}")
        if len(card.examples) != 2:
            raise ValueError(f"Card {card.id} must have exactly two examples.")
        if len(card.quiz.options) != 4 or len(set(card.quiz.options)) != 4:
            raise ValueError(f"Card {card.id} must have four unique quiz options.")
        if not 0 <= card.quiz.correct_index < 4:
            raise ValueError(f"Invalid correct answer in {card.id}.")
        if not all((card.infinitive, card.past_simple, card.past_participle, card.translation, card.note)):
            raise ValueError(f"Card {card.id} contains an empty required field.")


def get_card(order: int) -> IrregularVerbCard:
    cards = load_cards()
    if not 1 <= order <= len(cards):
        raise LookupError(f"Irregular verb card order {order} does not exist.")
    return cards[order - 1]


def cards_for_level(level: str) -> tuple[IrregularVerbCard, ...]:
    return tuple(card for card in load_cards() if card.level == level.upper())


def cards_for_pattern(pattern: str) -> tuple[IrregularVerbCard, ...]:
    return tuple(card for card in load_cards() if card.pattern == pattern.upper())
