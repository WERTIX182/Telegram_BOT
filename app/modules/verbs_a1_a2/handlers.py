from __future__ import annotations

from html import escape
import random

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.callbacks import SectionCallback

from .callbacks import VerbActionCallback, VerbListCallback, VerbQuizCallback
from .content import cards_for_level, get_card, load_cards
from .keyboards import (
    OPTION_LABELS,
    build_card,
    build_card_list,
    build_course_home,
    build_progress,
    build_quiz,
    build_reset_confirmation,
    build_result,
)
from .repository import (
    get_active_attempt,
    get_attempt_for_user,
    get_or_create_progress,
    record_answer,
    reset_course,
    set_current_card,
    start_attempt,
)
from .service import accuracy, option_order, parse_card_set, progress_bar
from .texts import COURSE_HOME_TEXT

router = Router(name=__name__)

async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise

def _render_card(card) -> str:
    forms = "\n".join(f"• {escape(item)}" for item in card.forms)
    meanings = "\n".join(f"• {escape(item)}" for item in card.meanings)
    examples = "\n".join(
        f"• <b>{escape(example.en)}</b> — {escape(example.ru)}"
        for example in card.examples
    )
    mistake = card.common_mistake
    return (
        f"<b>🔤 A1–A2 • карточка {card.order} из 50 • {card.level}</b>\n"
        f"<b>{escape(card.title_en)}</b>\n"
        f"<i>{escape(card.title_ru)}</i>\n\n"
        f"<b>Как употребляется</b>\n{escape(card.rule)}\n\n"
        f"<b>Формы и модели</b>\n{forms}\n\n"
        f"<b>Основные значения</b>\n{meanings}\n\n"
        f"<b>Не перепутайте</b>\n{escape(card.contrast)}\n\n"
        f"<b>Примеры</b>\n{examples}\n\n"
        f"<b>⚠️ Типичная ошибка</b>\n"
        f"❌ {escape(mistake.wrong)}\n"
        f"✅ {escape(mistake.right)}\n"
        f"{escape(mistake.note)}"
    )

def _render_quiz(card, attempt_id: int) -> str:
    options = "\n".join(
        f"<b>{OPTION_LABELS[display_index]})</b> {escape(card.quiz.options[canonical_index])}"
        for display_index, canonical_index in enumerate(option_order(attempt_id, card))
    )
    return (
        f"<b>🧠 Глаголы • {escape(card.level)}</b>\n\n"
        f"<b>{escape(card.quiz.prompt)}</b>\n\n"
        f"{options}\n\n"
        "Нажмите букву выбранного ответа."
    )

def _render_feedback(card, option_index: int, is_correct: bool) -> str:
    selected = card.quiz.options[option_index]
    correct = card.quiz.options[card.quiz.correct_index]
    icon = "✅ Верно" if is_correct else "❌ Пока неверно"
    return (
        f"<b>{icon}</b>\n\n"
        f"Ваш ответ: <b>{escape(selected)}</b>\n"
        f"Правильный ответ: <b>{escape(correct)}</b>\n\n"
        f"💡 {escape(card.quiz.explanation)}"
    )

@router.callback_query(VerbActionCallback.filter(F.action == "home"))
async def open_home(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        active = await get_active_attempt(session, callback.from_user.id)
        completed = parse_card_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        COURSE_HOME_TEXT,
        build_course_home(has_progress=bool(completed) or active is not None),
    )
    await callback.answer()

@router.callback_query(VerbActionCallback.filter(F.action == "continue"))
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
            card = get_card(active.card_order)
            await _safe_edit(callback.message, _render_quiz(card, active.id), build_quiz(active.id, card))
            await callback.answer("Продолжаем мини-квиз")
            return
        progress = await get_or_create_progress(session, callback.from_user.id)
    card = get_card(progress.current_card_order)
    await _safe_edit(callback.message, _render_card(card), build_card(card.order))
    await callback.answer("Продолжаем")

