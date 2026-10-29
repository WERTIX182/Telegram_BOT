from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IrregularVerbExample:
    label: str
    en: str
    ru: str


@dataclass(frozen=True, slots=True)
class CommonMistake:
    wrong: str
    right: str
    note: str


@dataclass(frozen=True, slots=True)
class IrregularVerbQuiz:
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str


@dataclass(frozen=True, slots=True)
class IrregularVerbCard:
    id: str
    order: int
    level: str
    pattern: str
    infinitive: str
    past_simple: str
    past_participle: str
    translation: str
    note: str
    examples: tuple[IrregularVerbExample, ...]
    common_mistake: CommonMistake
    quiz: IrregularVerbQuiz


@dataclass(frozen=True, slots=True)
class AnswerResult:
    accepted: bool
    is_correct: bool = False
    is_complete: bool = False
    score: int = 0
