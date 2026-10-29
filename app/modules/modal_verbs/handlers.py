from __future__ import annotations

from html import escape
import random

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .callbacks import ModalVerbActionCallback, ModalVerbListCallback, ModalVerbQuizCallback
from .content import TOTAL_TOPICS, get_topic, load_topics, topics_for_category, topics_for_level
from .keyboards import OPTION_LABELS, build_categories, build_course_home, build_feedback, build_progress, build_quiz, build_reset_confirmation, build_result, build_topic_card, build_topic_list
from .repository import get_active_attempt, get_attempt_for_user, get_or_create_progress, record_answer, reset_course, set_current_topic, start_attempt
from .service import accuracy, option_order, parse_topic_set, progress_bar
from .texts import CATEGORY_NAMES, COURSE_HOME_TEXT

router = Router(name=__name__)

async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise

def _render_topic(topic) -> str:
    patterns = "\n".join(f"• {escape(item)}" for item in topic.patterns)
    examples = "\n".join(f"• <b>{escape(example.en)}</b> — {escape(example.ru)}" for example in topic.examples)
    mistake = topic.common_mistake
    return (
        f"<b>🧭 Тема {topic.order} из {TOTAL_TOPICS} • {escape(topic.level)}</b>\n"
        f"<b>{escape(topic.title_en)}</b>\n<i>{escape(topic.title_ru)}</i>\n\n"
        f"<b>Короткое правило</b>\n{escape(topic.rule)}\n\n"
        f"<b>Модели</b>\n{patterns}\n\n"
        f"<b>Примеры</b>\n{examples}\n\n"
        f"<b>⚠️ Типичная ошибка</b>\n❌ {escape(mistake.wrong)}\n✅ {escape(mistake.right)}\n{escape(mistake.note)}"
    )

def _render_quiz(topic, quiz_index: int, attempt_id: int) -> str:
    quiz = topic.quizzes[quiz_index]
    lines = []
    for display_index, canonical_index in enumerate(option_order(attempt_id, topic, quiz_index)):
        lines.append(f"<b>{OPTION_LABELS[display_index]})</b> {escape(quiz.options[canonical_index])}")
    return (f"<b>🧠 Модальные глаголы</b>\nЗадание <b>{quiz_index + 1} из {len(topic.quizzes)}</b>\n\n"
            f"<b>{escape(quiz.prompt)}</b>\n\n" + "\n".join(lines) + "\n\nНажмите букву выбранного ответа.")

def _render_feedback(topic, quiz_index: int, option_index: int, is_correct: bool) -> str:
    quiz = topic.quizzes[quiz_index]
    selected = quiz.options[option_index]
    correct = quiz.options[quiz.correct_index]
    icon = "✅ Верно" if is_correct else "❌ Пока неверно"
    return (f"<b>{icon}</b>\n\nВаш ответ: <b>{escape(selected)}</b>\nПравильный ответ: <b>{escape(correct)}</b>\n\n💡 {escape(quiz.explanation)}")

@router.callback_query(ModalVerbActionCallback.filter(F.action == "home"))
async def open_home(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        active = await get_active_attempt(session, callback.from_user.id)
        completed = parse_topic_set(progress.completed_topics_json)
    await _safe_edit(callback.message, COURSE_HOME_TEXT, build_course_home(has_progress=bool(completed) or active is not None))
    await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "categories"))
async def open_categories(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(callback.message, "<b>🗂 Типы модальных глаголов</b>\n\nВыберите группу тем.", build_categories())
    await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "continue"))
async def continue_course(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    async with session_factory() as session:
        active = await get_active_attempt(session, callback.from_user.id)
        if active is not None:
            topic = get_topic(active.topic_order)
            index = min(active.current_quiz_index, len(topic.quizzes)-1)
            await _safe_edit(callback.message, _render_quiz(topic, index, active.id), build_quiz(active.id, topic, index))
            await callback.answer("Продолжаем мини-квиз"); return
        progress = await get_or_create_progress(session, callback.from_user.id)
    topic = get_topic(progress.current_topic_order)
    await _safe_edit(callback.message, _render_topic(topic), build_topic_card(topic.order))
    await callback.answer("Продолжаем")

@router.callback_query(ModalVerbActionCallback.filter(F.action == "open"))
async def open_topic(callback: CallbackQuery, callback_data: ModalVerbActionCallback, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    try:
        topic = get_topic(int(callback_data.value))
    except (ValueError, LookupError):
        await callback.answer("Тема не найдена", show_alert=True); return
    async with session_factory() as session:
        await set_current_topic(session, callback.from_user.id, topic.order)
    await _safe_edit(callback.message, _render_topic(topic), build_topic_card(topic.order))
    await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "level_list"))
async def open_current_level(callback: CallbackQuery, callback_data: ModalVerbActionCallback, session_factory: async_sessionmaker[AsyncSession]) -> None:
    try:
        topic = get_topic(int(callback_data.value))
    except (ValueError, LookupError):
        await callback.answer("Тема не найдена", show_alert=True); return
    await open_list(callback, ModalVerbListCallback(group_type="level", group_value=topic.level, page=0), session_factory)

