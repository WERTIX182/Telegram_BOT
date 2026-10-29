from __future__ import annotations

from html import escape
import random

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.callbacks import SectionCallback

from .callbacks import GrammarActionCallback, GrammarListCallback, GrammarQuizCallback
from .content import get_topic, load_topics, topics_for_level
from .keyboards import (
    OPTION_LABELS,
    build_course_home,
    build_grammar_levels,
    build_progress_keyboard,
    build_quiz_feedback,
    build_quiz_keyboard,
    build_reset_confirmation,
    build_topic_card,
    build_topic_list,
    build_topic_result,
)
from .repository import (
    get_active_attempt,
    get_attempt_for_user,
    get_or_create_progress,
    record_answer,
    reset_course,
    set_current_topic,
    start_attempt,
)
from .service import accuracy, option_order, parse_topic_set, progress_bar
from .texts import COURSE_HOME_TEXT, GRAMMAR_LEVELS_TEXT

router = Router(name=__name__)

async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise

def _render_topic(topic) -> str:
    forms = "\n".join(f"• {escape(item)}" for item in topic.forms)
    examples = "\n".join(
        f"• <b>{escape(example.en)}</b> — {escape(example.ru)}"
        for example in topic.examples
    )
    mistake = topic.common_mistake
    return (
        f"<b>📗 A1–A2 • тема {topic.order} из 70 • {topic.level}</b>\n"
        f"<b>{escape(topic.title_en)}</b>\n"
        f"<i>{escape(topic.title_ru)}</i>\n\n"
        f"<b>Короткое правило</b>\n{escape(topic.rule)}\n\n"
        f"<b>Формы</b>\n{forms}\n\n"
        f"<b>Примеры</b>\n{examples}\n\n"
        f"<b>⚠️ Типичная ошибка</b>\n"
        f"❌ {escape(mistake.wrong)}\n"
        f"✅ {escape(mistake.right)}\n"
        f"{escape(mistake.note)}"
    )

def _render_quiz(topic, quiz_index: int, attempt_id: int) -> str:
    quiz = topic.quizzes[quiz_index]
    options = "\n".join(
        f"<b>{OPTION_LABELS[display_index]})</b> {escape(quiz.options[canonical_index])}"
        for display_index, canonical_index in enumerate(option_order(attempt_id, topic, quiz_index))
    )
    return (
        f"<b>🧠 Грамматика • {escape(topic.level)}</b>\n"
        f"Задание <b>{quiz_index + 1} из 3</b>\n\n"
        f"<b>{escape(quiz.prompt)}</b>\n\n"
        f"{options}\n\n"
        "Нажмите букву выбранного ответа."
    )

def _render_feedback(topic, quiz_index: int, option_index: int, is_correct: bool) -> str:
    quiz = topic.quizzes[quiz_index]
    selected = quiz.options[option_index]
    correct = quiz.options[quiz.correct_index]
    icon = "✅ Верно" if is_correct else "❌ Пока неверно"
    return (
        f"<b>{icon}</b>\n\n"
        f"Ваш ответ: <b>{escape(selected)}</b>\n"
        f"Правильный ответ: <b>{escape(correct)}</b>\n\n"
        f"💡 {escape(quiz.explanation)}"
    )

@router.callback_query(SectionCallback.filter(F.name == "grammar"))
async def open_grammar_levels(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(callback.message, GRAMMAR_LEVELS_TEXT, build_grammar_levels())
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "unavailable"))
async def unavailable_level(callback: CallbackQuery) -> None:
    await callback.answer("Этот уровень будет добавлен следующим отдельным модулем.", show_alert=True)

