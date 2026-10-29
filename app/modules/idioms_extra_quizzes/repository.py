from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.idempotency import idempotent_answer

from .content import COURSE_ID, get_set
from .models import (
    IdiomExtraPracticeAnswer,
    IdiomExtraPracticeAttempt,
    IdiomExtraPracticeProgress,
)
from .schemas import AnswerResult, ExtraQuestionSet
from .service import dump_key_set, parse_key_set, practice_key

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def get_or_create_progress(
    session: AsyncSession, user_id: int
) -> IdiomExtraPracticeProgress:
    progress = await session.scalar(select(IdiomExtraPracticeProgress).where(
        IdiomExtraPracticeProgress.user_id == user_id,
        IdiomExtraPracticeProgress.course_id == COURSE_ID,
    ))
    if progress is not None:
        return progress
    progress = IdiomExtraPracticeProgress(user_id=user_id, course_id=COURSE_ID)
    session.add(progress)
    await session.commit()
    await session.refresh(progress)
    return progress

async def get_active_attempt(
    session: AsyncSession, user_id: int
) -> IdiomExtraPracticeAttempt | None:
    return await session.scalar(select(IdiomExtraPracticeAttempt).where(
        IdiomExtraPracticeAttempt.user_id == user_id,
        IdiomExtraPracticeAttempt.course_id == COURSE_ID,
        IdiomExtraPracticeAttempt.status == "in_progress",
    ).order_by(IdiomExtraPracticeAttempt.started_at.desc()))

async def get_attempt_for_user(
    session: AsyncSession, attempt_id: int, user_id: int
) -> IdiomExtraPracticeAttempt | None:
    return await session.scalar(select(IdiomExtraPracticeAttempt).where(
        IdiomExtraPracticeAttempt.id == attempt_id,
        IdiomExtraPracticeAttempt.user_id == user_id,
        IdiomExtraPracticeAttempt.course_id == COURSE_ID,
    ))

async def start_attempt(
    session: AsyncSession, user_id: int, practice_set: ExtraQuestionSet
) -> IdiomExtraPracticeAttempt:
    active = (await session.scalars(select(IdiomExtraPracticeAttempt).where(
        IdiomExtraPracticeAttempt.user_id == user_id,
        IdiomExtraPracticeAttempt.course_id == COURSE_ID,
        IdiomExtraPracticeAttempt.status == "in_progress",
    ))).all()
    for attempt in active:
        attempt.status = "abandoned"
        attempt.completed_at = utc_now()

    attempt = IdiomExtraPracticeAttempt(
        user_id=user_id,
        course_id=COURSE_ID,
        level_code=practice_set.level_code,
        base_card_id=practice_set.base_card_id,
        card_order=practice_set.card_order,
        current_question_index=0,
    )
    session.add(attempt)
    await get_or_create_progress(session, user_id)
    await session.commit()
    await session.refresh(attempt)
    return attempt

@idempotent_answer(AnswerResult)
async def record_answer(
    session: AsyncSession,
    *,
    attempt: IdiomExtraPracticeAttempt,
    question_index: int,
    option_index: int,
) -> AnswerResult:
    if attempt.status != "in_progress" or question_index != attempt.current_question_index:
        return AnswerResult(accepted=False)

    practice_set = get_set(attempt.level_code, attempt.card_order)
    if not 0 <= question_index < len(practice_set.questions):
        return AnswerResult(accepted=False)
    question = practice_set.questions[question_index]
    if not 0 <= option_index < len(question.options):
        return AnswerResult(accepted=False)

    existing = await session.scalar(select(IdiomExtraPracticeAnswer).where(
        IdiomExtraPracticeAnswer.attempt_id == attempt.id,
        IdiomExtraPracticeAnswer.question_index == question_index,
    ))
    if existing is not None:
        return AnswerResult(accepted=False)

    is_correct = option_index == question.correct_index
    session.add(IdiomExtraPracticeAnswer(
        attempt_id=attempt.id,
        question_index=question_index,
        selected_option_index=option_index,
        is_correct=is_correct,
    ))
    attempt.correct_answers += int(is_correct)

    progress = await get_or_create_progress(session, attempt.user_id)
    progress.total_answers += 1
    progress.correct_answers += int(is_correct)

    is_complete = question_index + 1 >= len(practice_set.questions)
    if is_complete:
        attempt.status = "completed"
        attempt.completed_at = utc_now()
        completed = parse_key_set(progress.completed_sets_json)
        mastered = parse_key_set(progress.mastered_sets_json)
        key = practice_key(attempt.level_code, attempt.card_order)
        completed.add(key)
        if attempt.correct_answers == len(practice_set.questions):
            mastered.add(key)
        else:
            mastered.discard(key)
        progress.completed_sets_json = dump_key_set(completed)
        progress.mastered_sets_json = dump_key_set(mastered)
        next_index = None
    else:
        attempt.current_question_index = question_index + 1
        next_index = attempt.current_question_index

    await session.commit()
    return AnswerResult(
        accepted=True,
        is_correct=is_correct,
        is_complete=is_complete,
        next_question_index=next_index,
        score=attempt.correct_answers,
    )
