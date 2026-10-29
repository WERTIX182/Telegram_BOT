from __future__ import annotations

import json
import random
from typing import Iterable

from .content import LEVEL_ORDER, load_questions, question_map
from .schemas import PlacementLayout, PlacementQuestion, PlacementResult

TEST_VERSION = "2026-07-level-placement-v1.0"
RAW_THRESHOLDS = {"A1": 0, "A2": 5, "B1": 9, "B2": 13, "C1": 17}
FOUNDATION_MINIMUMS = {"A2": 2, "B1": 4, "B2": 6, "C1": 9}

RESULT_DESCRIPTIONS = {
    "A1": "В заданиях теста вы уверенно распознаёте часть самых базовых слов и конструкций.",
    "A2": "В заданиях теста вы справляетесь с базовой грамматикой и простыми повседневными сообщениями.",
    "B1": "В заданиях теста вы понимаете основную мысль текстов на знакомые темы и владеете ключевыми моделями среднего уровня.",
    "B2": "В заданиях теста вы справляетесь с достаточно сложной грамматикой, коллокациями и смысловыми выводами из текста.",
    "C1": "В заданиях теста вы распознаёте сложные грамматические модели, точную лексику и тонкие смысловые отношения.",
}

STABLE_RECOMMENDATIONS = {
    "A1": ("A1", "Начните с блока A1 в разделе «Грамматика A1–A2» и базовых глаголов A1–A2."),
    "A2": ("A2", "Начните с блока A2 в разделе «Грамматика A1–A2», затем переходите к материалам B1."),
    "B1": ("B1", "Начните с блока B1 в разделе «Грамматика B1–B2» и подключите лексику Intermediate."),
    "B2": ("B2", "Начните с блока B2 в разделе «Грамматика B1–B2», затем добавьте Advanced-лексику."),
    "C1": ("C1", "Начните с раздела «Грамматика C1» и продвинутых модулей лексики."),
}

BORDERLINE_RECOMMENDATIONS = {
    "A1": ("A1", "Начните с первых тем A1 и двигайтесь последовательно, не пропуская базовые конструкции."),
    "A2": ("A1", "Сначала быстро повторите основные темы A1, затем переходите к блоку A2."),
    "B1": ("A2", "Начните с заключительных тем A2 и после короткого повторения переходите к B1."),
    "B2": ("B1", "Начните с верхней части B1, затем переходите к блоку B2."),
    "C1": ("B2", "Начните с повторения ключевых тем B2, затем переходите к C1."),
}

def make_layout(seed: int | None = None) -> PlacementLayout:
    rng = random.Random(seed)
    questions = load_questions()
    question_ids: list[str] = []
    option_orders: dict[str, tuple[int, ...]] = {}

    for level in LEVEL_ORDER:
        band = [question for question in questions if question.level == level]
        rng.shuffle(band)
        question_ids.extend(question.id for question in band)

    for question in questions:
        order = list(range(len(question.options)))
        rng.shuffle(order)
        option_orders[question.id] = tuple(order)

    return PlacementLayout(tuple(question_ids), option_orders)

def dump_layout(layout: PlacementLayout) -> tuple[str, str]:
    return (
        json.dumps(list(layout.question_ids), ensure_ascii=False),
        json.dumps({key: list(value) for key, value in layout.option_orders.items()}, ensure_ascii=False),
    )

def load_layout(question_order_json: str, option_orders_json: str) -> PlacementLayout:
    question_ids = tuple(json.loads(question_order_json))
    raw_options = json.loads(option_orders_json)
    layout = PlacementLayout(
        question_ids=question_ids,
        option_orders={key: tuple(value) for key, value in raw_options.items()},
    )
    validate_layout(layout)
    return layout

def validate_layout(layout: PlacementLayout) -> None:
    questions = question_map()
    if len(layout.question_ids) != len(questions):
        raise ValueError("Invalid question count in stored placement-test layout.")
    if set(layout.question_ids) != set(questions):
        raise ValueError("Stored question IDs do not match the current test version.")
    for question_id, question in questions.items():
        order = layout.option_orders.get(question_id)
        if order is None or sorted(order) != list(range(len(question.options))):
            raise ValueError(f"Invalid option order for {question_id}.")

    levels = [questions[question_id].level for question_id in layout.question_ids]
    if levels != sorted(levels, key=LEVEL_ORDER.index):
        raise ValueError("Question bands must remain in ascending CEFR order.")

def question_at(layout: PlacementLayout, position: int) -> PlacementQuestion:
    if not 0 <= position < len(layout.question_ids):
        raise IndexError("Placement-test position is out of range.")
    return question_map()[layout.question_ids[position]]

def display_options(layout: PlacementLayout, question: PlacementQuestion) -> tuple[str, ...]:
    return tuple(question.options[index] for index in layout.option_orders[question.id])

def canonical_index_for_display(
    layout: PlacementLayout,
    question: PlacementQuestion,
    display_position: int,
) -> int:
    order = layout.option_orders[question.id]
    if not 0 <= display_position < len(order):
        raise IndexError("Displayed answer position is out of range.")
    return order[display_position]

def _raw_candidate(score: int) -> str:
    for level in reversed(LEVEL_ORDER):
        if score >= RAW_THRESHOLDS[level]:
            return level
    return "A1"

def _foundation_score(level: str, band_scores: dict[str, int]) -> int:
    index = LEVEL_ORDER.index(level)
    return sum(band_scores[item] for item in LEVEL_ORDER[:index])

def previous_level(level: str) -> str:
    index = LEVEL_ORDER.index(level)
    return LEVEL_ORDER[max(0, index - 1)]

def evaluate_level(correct_question_ids: Iterable[str]) -> PlacementResult:
    questions = load_questions()
    correct_ids = set(correct_question_ids)
    valid_ids = {question.id for question in questions}
    if not correct_ids <= valid_ids:
        raise ValueError("Unknown question ID supplied to placement scoring.")

    band_scores = {level: 0 for level in LEVEL_ORDER}
    for question in questions:
        if question.id in correct_ids:
            band_scores[question.level] += 1

    score = sum(band_scores.values())
    raw_candidate = _raw_candidate(score)
    level = raw_candidate

    while level != "A1":
        band_confirmed = band_scores[level] >= 2
        foundation_confirmed = _foundation_score(level, band_scores) >= FOUNDATION_MINIMUMS[level]
        if band_confirmed and foundation_confirmed:
            break
        level = previous_level(level)

    lower_boundary = RAW_THRESHOLDS[level]
    downgraded = level != raw_candidate
    is_borderline = (
        downgraded
        or (level != "A1" and score <= lower_boundary + 1)
        or (level != "A1" and band_scores[level] == 2)
    )
    confidence = "borderline" if is_borderline else "stable"
    recommendation_source = BORDERLINE_RECOMMENDATIONS if is_borderline else STABLE_RECOMMENDATIONS
    start_level, recommendation = recommendation_source[level]

    return PlacementResult(
        level=level,
        raw_candidate=raw_candidate,
        score=score,
        total=len(questions),
        band_scores=band_scores,
        is_borderline=is_borderline,
        confidence=confidence,
        recommended_start_level=start_level,
        recommendation=recommendation,
        ceiling_reached=(level == "C1" and score >= 19),
    )

def result_description(level: str) -> str:
    return RESULT_DESCRIPTIONS[level]

def band_profile_text(band_scores: dict[str, int]) -> str:
    return " • ".join(f"{level}: {band_scores[level]}/4" for level in LEVEL_ORDER)
