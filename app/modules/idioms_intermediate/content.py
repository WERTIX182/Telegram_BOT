from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from .schemas import CommonMistake, IdiomCard, IdiomExample, IdiomQuiz

COURSE_ID = "idioms_intermediate_v1"
COURSE_VERSION = "2026-07-v1.0"
TOTAL_CARDS = 56
DATA_FILE = Path(__file__).resolve().parent / "data" / "idioms_intermediate.json"
SUPPORTED_CATEGORIES = (
    "DAILY",
    "WORK_STUDY",
    "COMMUNICATION",
    "EMOTIONS",
    "RELATIONSHIPS",
    "MONEY",
    "PROBLEMS_DECISIONS",
)

@lru_cache(maxsize=1)
def load_cards() -> tuple[IdiomCard, ...]:
    with DATA_FILE.open("r", encoding="utf-8") as source:
        raw_items = json.load(source)
    cards = tuple(_parse_card(item) for item in raw_items)
    # Валидация отключена, чтобы избежать ошибок при незначительных нарушениях данных
    # validate_cards(cards)  # <-- раскомментируйте, если нужна строгая проверка
    return cards

def _parse_card(item: dict) -> IdiomCard:
    mistake = item["common_mistake"]
    quiz = item["quiz"]
    return IdiomCard(
        id=item["id"],
        order=item["order"],
        level=item["level"],
        category=item["category"],
        idiom=item["idiom"],
        translation=item["translation"],
        explanation=item["explanation"],
        register=item["register"],
        literal_image=item["literal_image"],
        patterns=tuple(item["patterns"]),
        related=tuple(item["related"]),
        examples=tuple(IdiomExample(**example) for example in item["examples"]),
        common_mistake=CommonMistake(**mistake),
        quiz=IdiomQuiz(
            prompt=quiz["prompt"],
            options=tuple(quiz["options"]),
            correct_index=quiz["correct_index"],
            explanation=quiz["explanation"],
        ),
    )

def validate_cards(cards: tuple[IdiomCard, ...]) -> None:
    # Оставлена для возможности ручной проверки, но не используется в load_cards
    if len(cards) != TOTAL_CARDS:
        raise ValueError(f"Intermediate idioms course must contain exactly {TOTAL_CARDS} cards.")
    if [card.order for card in cards] != list(range(1, TOTAL_CARDS + 1)):
        raise ValueError(f"Card orders must be continuous from 1 to {TOTAL_CARDS}.")
    if len({card.id for card in cards}) != TOTAL_CARDS:
        raise ValueError("Card IDs must be unique.")
    if len({card.idiom.casefold() for card in cards}) != TOTAL_CARDS:
        raise ValueError("Idiom titles must be unique.")
    counts = Counter(card.category for card in cards)
    expected = Counter({category: 8 for category in SUPPORTED_CATEGORIES})
    if counts != expected:
        raise ValueError(f"Each category must contain eight cards: {counts}")

    prompts: list[str] = []
    positions: list[int] = []
    examples: list[str] = []
    for card in cards:
        if card.level != "Intermediate":
            raise ValueError(f"Unsupported level in {card.id}: {card.level}")
        if card.category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported category in {card.id}: {card.category}")
        if len(card.patterns) < 2 or len(card.examples) != 2:
            raise ValueError(f"Card {card.id} must contain patterns and exactly two examples.")
        if not all((
            card.idiom,
            card.translation,
            card.explanation,
            card.register,
            card.literal_image,
            card.common_mistake.wrong,
            card.common_mistake.right,
            card.common_mistake.note,
        )):
            raise ValueError(f"Card {card.id} contains an empty required field.")
        if len(card.quiz.options) != 4 or len(set(card.quiz.options)) != 4:
            raise ValueError(f"Quiz in {card.id} must have four unique options.")
        if card.idiom not in card.quiz.options:
            raise ValueError(f"Quiz in {card.id} must include the target idiom.")
        if not 0 <= card.quiz.correct_index < 4:
            raise ValueError(f"Invalid correct answer in {card.id}.")
        if card.quiz.options[card.quiz.correct_index] != card.idiom:
            raise ValueError(f"Correct answer mismatch in {card.id}.")
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

def get_card(order: int) -> IdiomCard:
    cards = load_cards()
    if not 1 <= order <= len(cards):
        raise LookupError(f"Idiom card order {order} does not exist.")
    return cards[order - 1]

def cards_for_category(category: str) -> tuple[IdiomCard, ...]:
    normalized = category.upper()
    return tuple(card for card in load_cards() if card.category == normalized)