@router.callback_query(ModalVerbListCallback.filter())
async def open_list(callback: CallbackQuery, callback_data: ModalVerbListCallback, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    if callback_data.group_type == "level":
        topics = topics_for_level(callback_data.group_value); title = f"Уровень {callback_data.group_value}"
    elif callback_data.group_type == "category":
        topics = topics_for_category(callback_data.group_value); title = CATEGORY_NAMES.get(callback_data.group_value, callback_data.group_value)
    else:
        await callback.answer("Неизвестная группа", show_alert=True); return
    max_page = max(0, (len(topics)-1)//8); page = max(0, min(callback_data.page, max_page))
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        completed = parse_topic_set(progress.completed_topics_json); mastered = parse_topic_set(progress.mastered_topics_json)
    text = f"<b>📋 {escape(title)}</b>\n\n✅ — 2 из 2\n☑️ — тему стоит повторить\n▫️ — ещё не пройдена"
    await _safe_edit(callback.message, text, build_topic_list(topics=topics, completed=completed, mastered=mastered, group_type=callback_data.group_type, group_value=callback_data.group_value, page=page))
    await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "random"))
async def random_topic(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    topic = random.choice(load_topics())
    async with session_factory() as session:
        await set_current_topic(session, callback.from_user.id, topic.order)
    await _safe_edit(callback.message, _render_topic(topic), build_topic_card(topic.order))
    await callback.answer("Случайная тема")

@router.callback_query(ModalVerbActionCallback.filter(F.action == "start_quiz"))
async def start_quiz_handler(callback: CallbackQuery, callback_data: ModalVerbActionCallback, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    try:
        topic = get_topic(int(callback_data.value))
    except (ValueError, LookupError):
        await callback.answer("Тема не найдена", show_alert=True); return
    async with session_factory() as session:
        attempt = await start_attempt(session, callback.from_user.id, topic)
    await _safe_edit(callback.message, _render_quiz(topic, 0, attempt.id), build_quiz(attempt.id, topic, 0))
    await callback.answer("Два коротких задания")

@router.callback_query(ModalVerbQuizCallback.filter())
async def answer_quiz(callback: CallbackQuery, callback_data: ModalVerbQuizCallback, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    try:
        topic = get_topic(callback_data.topic_order)
        quiz = topic.quizzes[callback_data.quiz_index]
        if not 0 <= callback_data.option_index < len(quiz.options): raise IndexError
    except (LookupError, IndexError):
        await callback.answer("Задание не найдено", show_alert=True); return
    async with session_factory() as session:
        attempt = await get_attempt_for_user(session, callback_data.attempt_id, callback.from_user.id)
        if attempt is None:
            await callback.answer("Попытка не найдена", show_alert=True); return
        result = await record_answer(session, attempt=attempt, topic=topic, quiz_index=callback_data.quiz_index, option_index=callback_data.option_index)
    if not result.accepted:
        await callback.answer("Этот ответ уже обработан"); return
    feedback = _render_feedback(topic, callback_data.quiz_index, callback_data.option_index, result.is_correct)
    if result.is_complete:
        status = "Тема освоена" if result.score == len(topic.quizzes) else "Тему лучше повторить"
        text = f"{feedback}\n\n<b>🏁 {status}</b>\nРезультат: <b>{result.score} из {len(topic.quizzes)}</b>.\n\nПрогресс сохранён автоматически."
        await _safe_edit(callback.message, text, build_result(topic.order)); await callback.answer("Готово"); return
    await _safe_edit(callback.message, feedback, build_feedback(callback_data.attempt_id)); await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "next_quiz"))
async def show_next_quiz(callback: CallbackQuery, callback_data: ModalVerbActionCallback, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    try:
        attempt_id = int(callback_data.value)
    except ValueError:
        await callback.answer("Попытка не найдена", show_alert=True); return
    async with session_factory() as session:
        attempt = await get_attempt_for_user(session, attempt_id, callback.from_user.id)
    if attempt is None or attempt.status != "in_progress":
        await callback.answer("Незавершённое задание не найдено", show_alert=True); return
    topic = get_topic(attempt.topic_order); index = attempt.current_quiz_index
    if not 0 <= index < len(topic.quizzes):
        await callback.answer("Тема уже завершена", show_alert=True); return
    await _safe_edit(callback.message, _render_quiz(topic, index, attempt.id), build_quiz(attempt.id, topic, index)); await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "progress"))
async def show_progress(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        completed = parse_topic_set(progress.completed_topics_json); mastered = parse_topic_set(progress.mastered_topics_json)
    text = (f"<b>📊 Модальные глаголы</b>\n\n{progress_bar(len(completed))} <b>{len(completed)} из {TOTAL_TOPICS}</b>\n"
            f"Освоено полностью: <b>{len(mastered)}</b>\nОтветов: <b>{progress.total_answers}</b>\nТочность: <b>{accuracy(progress.correct_answers, progress.total_answers)}%</b>")
    await _safe_edit(callback.message, text, build_progress(progress.current_topic_order)); await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "reset_request"))
async def reset_request(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(callback.message, "<b>Удалить весь прогресс по модальным глаголам?</b>\n\nЭто действие нельзя отменить.", build_reset_confirmation())
    await callback.answer()

@router.callback_query(ModalVerbActionCallback.filter(F.action == "reset_confirm"))
async def reset_confirm(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if callback.message is None:
        await callback.answer(); return
    async with session_factory() as session:
        await reset_course(session, callback.from_user.id)
    await _safe_edit(callback.message, COURSE_HOME_TEXT, build_course_home(has_progress=False)); await callback.answer("Прогресс удалён")
