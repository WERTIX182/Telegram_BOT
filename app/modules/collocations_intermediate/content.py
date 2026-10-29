from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from .schemas import CollocationCard, CollocationExample, CollocationQuiz, CommonMistake

COURSE_ID = "collocations_intermediate_v1"
COURSE_VERSION = "2026-07-v1"
TOTAL_CARDS = 54
DATA_FILE = Path(__file__).resolve().parent / "data" / "collocations_intermediate.json"
SUPPORTED_CATEGORIES = ("WORK", "EDUCATION", "TRAVEL", "COMMUNICATION", "EMOTIONS", "RELATIONSHIPS", "HEALTH", "TECHNOLOGY", "EVERYDAY")

@lru_cache(maxsize=1)
def load_cards() -> tuple[CollocationCard, ...]:
    with DATA_FILE.open("r", encoding="utf-8") as source:
        raw_items = json.load(source)
    cards = tuple(_parse_card(item) for item in raw_items)
    validate_cards(cards)
    return cards

def _parse_card(item: dict) -> CollocationCard:
    mistake = item["common_mistake"]
    quiz = item["quiz"]
    return CollocationCard(
        id=item["id"], order=item["order"], level=item["level"], category=item["category"],
        phrase=item["phrase"], translation=item["translation"], explanation=item["explanation"],
        patterns=tuple(item["patterns"]), related=tuple(item["related"]),
        examples=tuple(CollocationExample(**example) for example in item["examples"]),
        common_mistake=CommonMistake(**mistake),
        quiz=CollocationQuiz(prompt=quiz["prompt"], options=tuple(quiz["options"]),
                             correct_index=quiz["correct_index"], explanation=quiz["explanation"]),
    )

def validate_cards(cards: tuple[CollocationCard, ...]) -> None:
    if len(cards) != TOTAL_CARDS:
        raise ValueError(f"Intermediate collocations course must contain exactly {TOTAL_CARDS} cards.")
    if [card.order for card in cards] != list(range(1, TOTAL_CARDS + 1)):
        raise ValueError("Card orders must be continuous from 1 to 54.")
    if len({card.id for card in cards}) != TOTAL_CARDS:
        raise ValueError("Card IDs must be unique.")
    if len({card.phrase for card in cards}) != TOTAL_CARDS:
        raise ValueError("Collocation phrases must be unique.")
    counts = Counter(card.category for card in cards)
    if counts != Counter({category: 6 for category in SUPPORTED_CATEGORIES}):
        raise ValueError(f"Each category must contain six cards: {counts}")
    prompts, positions, examples = [], [], []
    for card in cards:
        if card.level != "Intermediate":
            raise ValueError(f"Unsupported level in {card.id}: {card.level}")
        if card.category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported category in {card.id}: {card.category}")
        if len(card.patterns) < 2 or len(card.examples) != 3:
            raise ValueError(f"Card {card.id} must contain patterns and exactly three examples.")
        if not all((card.explanation, card.translation, card.common_mistake.wrong,
                    card.common_mistake.right, card.common_mistake.note)):
            raise ValueError(f"Card {card.id} contains an empty required field.")
        if len(card.quiz.options) != 4 or len(set(card.quiz.options)) != 4:
            raise ValueError(f"Quiz in {card.id} must have four unique options.")
        if not 0 <= card.quiz.correct_index < 4:
            raise ValueError(f"Invalid correct answer in {card.id}.")
        prompts.append(card.quiz.prompt.strip())
        positions.append(card.quiz.correct_index)
        examples.extend(example.en.strip() for example in card.examples)
    if len(set(prompts)) != len(prompts):
        raise ValueError("Quiz prompts must be unique.")
    if len(set(examples)) != len(examples):
        raise ValueError("English examples must be unique.")
    distribution = Counter(positions)
    if max(distribution.values()) - min(distribution.values()) > 1:
        raise ValueError(f"Correct-answer positions are unbalanced: {distribution}")

def get_card(order: int) -> CollocationCard:
    cards = load_cards()
    if not 1 <= order <= len(cards):
        raise LookupError(f"Collocation card order {order} does not exist.")
    return cards[order - 1]

def cards_for_category(category: str) -> tuple[CollocationCard, ...]:
    normalized = category.upper()
    return tuple(card for card in load_cards() if card.category == normalized)
