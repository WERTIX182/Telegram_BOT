from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class IdiomExample:
    en: str
    ru: str

@dataclass(frozen=True, slots=True)
class CommonMistake:
    wrong: str
    right: str
    note: str

@dataclass(frozen=True, slots=True)
class IdiomQuiz:
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str

@dataclass(frozen=True, slots=True)
class IdiomCard:
    id: str
    order: int
    level: str
    category: str
    idiom: str
    translation: str
    explanation: str
    register: str
    literal_image: str
    patterns: tuple[str, ...]
    related: tuple[str, ...]
    examples: tuple[IdiomExample, ...]
    common_mistake: CommonMistake
    quiz: IdiomQuiz

@dataclass(frozen=True, slots=True)
class AnswerResult:
    accepted: bool
    is_correct: bool = False
    is_complete: bool = False
    score: int = 0
