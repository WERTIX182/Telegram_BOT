from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from .schemas import ExtraQuestion, ExtraQuestionSet

COURSE_ID = "collocations_extra_quizzes_v1"
COURSE_VERSION = "2026-07-v1.0"
TOTAL_SETS = 108
QUESTIONS_PER_SET = 2
TOTAL_QUESTIONS = TOTAL_SETS * QUESTIONS_PER_SET
DATA_FILE = Path(__file__).resolve().parent / "data" / "collocations_extra_quizzes.json"

@lru_cache(maxsize=1)
def load_sets() -> tuple[ExtraQuestionSet, ...]:
    with DATA_FILE.open("r", encoding="utf-8") as source:
        raw_items = json.load(source)
    sets = tuple(_parse_set(item) for item in raw_items)
    validate_sets(sets)
    return sets

def _parse_set(item: dict) -> ExtraQuestionSet:
    return ExtraQuestionSet(
        base_card_id=item["base_card_id"],
        card_order=item["card_order"],
        level_code=item["level_code"],
        level=item["level"],
        category=item["category"],
        collocation=item["collocation"],
        translation=item["translation"],
        questions=tuple(ExtraQuestion(
            id=q["id"],
            type=q["type"],
            prompt=q["prompt"],
            options=tuple(q["options"]),
            correct_index=q["correct_index"],
            explanation=q["explanation"],
            source_example_index=q["source_example_index"],
        ) for q in item["questions"]),
    )

def validate_sets(sets: tuple[ExtraQuestionSet, ...]) -> None:
    if len(sets) != TOTAL_SETS:
        raise ValueError(f"Expected {TOTAL_SETS} extra-practice sets, got {len(sets)}.")
    counts = Counter(item.level_code for item in sets)
    if counts != Counter({"i": 54, "a": 54}):
        raise ValueError(f"Expected 54 sets per level, got {counts}.")

    ids, prompts, positions, keys = [], [], [], []
    for item in sets:
        if item.level_code not in {"i", "a"}:
            raise ValueError(f"Unsupported level code in {item.base_card_id}.")
        expected_level = "Intermediate" if item.level_code == "i" else "Advanced"
        if item.level != expected_level:
            raise ValueError(f"Level mismatch in {item.base_card_id}.")
        if not 1 <= item.card_order <= 54:
            raise ValueError(f"Invalid source order in {item.base_card_id}.")
        if len(item.questions) != QUESTIONS_PER_SET:
            raise ValueError(f"{item.base_card_id} must contain exactly two questions.")
        keys.append((item.level_code, item.card_order))
        for q in item.questions:
            if q.type not in {"meaning_to_form", "meaning_in_context"}:
                raise ValueError(f"Unsupported question type: {q.id}")
            if len(q.options) != 4 or len(set(q.options)) != 4:
                raise ValueError(f"{q.id} must have four unique options.")
            if not 0 <= q.correct_index < 4:
                raise ValueError(f"Invalid correct index in {q.id}.")
            correct = q.options[q.correct_index]
            if correct.casefold() in q.prompt.casefold():
                raise ValueError(f"Correct option is leaked in prompt: {q.id}")
            if not q.explanation.strip():
                raise ValueError(f"Missing explanation in {q.id}.")
            ids.append(q.id); prompts.append(q.prompt.strip()); positions.append(q.correct_index)
    if len(set(keys)) != TOTAL_SETS:
        raise ValueError("Source level/order keys must be unique.")
    if len(set(ids)) != TOTAL_QUESTIONS:
        raise ValueError("Question IDs must be unique.")
    if len(set(prompts)) != TOTAL_QUESTIONS:
        raise ValueError("Question prompts must be unique.")
    if Counter(positions) != Counter({0: 54, 1: 54, 2: 54, 3: 54}):
        raise ValueError(f"Correct-answer positions are unbalanced: {Counter(positions)}")

def get_set(level_code: str, card_order: int) -> ExtraQuestionSet:
    normalized = level_code.lower()
    for item in load_sets():
        if item.level_code == normalized and item.card_order == card_order:
            return item
    raise LookupError(f"Extra collocation practice not found: {level_code}/{card_order}")
