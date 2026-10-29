from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from .schemas import CommonMistake, VerbCard, VerbExample, VerbQuiz

COURSE_ID = "verbs_c1_v1"
COURSE_VERSION = "2026-07-v1"
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILES = (DATA_DIR / "verbs_c1.json",)

@lru_cache(maxsize=1)
def load_cards() -> tuple[VerbCard, ...]:
    raw_items: list[dict] = []
    for path in DATA_FILES:
        with path.open("r", encoding="utf-8") as source:
            raw_items.extend(json.load(source))
    cards = tuple(_parse_card(item) for item in raw_items)
    validate_cards(cards)
    return cards

def _parse_card(item: dict) -> VerbCard:
    mistake = item["common_mistake"]
    quiz = item["quiz"]
    return VerbCard(
        id=item["id"],
        order=item["order"],
        level=item["level"],
        category=item["category"],
        title_en=item["title_en"],
        title_ru=item["title_ru"],
        rule=item["rule"],
        forms=tuple(item["forms"]),
        meanings=tuple(item["meanings"]),
        contrast=item["contrast"],
        examples=tuple(VerbExample(**example) for example in item["examples"]),
        common_mistake=CommonMistake(**mistake),
        quiz=VerbQuiz(
            prompt=quiz["prompt"],
            options=tuple(quiz["options"]),
            correct_index=quiz["correct_index"],
            explanation=quiz["explanation"],
        ),
    )

def validate_cards(cards: tuple[VerbCard, ...]) -> None:
    if len(cards) != 40:
        raise ValueError("C1 verb course must contain exactly 40 cards.")
    if [card.order for card in cards] != list(range(1, 41)):
        raise ValueError("Card orders must be continuous from 1 to 40.")
    ids = [card.id for card in cards]
    if len(ids) != len(set(ids)):
        raise ValueError("Card IDs must be unique.")
    answer_distribution = {0: 0, 1: 0, 2: 0, 3: 0}
    for card in cards:
        if card.level != "C1":
            raise ValueError(f"Unsupported level: {card.level}")
        if len(card.examples) != 3:
            raise ValueError(f"Card {card.id} must have exactly 3 examples.")
        if not card.forms or not card.meanings:
            raise ValueError(f"Card {card.id} must include forms and meanings.")
        if len(card.quiz.options) != 4:
            raise ValueError(f"Card {card.id} quiz must have exactly 4 options.")
        if len(set(card.quiz.options)) != len(card.quiz.options):
            raise ValueError(f"Card {card.id} quiz options must be unique.")
        if not 0 <= card.quiz.correct_index < len(card.quiz.options):
            raise ValueError(f"Invalid correct answer in {card.id}.")
        answer_distribution[card.quiz.correct_index] += 1
    if answer_distribution != {0: 10, 1: 10, 2: 10, 3: 10}:
        raise ValueError("Correct answers must be evenly distributed across A-D.")

def get_card(order: int) -> VerbCard:
    cards = load_cards()
    if not 1 <= order <= len(cards):
        raise LookupError(f"Verb card order {order} does not exist.")
    return cards[order - 1]

def cards_for_level(level: str) -> tuple[VerbCard, ...]:
    normalized = level.upper()
    return tuple(card for card in load_cards() if card.level == normalized)