@router.callback_query(GrammarActionCallback.filter(F.action == "home"))
async def open_course_home(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        active = await get_active_attempt(session, callback.from_user.id)
        completed = parse_topic_set(progress.completed_topics_json)
    await _safe_edit(
        callback.message,
        COURSE_HOME_TEXT,
        build_course_home(has_active_attempt=active is not None, has_progress=bool(completed)),
    )
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "continue"))
async def continue_course(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        active = await get_active_attempt(session, callback.from_user.id)
        if active is not None:
            topic = get_topic(active.topic_order)
            quiz_index = min(active.current_quiz_index, 2)
            await _safe_edit(
                callback.message,
                _render_quiz(topic, quiz_index, active.id),
                build_quiz_keyboard(attempt_id=active.id, topic=topic, quiz_index=quiz_index),
            )
            await callback.answer("Продолжаем")
            return
        progress = await get_or_create_progress(session, callback.from_user.id)
        order = progress.current_topic_order
    topic = get_topic(order)
    await _safe_edit(callback.message, _render_topic(topic), build_topic_card(topic.order))
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "open"))
async def open_topic(
    callback: CallbackQuery,
    callback_data: GrammarActionCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        order = int(callback_data.value)
        topic = get_topic(order)
    except (ValueError, LookupError):
        await callback.answer("Тема не найдена", show_alert=True)
        return
    async with session_factory() as session:
        await set_current_topic(session, callback.from_user.id, order)
    await _safe_edit(callback.message, _render_topic(topic), build_topic_card(order))
    await callback.answer()

@router.callback_query(GrammarListCallback.filter())
async def open_topic_list(
    callback: CallbackQuery,
    callback_data: GrammarListCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    topics = topics_for_level(callback_data.level)
    max_page = (len(topics) - 1) // 8
    page = max(0, min(callback_data.page, max_page))
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        completed = parse_topic_set(progress.completed_topics_json)
        mastered = parse_topic_set(progress.mastered_topics_json)
    text = (
        f"<b>📋 Грамматика {escape(callback_data.level)}</b>\n\n"
        "✅ — тема освоена (2–3 правильных ответа)\n"
        "☑️ — тема пройдена, но её стоит повторить\n"
        "▫️ — тема ещё не пройдена"
    )
    await _safe_edit(
        callback.message,
        text,
        build_topic_list(
            topics=topics,
            completed=completed,
            mastered=mastered,
            level=callback_data.level,
            page=page,
        ),
    )
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "random"))
async def open_random_topic(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    topic = random.choice(load_topics())
    async with session_factory() as session:
        await set_current_topic(session, callback.from_user.id, topic.order)
    await _safe_edit(callback.message, _render_topic(topic), build_topic_card(topic.order))
    await callback.answer("Случайная тема")

@router.callback_query(GrammarActionCallback.filter(F.action == "start_quiz"))
async def start_topic_quiz(
    callback: CallbackQuery,
    callback_data: GrammarActionCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        topic = get_topic(int(callback_data.value))
    except (ValueError, LookupError):
        await callback.answer("Тема не найдена", show_alert=True)
        return
    async with session_factory() as session:
        attempt = await start_attempt(session, callback.from_user.id, topic)
    await _safe_edit(
        callback.message,
        _render_quiz(topic, 0, attempt.id),
        build_quiz_keyboard(attempt_id=attempt.id, topic=topic, quiz_index=0),
    )
    await callback.answer("Три коротких задания")

@router.callback_query(GrammarQuizCallback.filter())
async def answer_quiz(
    callback: CallbackQuery,
    callback_data: GrammarQuizCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        topic = get_topic(callback_data.topic_order)
        quiz = topic.quizzes[callback_data.quiz_index]
        if not 0 <= callback_data.option_index < len(quiz.options):
            raise IndexError
    except (LookupError, IndexError):
        await callback.answer("Задание не найдено", show_alert=True)
        return

    async with session_factory() as session:
        attempt = await get_attempt_for_user(session, callback_data.attempt_id, callback.from_user.id)
        if attempt is None:
            await callback.answer("Попытка не найдена", show_alert=True)
            return
        result = await record_answer(
            session,
            attempt=attempt,
            topic=topic,
            quiz_index=callback_data.quiz_index,
            option_index=callback_data.option_index,
        )

    if not result.accepted:
        await callback.answer("Этот ответ уже обработан")
        return

    feedback = _render_feedback(
        topic,
        callback_data.quiz_index,
        callback_data.option_index,
        result.is_correct,
    )
    if result.is_complete:
        status = "Тема освоена" if result.score >= 2 else "Тему лучше повторить"
        text = (
            f"{feedback}\n\n"
            f"<b>🏁 {status}</b>\n"
            f"Результат: <b>{result.score} из 3</b>.\n\n"
            "Прогресс сохранён автоматически."
        )
        await _safe_edit(callback.message, text, build_topic_result(topic.order))
        await callback.answer("Готово")
        return

    await _safe_edit(
        callback.message,
        feedback,
        build_quiz_feedback(callback_data.attempt_id),
    )
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "next_quiz"))
async def show_next_quiz(
    callback: CallbackQuery,
    callback_data: GrammarActionCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        attempt_id = int(callback_data.value)
    except ValueError:
        await callback.answer("Попытка не найдена", show_alert=True)
        return
    async with session_factory() as session:
        attempt = await get_attempt_for_user(session, attempt_id, callback.from_user.id)
    if attempt is None or attempt.status != "in_progress":
        await callback.answer("Незавершённое задание не найдено", show_alert=True)
        return
    topic = get_topic(attempt.topic_order)
    index = attempt.current_quiz_index
    if not 0 <= index < len(topic.quizzes):
        await callback.answer("Тема уже завершена", show_alert=True)
        return
    await _safe_edit(
        callback.message,
        _render_quiz(topic, index, attempt.id),
        build_quiz_keyboard(attempt_id=attempt.id, topic=topic, quiz_index=index),
    )
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "progress"))
async def show_progress(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        completed = parse_topic_set(progress.completed_topics_json)
        mastered = parse_topic_set(progress.mastered_topics_json)
    current = get_topic(progress.current_topic_order)
    text = (
        "<b>📊 Прогресс по грамматике A1–A2</b>\n\n"
        f"{progress_bar(len(completed))} <b>{len(completed)} из 70</b> тем пройдено\n"
        f"✅ Освоено: <b>{len(mastered)}</b>\n"
        f"🎯 Точность ответов: <b>{accuracy(progress.correct_answers, progress.total_answers)}%</b>\n\n"
        f"Следующая тема: <b>{current.order}. {escape(current.title_en)}</b>"
    )
    await _safe_edit(
        callback.message,
        text,
        build_progress_keyboard(progress.current_topic_order),
    )
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "reset_request"))
async def request_reset(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(
            callback.message,
            "<b>Удалить весь прогресс A1–A2?</b>\n\nБудут удалены пройденные темы, результаты заданий и незавершённая попытка.",
            build_reset_confirmation(),
        )
    await callback.answer()

@router.callback_query(GrammarActionCallback.filter(F.action == "reset_confirm"))
async def confirm_reset(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        await reset_course(session, callback.from_user.id)
    await _safe_edit(
        callback.message,
        COURSE_HOME_TEXT,
        build_course_home(has_active_attempt=False, has_progress=False),
    )
    await callback.answer("Прогресс удалён")
