from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class PlacementQuestion:
    id: str
    order: int
    level: str
    skill: str
    instruction: str
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str

@dataclass(frozen=True, slots=True)
class PlacementLayout:
    question_ids: tuple[str, ...]
    option_orders: dict[str, tuple[int, ...]]

@dataclass(frozen=True, slots=True)
class PlacementResult:
    level: str
    raw_candidate: str
    score: int
    total: int
    band_scores: dict[str, int]
    is_borderline: bool
    confidence: str
    recommended_start_level: str
    recommendation: str
    ceiling_reached: bool

@dataclass(frozen=True, slots=True)
class AnswerOutcome:
    accepted: bool
    next_position: int | None = None
    result: PlacementResult | None = None
