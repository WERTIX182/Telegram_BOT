from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class CollocationExample:
    en: str
    ru: str

@dataclass(frozen=True, slots=True)
class CommonMistake:
    wrong: str
    right: str
    note: str

@dataclass(frozen=True, slots=True)
class CollocationQuiz:
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str

@dataclass(frozen=True, slots=True)
class CollocationCard:
    id: str
    order: int
    level: str
    category: str
    phrase: str
    translation: str
    explanation: str
    patterns: tuple[str, ...]
    related: tuple[str, ...]
    examples: tuple[CollocationExample, ...]
    common_mistake: CommonMistake
    quiz: CollocationQuiz

@dataclass(frozen=True, slots=True)
class AnswerResult:
    accepted: bool
    is_correct: bool = False
    is_complete: bool = False
    score: int = 0
