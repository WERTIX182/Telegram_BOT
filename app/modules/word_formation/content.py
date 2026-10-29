from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from .schemas import (
    CommonMistake,
    WordForm,
    WordFormationCard,
    WordFormationExample,
    WordFormationQuiz,
)

COURSE_ID = "word_formation_v1"
COURSE_VERSION = "2026-07-v1.1"
TOTAL_CARDS = 56
DATA_FILE = Path(__file__).resolve().parent / "data" / "word_formation.json"
SUPPORTED_CATEGORIES = (
    "FOUNDATIONS",
    "NOUNS",
    "ADJECTIVES",
    "VERBS",
    "ADVERBS",
    "PREFIXES",
    "SPELLING_IRREGULAR",
)
SUPPORTED_LEVELS = ("A2", "B1", "B2", "C1")

@lru_cache(maxsize=1)
def load_cards() -> tuple[WordFormationCard, ...]:
    with DATA_FILE.open("r", encoding="utf-8") as source:
        raw_items = json.load(source)
    cards = tuple(_parse_card(item) for item in raw_items)
    validate_cards(cards)
    return cards

def _parse_card(item: dict) -> WordFormationCard:
    mistake = item["common_mistake"]
    quiz = item["quiz"]
    return WordFormationCard(
        id=item["id"],
        order=item["order"],
        level=item["level"],
        category=item["category"],
        title=item["title"],
        base_word=item["base_word"],
        focus=item["focus"],
        rule=item["rule"],
        forms=tuple(WordForm(**form) for form in item["forms"]),
        spelling_note=item["spelling_note"],
        examples=tuple(WordFormationExample(**example) for example in item["examples"]),
        common_mistake=CommonMistake(**mistake),
        quiz=WordFormationQuiz(
            prompt=quiz["prompt"],
            options=tuple(quiz["options"]),
            correct_index=quiz["correct_index"],
            answer=quiz["answer"],
            explanation=quiz["explanation"],
        ),
    )

def validate_cards(cards: tuple[WordFormationCard, ...]) -> None:
    if len(cards) != TOTAL_CARDS:
        raise ValueError(f"Word formation course must contain exactly {TOTAL_CARDS} cards.")
    if [card.order for card in cards] != list(range(1, TOTAL_CARDS + 1)):
        raise ValueError(f"Card orders must be continuous from 1 to {TOTAL_CARDS}.")
    if len({card.id for card in cards}) != TOTAL_CARDS:
        raise ValueError("Card IDs must be unique.")
    if len({card.title.casefold() for card in cards}) != TOTAL_CARDS:
        raise ValueError("Card titles must be unique.")
    if len({card.base_word.casefold() for card in cards}) != TOTAL_CARDS:
        raise ValueError("Base-word labels must be unique.")

    category_counts = Counter(card.category for card in cards)
    expected_categories = Counter({category: 8 for category in SUPPORTED_CATEGORIES})
    if category_counts != expected_categories:
        raise ValueError(f"Each category must contain eight cards: {category_counts}")

    prompts: list[str] = []
    positions: list[int] = []
    examples: list[str] = []
    for card in cards:
        if card.level not in SUPPORTED_LEVELS:
            raise ValueError(f"Unsupported level in {card.id}: {card.level}")
        if card.category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported category in {card.id}: {card.category}")
        if len(card.forms) != 4:
            raise ValueError(f"Card {card.id} must contain exactly four word forms.")
        if len(card.examples) != 2:
            raise ValueError(f"Card {card.id} must contain exactly two examples.")
        if len({form.form.casefold() for form in card.forms}) != len(card.forms):
            raise ValueError(f"Card {card.id} contains duplicate word forms.")
        if not all(
            (
                card.title,
                card.base_word,
                card.focus,
                card.rule,
                card.spelling_note,
                card.common_mistake.wrong,
                card.common_mistake.right,
                card.common_mistake.note,
            )
        ):
            raise ValueError(f"Card {card.id} contains an empty required field.")
        if any(not all((form.form, form.word_class, form.translation)) for form in card.forms):
            raise ValueError(f"Card {card.id} contains an incomplete word-family entry.")
        if len(card.quiz.options) != 4 or len(set(card.quiz.options)) != 4:
            raise ValueError(f"Quiz in {card.id} must have four unique options.")
        if not 0 <= card.quiz.correct_index < 4:
            raise ValueError(f"Invalid correct answer in {card.id}.")
        if card.quiz.options[card.quiz.correct_index] != card.quiz.answer:
            raise ValueError(f"Correct answer mismatch in {card.id}.")
        if not card.quiz.explanation.strip():
            raise ValueError(f"Quiz explanation is empty in {card.id}.")
        prompts.append(card.quiz.prompt.strip())
        positions.append(card.quiz.correct_index)
        examples.extend(example.en.strip() for example in card.examples)

    if len(set(prompts)) != len(prompts):
        raise ValueError("Quiz prompts must be unique.")
    if len(set(examples)) != len(examples):
        raise ValueError("English examples must be unique.")
    distribution = Counter(positions)
    if distribution != Counter({0: 14, 1: 14, 2: 14, 3: 14}):
        raise ValueError(f"Correct-answer positions are unbalanced: {distribution}")

def get_card(order: int) -> WordFormationCard:
    cards = load_cards()
    if not 1 <= order <= len(cards):
        raise LookupError(f"Word-formation card order {order} does not exist.")
    return cards[order - 1]

def cards_for_category(category: str) -> tuple[WordFormationCard, ...]:
    normalized = category.upper()
    return tuple(card for card in load_cards() if card.category == normalized)

def cards_for_level(level: str) -> tuple[WordFormationCard, ...]:
    normalized = level.upper()
    return tuple(card for card in load_cards() if card.level == normalized)
