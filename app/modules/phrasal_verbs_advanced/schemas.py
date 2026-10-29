from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class PhrasalVerbExample:
    en: str
    ru: str

@dataclass(frozen=True, slots=True)
class CommonMistake:
    wrong: str
    right: str
    note: str

@dataclass(frozen=True, slots=True)
class PhrasalVerbQuiz:
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str

@dataclass(frozen=True, slots=True)
class PhrasalVerbCard:
    id: str
    order: int
    level: str
    category: str
    phrase: str
    translation: str
    explanation: str
    patterns: tuple[str, ...]
    related: tuple[str, ...]
    examples: tuple[PhrasalVerbExample, ...]
    common_mistake: CommonMistake
    quiz: PhrasalVerbQuiz

@dataclass(frozen=True, slots=True)
class AnswerResult:
    accepted: bool
    is_correct: bool = False
    is_complete: bool = False
    score: int = 0
