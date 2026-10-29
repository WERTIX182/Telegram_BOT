from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.idempotency import idempotent_answer

from .content import COURSE_ID, GrammarTopic
from .models import (
    GrammarC1Progress,
    GrammarC1TopicAttempt,
    GrammarC1QuizAnswer,
)
from .schemas import AnswerResult
from .service import MASTERY_THRESHOLD, dump_topic_set, first_uncompleted, parse_topic_set


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_progress(session: AsyncSession, user_id: int) -> GrammarC1Progress:
    progress = await session.scalar(
        select(GrammarC1Progress).where(
            GrammarC1Progress.user_id == user_id,
            GrammarC1Progress.course_id == COURSE_ID,
        )
    )
    if progress is not None:
        return progress

    progress = GrammarC1Progress(user_id=user_id, course_id=COURSE_ID)
    session.add(progress)
    await session.commit()
    await session.refresh(progress)
    return progress


async def set_current_topic(
    session: AsyncSession, user_id: int, topic_order: int
) -> GrammarC1Progress:
    progress = await get_or_create_progress(session, user_id)
    progress.current_topic_order = topic_order
    await session.commit()
    return progress


async def get_active_attempt(
    session: AsyncSession, user_id: int
) -> GrammarC1TopicAttempt | None:
    return await session.scalar(
        select(GrammarC1TopicAttempt)
        .where(
            GrammarC1TopicAttempt.user_id == user_id,
            GrammarC1TopicAttempt.course_id == COURSE_ID,
            GrammarC1TopicAttempt.status == "in_progress",
        )
        .order_by(GrammarC1TopicAttempt.started_at.desc())
    )


async def get_attempt_for_user(
    session: AsyncSession, attempt_id: int, user_id: int
) -> GrammarC1TopicAttempt | None:
    return await session.scalar(
        select(GrammarC1TopicAttempt).where(
            GrammarC1TopicAttempt.id == attempt_id,
            GrammarC1TopicAttempt.user_id == user_id,
            GrammarC1TopicAttempt.course_id == COURSE_ID,
        )
    )


async def start_attempt(
    session: AsyncSession, user_id: int, topic: GrammarTopic
) -> GrammarC1TopicAttempt:
    active_attempts = (
        await session.scalars(
            select(GrammarC1TopicAttempt).where(
                GrammarC1TopicAttempt.user_id == user_id,
                GrammarC1TopicAttempt.course_id == COURSE_ID,
                GrammarC1TopicAttempt.status == "in_progress",
            )
        )
    ).all()
    for attempt in active_attempts:
        attempt.status = "abandoned"
        attempt.completed_at = utc_now()

    attempt = GrammarC1TopicAttempt(
        user_id=user_id,
        course_id=COURSE_ID,
        topic_id=topic.id,
        topic_order=topic.order,
    )
    session.add(attempt)
    progress = await get_or_create_progress(session, user_id)
    progress.current_topic_order = topic.order
    await session.commit()
    await session.refresh(attempt)
    return attempt


@idempotent_answer(AnswerResult)
async def record_answer(
    session: AsyncSession,
    *,
    attempt: GrammarC1TopicAttempt,
    topic: GrammarTopic,
    quiz_index: int,
    option_index: int,
) -> AnswerResult:
    if attempt.status != "in_progress" or attempt.current_quiz_index != quiz_index:
        return AnswerResult(accepted=False)

    existing = await session.scalar(
        select(GrammarC1QuizAnswer).where(
            GrammarC1QuizAnswer.attempt_id == attempt.id,
            GrammarC1QuizAnswer.quiz_index == quiz_index,
        )
    )
    if existing is not None:
        return AnswerResult(accepted=False)

    quiz = topic.quizzes[quiz_index]
    is_correct = option_index == quiz.correct_index
    session.add(
        GrammarC1QuizAnswer(
            attempt_id=attempt.id,
            quiz_index=quiz_index,
            selected_option_index=option_index,
            is_correct=is_correct,
        )
    )
    attempt.current_quiz_index += 1
    if is_correct:
        attempt.correct_answers += 1

    is_complete = attempt.current_quiz_index >= len(topic.quizzes)
    if is_complete:
        attempt.status = "completed"
        attempt.completed_at = utc_now()
        await _apply_completed_topic(session, attempt)

    await session.commit()
    return AnswerResult(
        accepted=True,
        is_correct=is_correct,
        is_complete=is_complete,
        score=attempt.correct_answers,
        next_quiz_index=attempt.current_quiz_index,
    )


async def _apply_completed_topic(
    session: AsyncSession, attempt: GrammarC1TopicAttempt
) -> None:
    progress = await get_or_create_progress(session, attempt.user_id)
    completed = parse_topic_set(progress.completed_topics_json)
    mastered = parse_topic_set(progress.mastered_topics_json)

    completed.add(attempt.topic_order)
    if attempt.correct_answers >= MASTERY_THRESHOLD:
        mastered.add(attempt.topic_order)
    else:
        mastered.discard(attempt.topic_order)

    progress.completed_topics_json = dump_topic_set(completed)
    progress.mastered_topics_json = dump_topic_set(mastered)
    progress.total_answers += 3
    progress.correct_answers += attempt.correct_answers
    progress.current_topic_order = first_uncompleted(completed)


async def reset_course(session: AsyncSession, user_id: int) -> None:
    attempt_ids = list(
        await session.scalars(
            select(GrammarC1TopicAttempt.id).where(
                GrammarC1TopicAttempt.user_id == user_id,
                GrammarC1TopicAttempt.course_id == COURSE_ID,
            )
        )
    )
    if attempt_ids:
        await session.execute(
            delete(GrammarC1QuizAnswer).where(GrammarC1QuizAnswer.attempt_id.in_(attempt_ids))
        )
    await session.execute(
        delete(GrammarC1TopicAttempt).where(
            GrammarC1TopicAttempt.user_id == user_id,
            GrammarC1TopicAttempt.course_id == COURSE_ID,
        )
    )
    await session.execute(
        delete(GrammarC1Progress).where(
            GrammarC1Progress.user_id == user_id,
            GrammarC1Progress.course_id == COURSE_ID,
        )
    )
    await session.commit()
