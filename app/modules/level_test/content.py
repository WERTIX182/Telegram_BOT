from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from .schemas import PlacementQuestion

LEVEL_ORDER = ("A1", "A2", "B1", "B2", "C1")
TOTAL_QUESTIONS = 20
QUESTIONS_PATH = Path(__file__).resolve().parent / "data" / "questions.json"

@lru_cache(maxsize=1)
def load_questions() -> tuple[PlacementQuestion, ...]:
    with QUESTIONS_PATH.open("r", encoding="utf-8") as source:
        raw = json.load(source)

    questions = tuple(
        PlacementQuestion(
            id=item["id"],
            order=item["order"],
            level=item["level"],
            skill=item["skill"],
            instruction=item["instruction"],
            prompt=item["prompt"],
            options=tuple(item["options"]),
            correct_index=item["correct_index"],
            explanation=item["explanation"],
        )
        for item in raw
    )
    validate_questions(questions)
    return questions

def validate_questions(questions: tuple[PlacementQuestion, ...]) -> None:
    if len(questions) != TOTAL_QUESTIONS:
        raise ValueError(f"Expected {TOTAL_QUESTIONS} placement questions.")

    ids = [question.id for question in questions]
    orders = [question.order for question in questions]
    prompts = [question.prompt for question in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("Question IDs must be unique.")
    if sorted(orders) != list(range(1, TOTAL_QUESTIONS + 1)):
        raise ValueError("Question orders must be continuous from 1 to 20.")
    if len(prompts) != len(set(prompts)):
        raise ValueError("Question prompts must be unique.")

    level_counts = Counter(question.level for question in questions)
    if level_counts != Counter({level: 4 for level in LEVEL_ORDER}):
        raise ValueError("The test must contain four questions per CEFR band A1-C1.")

    correct_positions = Counter(question.correct_index for question in questions)
    if correct_positions != Counter({0: 5, 1: 5, 2: 5, 3: 5}):
        raise ValueError("Canonical correct positions must be balanced 5/5/5/5.")

    for question in questions:
        if question.level not in LEVEL_ORDER:
            raise ValueError(f"Unsupported level: {question.level}")
        if len(question.options) != 4:
            raise ValueError(f"Question {question.id} must have exactly four options.")
        if len(set(question.options)) != 4:
            raise ValueError(f"Question {question.id} contains duplicate options.")
        if not 0 <= question.correct_index < 4:
            raise ValueError(f"Invalid correct index in {question.id}.")
        if not question.explanation.strip():
            raise ValueError(f"Question {question.id} has no explanation.")

def question_map() -> dict[str, PlacementQuestion]:
    return {question.id: question for question in load_questions()}