@router.callback_query(VerbActionCallback.filter(F.action == "open"))
async def open_card(
    callback: CallbackQuery,
    callback_data: VerbActionCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        card = get_card(int(callback_data.value))
    except (ValueError, LookupError):
        await callback.answer("Карточка не найдена", show_alert=True)
        return
    async with session_factory() as session:
        await set_current_card(session, callback.from_user.id, card.order)
    await _safe_edit(callback.message, _render_card(card), build_card(card.order))
    await callback.answer()

@router.callback_query(VerbListCallback.filter())
async def open_list(
    callback: CallbackQuery,
    callback_data: VerbListCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    cards = cards_for_level(callback_data.level)
    max_page = (len(cards) - 1) // 8
    page = max(0, min(callback_data.page, max_page))
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        completed = parse_card_set(progress.completed_cards_json)
        mastered = parse_card_set(progress.mastered_cards_json)
    text = (
        f"<b>📋 Глаголы {escape(callback_data.level)}</b>\n\n"
        "✅ — ответ верный\n"
        "☑️ — карточка пройдена, но её стоит повторить\n"
        "▫️ — ещё не пройдена"
    )
    await _safe_edit(
        callback.message,
        text,
        build_card_list(
            cards=cards,
            completed=completed,
            mastered=mastered,
            level=callback_data.level,
            page=page,
        ),
    )
    await callback.answer()

@router.callback_query(VerbActionCallback.filter(F.action == "random"))
async def random_card(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    card = random.choice(load_cards())
    async with session_factory() as session:
        await set_current_card(session, callback.from_user.id, card.order)
    await _safe_edit(callback.message, _render_card(card), build_card(card.order))
    await callback.answer("Случайная карточка")

@router.callback_query(VerbActionCallback.filter(F.action == "start_quiz"))
async def start_quiz(
    callback: CallbackQuery,
    callback_data: VerbActionCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        card = get_card(int(callback_data.value))
    except (ValueError, LookupError):
        await callback.answer("Карточка не найдена", show_alert=True)
        return
    async with session_factory() as session:
        attempt = await start_attempt(session, callback.from_user.id, card)
    await _safe_edit(callback.message, _render_quiz(card, attempt.id), build_quiz(attempt.id, card))
    await callback.answer("Один короткий вопрос")

@router.callback_query(VerbQuizCallback.filter())
async def answer_quiz(
    callback: CallbackQuery,
    callback_data: VerbQuizCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        card = get_card(callback_data.card_order)
    except LookupError:
        await callback.answer("Карточка не найдена", show_alert=True)
        return
    if not 0 <= callback_data.option_index < len(card.quiz.options):
        await callback.answer("Некорректный ответ", show_alert=True)
        return
    async with session_factory() as session:
        attempt = await get_attempt_for_user(
            session,
            callback_data.attempt_id,
            callback.from_user.id,
        )
        if attempt is None or attempt.card_order != card.order:
            await callback.answer("Попытка не найдена", show_alert=True)
            return
        result = await record_answer(
            session,
            attempt=attempt,
            card=card,
            option_index=callback_data.option_index,
        )
    if not result.accepted:
        await callback.answer("Этот ответ уже принят", show_alert=True)
        return
    await _safe_edit(
        callback.message,
        _render_feedback(card, callback_data.option_index, result.is_correct),
        build_result(card.order),
    )
    await callback.answer("Верно" if result.is_correct else "Посмотрите объяснение")

@router.callback_query(VerbActionCallback.filter(F.action == "progress"))
async def show_progress(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        completed = parse_card_set(progress.completed_cards_json)
        mastered = parse_card_set(progress.mastered_cards_json)
    current = get_card(progress.current_card_order)
    text = (
        "<b>📊 Прогресс: глаголы A1–A2</b>\n\n"
        f"{progress_bar(len(completed))} <b>{len(completed)} из 50</b> карточек пройдено\n"
        f"✅ Верно с первой попытки: <b>{len(mastered)}</b>\n"
        f"🎯 Точность: <b>{accuracy(progress.correct_answers, progress.total_answers)}%</b>\n\n"
        f"Следующая карточка: <b>{current.order}. {escape(current.title_en)}</b>"
    )
    await _safe_edit(
        callback.message,
        text,
        build_progress(progress.current_card_order),
    )
    await callback.answer()

@router.callback_query(VerbActionCallback.filter(F.action == "reset_request"))
async def request_reset(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(
            callback.message,
            "<b>Удалить весь прогресс по глаголам A1–A2?</b>\n\n"
            "Будут удалены результаты всех карточек.",
            build_reset_confirmation(),
        )
    await callback.answer()

@router.callback_query(VerbActionCallback.filter(F.action == "reset_confirm"))
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
        build_course_home(has_progress=False),
    )
    await callback.answer("Прогресс удалён")
