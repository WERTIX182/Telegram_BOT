from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class WordForm:
    form: str
    word_class: str
    translation: str

@dataclass(frozen=True, slots=True)
class WordFormationExample:
    en: str
    ru: str

@dataclass(frozen=True, slots=True)
class CommonMistake:
    wrong: str
    right: str
    note: str

@dataclass(frozen=True, slots=True)
class WordFormationQuiz:
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    answer: str
    explanation: str

@dataclass(frozen=True, slots=True)
class WordFormationCard:
    id: str
    order: int
    level: str
    category: str
    title: str
    base_word: str
    focus: str
    rule: str
    forms: tuple[WordForm, ...]
    spelling_note: str
    examples: tuple[WordFormationExample, ...]
    common_mistake: CommonMistake
    quiz: WordFormationQuiz

@dataclass(frozen=True, slots=True)
class AnswerResult:
    accepted: bool
    is_correct: bool = False
    is_complete: bool = False
    score: int = 0
