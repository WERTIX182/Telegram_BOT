from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.idempotency import idempotent_answer

from .content import COURSE_ID
from .models import AdvancedCollocationAnswer, AdvancedCollocationAttempt, AdvancedCollocationProgress
from .schemas import AnswerResult, CollocationCard
from .service import dump_card_set, first_uncompleted, parse_card_set


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_progress(session: AsyncSession, user_id: int) -> AdvancedCollocationProgress:
    progress = await session.scalar(select(AdvancedCollocationProgress).where(
        AdvancedCollocationProgress.user_id == user_id,
        AdvancedCollocationProgress.course_id == COURSE_ID,
    ))
    if progress is not None:
        return progress
    progress = AdvancedCollocationProgress(user_id=user_id, course_id=COURSE_ID)
    session.add(progress)
    await session.commit()
    await session.refresh(progress)
    return progress


async def set_current_card(session: AsyncSession, user_id: int, card_order: int) -> AdvancedCollocationProgress:
    progress = await get_or_create_progress(session, user_id)
    progress.current_card_order = card_order
    await session.commit()
    return progress


async def get_active_attempt(session: AsyncSession, user_id: int) -> AdvancedCollocationAttempt | None:
    return await session.scalar(select(AdvancedCollocationAttempt).where(
        AdvancedCollocationAttempt.user_id == user_id,
        AdvancedCollocationAttempt.course_id == COURSE_ID,
        AdvancedCollocationAttempt.status == "in_progress",
    ).order_by(AdvancedCollocationAttempt.started_at.desc()))


async def get_attempt_for_user(session: AsyncSession, attempt_id: int, user_id: int) -> AdvancedCollocationAttempt | None:
    return await session.scalar(select(AdvancedCollocationAttempt).where(
        AdvancedCollocationAttempt.id == attempt_id,
        AdvancedCollocationAttempt.user_id == user_id,
        AdvancedCollocationAttempt.course_id == COURSE_ID,
    ))


async def start_attempt(session: AsyncSession, user_id: int, card: CollocationCard) -> AdvancedCollocationAttempt:
    active = (await session.scalars(select(AdvancedCollocationAttempt).where(
        AdvancedCollocationAttempt.user_id == user_id,
        AdvancedCollocationAttempt.course_id == COURSE_ID,
        AdvancedCollocationAttempt.status == "in_progress",
    ))).all()
    for attempt in active:
        attempt.status = "abandoned"
        attempt.completed_at = utc_now()
    attempt = AdvancedCollocationAttempt(user_id=user_id, course_id=COURSE_ID, card_id=card.id, card_order=card.order)
    session.add(attempt)
    progress = await get_or_create_progress(session, user_id)
    progress.current_card_order = card.order
    await session.commit()
    await session.refresh(attempt)
    return attempt


@idempotent_answer(AnswerResult)
async def record_answer(session: AsyncSession, *, attempt: AdvancedCollocationAttempt,
                        card: CollocationCard, option_index: int) -> AnswerResult:
    if attempt.status != "in_progress":
        return AnswerResult(accepted=False)
    existing = await session.scalar(select(AdvancedCollocationAnswer).where(
        AdvancedCollocationAnswer.attempt_id == attempt.id))
    if existing is not None:
        return AnswerResult(accepted=False)
    is_correct = option_index == card.quiz.correct_index
    session.add(AdvancedCollocationAnswer(attempt_id=attempt.id,
                selected_option_index=option_index, is_correct=is_correct))
    attempt.status = "completed"
    attempt.completed_at = utc_now()
    attempt.correct_answers = int(is_correct)
    progress = await get_or_create_progress(session, attempt.user_id)
    completed = parse_card_set(progress.completed_cards_json)
    mastered = parse_card_set(progress.mastered_cards_json)
    completed.add(attempt.card_order)
    if is_correct:
        mastered.add(attempt.card_order)
    else:
        mastered.discard(attempt.card_order)
    progress.completed_cards_json = dump_card_set(completed)
    progress.mastered_cards_json = dump_card_set(mastered)
    progress.total_answers += 1
    progress.correct_answers += int(is_correct)
    progress.current_card_order = first_uncompleted(completed)
    await session.commit()
    return AnswerResult(accepted=True, is_correct=is_correct, is_complete=True, score=int(is_correct))


async def reset_course(session: AsyncSession, user_id: int) -> None:
    attempt_ids = list(await session.scalars(select(AdvancedCollocationAttempt.id).where(
        AdvancedCollocationAttempt.user_id == user_id,
        AdvancedCollocationAttempt.course_id == COURSE_ID,
    )))
    if attempt_ids:
        await session.execute(delete(AdvancedCollocationAnswer).where(
            AdvancedCollocationAnswer.attempt_id.in_(attempt_ids)))
    await session.execute(delete(AdvancedCollocationAttempt).where(
        AdvancedCollocationAttempt.user_id == user_id,
        AdvancedCollocationAttempt.course_id == COURSE_ID))
    await session.execute(delete(AdvancedCollocationProgress).where(
        AdvancedCollocationProgress.user_id == user_id,
        AdvancedCollocationProgress.course_id == COURSE_ID))
    await session.commit()
