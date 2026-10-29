from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExtraQuestion:
    id: str
    type: str
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str
    source_example_index: int


@dataclass(frozen=True, slots=True)
class ExtraQuestionSet:
    base_card_id: str
    card_order: int
    level_code: str
    level: str
    category: str
    phrasal_verb: str
    translation: str
    questions: tuple[ExtraQuestion, ...]


@dataclass(frozen=True, slots=True)
class AnswerResult:
    accepted: bool
    is_correct: bool = False
    is_complete: bool = False
    next_question_index: int | None = None
    score: int = 0