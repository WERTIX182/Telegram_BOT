from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class PatternExample:
    en: str
    ru: str

@dataclass(frozen=True, slots=True)
class CommonMistake:
    wrong: str
    right: str
    note: str

@dataclass(frozen=True, slots=True)
class PatternQuiz:
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str

@dataclass(frozen=True, slots=True)
class ModalVerbTopic:
    id: str
    order: int
    level: str
    category: str
    title_en: str
    title_ru: str
    rule: str
    patterns: tuple[str, ...]
    examples: tuple[PatternExample, ...]
    common_mistake: CommonMistake
    quizzes: tuple[PatternQuiz, ...]

@dataclass(frozen=True, slots=True)
class AnswerResult:
    accepted: bool
    is_correct: bool = False
    is_complete: bool = False
    score: int = 0
    next_quiz_index: int = 0
