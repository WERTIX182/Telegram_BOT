from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.idempotency import idempotent_answer

from .content import COURSE_ID
from .models import VerbPatternAnswer, VerbPatternAttempt, VerbPatternProgress
from .schemas import AnswerResult, VerbPatternTopic
from .service import MASTERY_THRESHOLD, dump_topic_set, first_uncompleted, parse_topic_set


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_progress(session: AsyncSession, user_id: int) -> VerbPatternProgress:
    progress = await session.scalar(select(VerbPatternProgress).where(VerbPatternProgress.user_id == user_id, VerbPatternProgress.course_id == COURSE_ID))
    if progress is not None:
        return progress
    progress = VerbPatternProgress(user_id=user_id, course_id=COURSE_ID)
    session.add(progress)
    await session.commit()
    await session.refresh(progress)
    return progress


async def set_current_topic(session: AsyncSession, user_id: int, topic_order: int) -> VerbPatternProgress:
    progress = await get_or_create_progress(session, user_id)
    progress.current_topic_order = topic_order
    await session.commit()
    return progress


async def get_active_attempt(session: AsyncSession, user_id: int) -> VerbPatternAttempt | None:
    return await session.scalar(select(VerbPatternAttempt).where(VerbPatternAttempt.user_id == user_id, VerbPatternAttempt.course_id == COURSE_ID, VerbPatternAttempt.status == "in_progress").order_by(VerbPatternAttempt.started_at.desc()))


async def get_attempt_for_user(session: AsyncSession, attempt_id: int, user_id: int) -> VerbPatternAttempt | None:
    return await session.scalar(select(VerbPatternAttempt).where(VerbPatternAttempt.id == attempt_id, VerbPatternAttempt.user_id == user_id, VerbPatternAttempt.course_id == COURSE_ID))


async def start_attempt(session: AsyncSession, user_id: int, topic: VerbPatternTopic) -> VerbPatternAttempt:
    active = (await session.scalars(select(VerbPatternAttempt).where(VerbPatternAttempt.user_id == user_id, VerbPatternAttempt.course_id == COURSE_ID, VerbPatternAttempt.status == "in_progress"))).all()
    for attempt in active:
        attempt.status = "abandoned"
        attempt.completed_at = utc_now()
    attempt = VerbPatternAttempt(user_id=user_id, course_id=COURSE_ID, topic_id=topic.id, topic_order=topic.order)
    session.add(attempt)
    progress = await get_or_create_progress(session, user_id)
    progress.current_topic_order = topic.order
    await session.commit()
    await session.refresh(attempt)
    return attempt


@idempotent_answer(AnswerResult)
async def record_answer(session: AsyncSession, *, attempt: VerbPatternAttempt, topic: VerbPatternTopic, quiz_index: int, option_index: int) -> AnswerResult:
    if attempt.status != "in_progress" or attempt.current_quiz_index != quiz_index:
        return AnswerResult(accepted=False)
    existing = await session.scalar(select(VerbPatternAnswer).where(VerbPatternAnswer.attempt_id == attempt.id, VerbPatternAnswer.quiz_index == quiz_index))
    if existing is not None:
        return AnswerResult(accepted=False)
    quiz = topic.quizzes[quiz_index]
    is_correct = option_index == quiz.correct_index
    session.add(VerbPatternAnswer(attempt_id=attempt.id, quiz_index=quiz_index, selected_option_index=option_index, is_correct=is_correct))
    attempt.current_quiz_index += 1
    attempt.correct_answers += int(is_correct)
    is_complete = attempt.current_quiz_index >= len(topic.quizzes)
    if is_complete:
        attempt.status = "completed"
        attempt.completed_at = utc_now()
        await _apply_completed_topic(session, attempt, len(topic.quizzes))
    await session.commit()
    return AnswerResult(accepted=True, is_correct=is_correct, is_complete=is_complete, score=attempt.correct_answers, next_quiz_index=attempt.current_quiz_index)


async def _apply_completed_topic(session: AsyncSession, attempt: VerbPatternAttempt, quiz_count: int) -> None:
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
    progress.total_answers += quiz_count
    progress.correct_answers += attempt.correct_answers
    progress.current_topic_order = first_uncompleted(completed)


async def reset_course(session: AsyncSession, user_id: int) -> None:
    attempt_ids = list(await session.scalars(select(VerbPatternAttempt.id).where(VerbPatternAttempt.user_id == user_id, VerbPatternAttempt.course_id == COURSE_ID)))
    if attempt_ids:
        await session.execute(delete(VerbPatternAnswer).where(VerbPatternAnswer.attempt_id.in_(attempt_ids)))
    await session.execute(delete(VerbPatternAttempt).where(VerbPatternAttempt.user_id == user_id, VerbPatternAttempt.course_id == COURSE_ID))
    await session.execute(delete(VerbPatternProgress).where(VerbPatternProgress.user_id == user_id, VerbPatternProgress.course_id == COURSE_ID))
    await session.commit()
