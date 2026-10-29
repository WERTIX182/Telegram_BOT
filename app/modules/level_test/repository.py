from __future__ import annotations

from datetime import datetime, timezone
import json
import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import PlacementTestAnswer, PlacementTestAttempt
from .schemas import AnswerOutcome
from .service import (
    TEST_VERSION,
    canonical_index_for_display,
    dump_layout,
    evaluate_level,
    load_layout,
    make_layout,
    question_at,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def get_active_attempt(session: AsyncSession, user_id: int) -> PlacementTestAttempt | None:
    return await session.scalar(
        select(PlacementTestAttempt)
        .where(
            PlacementTestAttempt.user_id == user_id,
            PlacementTestAttempt.status == "in_progress",
        )
        .order_by(PlacementTestAttempt.started_at.desc())
        .limit(1)
    )

async def get_latest_completed_attempt(session: AsyncSession, user_id: int) -> PlacementTestAttempt | None:
    return await session.scalar(
        select(PlacementTestAttempt)
        .where(
            PlacementTestAttempt.user_id == user_id,
            PlacementTestAttempt.status == "completed",
        )
        .order_by(PlacementTestAttempt.completed_at.desc())
        .limit(1)
    )

async def create_attempt(session: AsyncSession, user_id: int) -> PlacementTestAttempt:
    active = (await session.scalars(
        select(PlacementTestAttempt).where(
            PlacementTestAttempt.user_id == user_id,
            PlacementTestAttempt.status == "in_progress",
        )
    )).all()
    for attempt in active:
        attempt.status = "abandoned"
        attempt.completed_at = utc_now()

    layout = make_layout(seed=secrets.randbits(63))
    question_order_json, option_orders_json = dump_layout(layout)
    attempt = PlacementTestAttempt(
        user_id=user_id,
        test_version=TEST_VERSION,
        status="in_progress",
        current_position=0,
        correct_answers=0,
        question_order_json=question_order_json,
        option_orders_json=option_orders_json,
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt

async def get_attempt_for_user(
    session: AsyncSession,
    attempt_id: int,
    user_id: int,
) -> PlacementTestAttempt | None:
    return await session.scalar(
        select(PlacementTestAttempt).where(
            PlacementTestAttempt.id == attempt_id,
            PlacementTestAttempt.user_id == user_id,
        )
    )

async def record_answer(
    session: AsyncSession,
    *,
    attempt_id: int,
    user_id: int,
    position: int,
    display_option: int,
) -> AnswerOutcome:
    attempt = await session.scalar(
        select(PlacementTestAttempt)
        .where(
            PlacementTestAttempt.id == attempt_id,
            PlacementTestAttempt.user_id == user_id,
        )
        .with_for_update()
    )
    if attempt is None or attempt.status != "in_progress":
        return AnswerOutcome(accepted=False)
    if attempt.current_position != position:
        return AnswerOutcome(accepted=False, next_position=attempt.current_position)

    layout = load_layout(attempt.question_order_json, attempt.option_orders_json)
    question = question_at(layout, position)
    try:
        canonical_option = canonical_index_for_display(
            layout,
            question,
            display_option,
        )
    except IndexError:
        return AnswerOutcome(accepted=False, next_position=attempt.current_position)

    existing = await session.scalar(
        select(PlacementTestAnswer).where(
            PlacementTestAnswer.attempt_id == attempt.id,
            PlacementTestAnswer.question_id == question.id,
        )
    )
    if existing is not None:
        return AnswerOutcome(accepted=False, next_position=attempt.current_position)

    is_correct = canonical_option == question.correct_index
    session.add(
        PlacementTestAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            question_level=question.level,
            display_option=display_option,
            canonical_option=canonical_option,
            is_correct=is_correct,
        )
    )
    attempt.current_position += 1
    attempt.correct_answers += int(is_correct)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return AnswerOutcome(accepted=False)

    if attempt.current_position < len(layout.question_ids):
        await session.commit()
        return AnswerOutcome(accepted=True, next_position=attempt.current_position)

    correct_ids = set((await session.scalars(
        select(PlacementTestAnswer.question_id).where(
            PlacementTestAnswer.attempt_id == attempt.id,
            PlacementTestAnswer.is_correct.is_(True),
        )
    )).all())
    result = evaluate_level(correct_ids)
    attempt.status = "completed"
    attempt.result_level = result.level
    attempt.recommended_start_level = result.recommended_start_level
    attempt.result_score = result.score
    attempt.result_is_borderline = result.is_borderline
    attempt.band_scores_json = json.dumps(result.band_scores, ensure_ascii=False)
    attempt.completed_at = utc_now()
    await session.commit()
    return AnswerOutcome(accepted=True, result=result)
