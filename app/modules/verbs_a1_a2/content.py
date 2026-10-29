from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from .schemas import CommonMistake, VerbCard, VerbExample, VerbQuiz

COURSE_ID = "verbs_a1_a2_v1"
COURSE_VERSION = "2026-07-v1"
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILES = (DATA_DIR / "verbs_a1.json", DATA_DIR / "verbs_a2.json")

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
    if len(cards) != 50:
        raise ValueError("A1-A2 verb course must contain exactly 50 cards.")
    if [card.order for card in cards] != list(range(1, 51)):
        raise ValueError("Card orders must be continuous from 1 to 50.")
    ids = [card.id for card in cards]
    if len(ids) != len(set(ids)):
        raise ValueError("Card IDs must be unique.")
    counts = {"A1": 0, "A2": 0}
    for card in cards:
        if card.level not in counts:
            raise ValueError(f"Unsupported level: {card.level}")
        counts[card.level] += 1
        if len(card.examples) != 3:
            raise ValueError(f"Card {card.id} must have exactly 3 examples.")
        if not card.forms or not card.meanings:
            raise ValueError(f"Card {card.id} must include forms and meanings.")
        if len(card.quiz.options) not in {3, 4}:
            raise ValueError(f"Card {card.id} quiz must have 3 or 4 options.")
        if not 0 <= card.quiz.correct_index < len(card.quiz.options):
            raise ValueError(f"Invalid correct answer in {card.id}.")
    if counts != {"A1": 25, "A2": 25}:
        raise ValueError("Course must contain 25 A1 and 25 A2 cards.")

def get_card(order: int) -> VerbCard:
    cards = load_cards()
    if not 1 <= order <= len(cards):
        raise LookupError(f"Verb card order {order} does not exist.")
    return cards[order - 1]

def cards_for_level(level: str) -> tuple[VerbCard, ...]:
    normalized = level.upper()
    return tuple(card for card in load_cards() if card.level == normalized)
