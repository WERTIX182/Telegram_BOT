from __future__ import annotations

from html import escape
import random

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from app.callbacks import SectionCallback
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .callbacks import WordFormationActionCallback, WordFormationListCallback, WordFormationQuizCallback
from .content import (
    TOTAL_CARDS,
    cards_for_category,
    cards_for_level,
    get_card,
    load_cards,
)
from .keyboards import (
    OPTION_LABELS,
    build_card,
    build_card_list,
    build_categories,
    build_course_home,
    build_levels,
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
from .texts import CATEGORY_NAMES, COURSE_HOME_TEXT, LEVEL_NAMES, WORD_CLASS_NAMES

router = Router(name=__name__)

@router.callback_query(SectionCallback.filter(F.name == "word_formation"))
async def open_word_formation_section(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Open the course directly from the host project's main menu.

    This handler is intentionally part of the module router. It prevents the
    integration from depending on a separate wrapper file that can easily be
    omitted during assembly. The module router must still be registered before
    a generic SectionCallback placeholder router.
    """
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

async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise

def _render_card(card) -> str:
    forms = "\n".join(
        f"• <b>{escape(item.form)}</b> — "
        f"{escape(WORD_CLASS_NAMES.get(item.word_class, item.word_class))}; "
        f"{escape(item.translation)}"
        for item in card.forms
    )
    examples = "\n".join(
        f"• <b>{escape(example.en)}</b> — {escape(example.ru)}"
        for example in card.examples
    )
    mistake = card.common_mistake
    return (
        f"<b>🧩 Карточка {card.order} из {TOTAL_CARDS} • {escape(card.level)}</b>\n"
        f"<b>{escape(card.title)}</b>\n"
        f"Исходная основа: <code>{escape(card.base_word)}</code>\n\n"
        f"<b>На что смотрим</b>\n{escape(card.focus)}\n\n"
        f"<b>Правило</b>\n{escape(card.rule)}\n\n"
        f"<b>Семья слов</b>\n{forms}\n\n"
        f"<b>✍️ Орфография</b>\n{escape(card.spelling_note)}\n\n"
        f"<b>Примеры</b>\n{examples}\n\n"
        f"<b>⚠️ Частая ошибка</b>\n"
        f"❌ {escape(mistake.wrong)}\n"
        f"✅ {escape(mistake.right)}\n"
        f"{escape(mistake.note)}"
    )

def _render_quiz(card, attempt_id: int) -> str:
    lines = []
    for display_index, canonical_index in enumerate(option_order(attempt_id, card)):
        lines.append(
            f"<b>{OPTION_LABELS[display_index]})</b> "
            f"{escape(card.quiz.options[canonical_index])}"
        )
    return (
        f"<b>🧠 Словообразование • {escape(card.level)}</b>\n\n"
        f"<b>{escape(card.quiz.prompt)}</b>\n\n"
        + "\n".join(lines)
        + "\n\nВыберите форму, которая грамматически и по смыслу подходит в предложение."
    )

def _render_feedback(card, option_index: int, is_correct: bool) -> str:
    selected = card.quiz.options[option_index]
    correct = card.quiz.answer
    icon = "✅ Верно" if is_correct else "❌ Пока неверно"
    return (
        f"<b>{icon}</b>\n\n"
        f"Ваш ответ: <b>{escape(selected)}</b>\n"
        f"Правильный ответ: <b>{escape(correct)}</b>\n\n"
        f"💡 {escape(card.quiz.explanation)}"
    )

@router.callback_query(WordFormationActionCallback.filter(F.action == "home"))
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

@router.callback_query(WordFormationActionCallback.filter(F.action == "categories"))
async def open_categories(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(
            callback.message,
            "<b>🗂 Темы словообразования</b>\n\nВыберите блок.",
            build_categories(),
        )
    await callback.answer()

@router.callback_query(WordFormationActionCallback.filter(F.action == "levels"))
async def open_levels(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(
            callback.message,
            "<b>🎯 Уровни словообразования</b>\n\nКарточки открыты независимо от результата входного теста.",
            build_levels(),
        )
    await callback.answer()

@router.callback_query(WordFormationActionCallback.filter(F.action == "continue"))
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
            await _safe_edit(
                callback.message,
                _render_quiz(card, active.id),
                build_quiz(active.id, card),
            )
            await callback.answer("Продолжаем мини-квиз")
            return
        progress = await get_or_create_progress(session, callback.from_user.id)
    card = get_card(progress.current_card_order)
    await _safe_edit(callback.message, _render_card(card), build_card(card.order))
    await callback.answer("Продолжаем")

@router.callback_query(WordFormationActionCallback.filter(F.action == "open"))
async def open_card(
    callback: CallbackQuery,
    callback_data: WordFormationActionCallback,
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

@router.callback_query(WordFormationActionCallback.filter(F.action == "category_list"))
async def open_current_category(
    callback: CallbackQuery,
    callback_data: WordFormationActionCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    try:
        card = get_card(int(callback_data.value))
    except (ValueError, LookupError):
        await callback.answer("Карточка не найдена", show_alert=True)
        return
    await open_list(
        callback,
        WordFormationListCallback(group_type="category", group_value=card.category, page=0),
        session_factory,
    )

@router.callback_query(WordFormationListCallback.filter())
async def open_list(
    callback: CallbackQuery,
    callback_data: WordFormationListCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    if callback_data.group_type == "category":
        cards = cards_for_category(callback_data.group_value)
        title = CATEGORY_NAMES.get(callback_data.group_value, callback_data.group_value)
    elif callback_data.group_type == "level":
        cards = cards_for_level(callback_data.group_value)
        title = LEVEL_NAMES.get(callback_data.group_value, callback_data.group_value)
    elif callback_data.group_type == "all":
        cards = load_cards()
        title = "Все карточки"
    else:
        await callback.answer("Неизвестная группа", show_alert=True)
        return
    max_page = max(0, (len(cards) - 1) // 8)
    page = max(0, min(callback_data.page, max_page))
    async with session_factory() as session:
        progress = await get_or_create_progress(session, callback.from_user.id)
        completed = parse_card_set(progress.completed_cards_json)
        mastered = parse_card_set(progress.mastered_cards_json)
    text = (
        f"<b>📋 {escape(title)}</b>\n\n"
        "✅ — квиз выполнен верно\n"
        "☑️ — карточку стоит повторить\n"
        "▫️ — ещё не пройдена"
    )
    await _safe_edit(
        callback.message,
        text,
        build_card_list(
            cards=cards,
            completed=completed,
            mastered=mastered,
            group_type=callback_data.group_type,
            group_value=callback_data.group_value,
            page=page,
        ),
    )
    await callback.answer()

@router.callback_query(WordFormationActionCallback.filter(F.action == "random"))
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

@router.callback_query(WordFormationActionCallback.filter(F.action == "start_quiz"))
async def start_quiz(
    callback: CallbackQuery,
    callback_data: WordFormationActionCallback,
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
    await _safe_edit(
        callback.message,
        _render_quiz(card, attempt.id),
        build_quiz(attempt.id, card),
    )
    await callback.answer("Один короткий вопрос")

@router.callback_query(WordFormationQuizCallback.filter())
async def answer_quiz(
    callback: CallbackQuery,
    callback_data: WordFormationQuizCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        card = get_card(callback_data.card_order)
        if not 0 <= callback_data.option_index < len(card.quiz.options):
            raise IndexError
    except (LookupError, IndexError):
        await callback.answer("Задание не найдено", show_alert=True)
        return
    async with session_factory() as session:
        attempt = await get_attempt_for_user(
            session,
            callback_data.attempt_id,
            callback.from_user.id,
        )
        if attempt is None:
            await callback.answer("Попытка не найдена", show_alert=True)
            return
        result = await record_answer(
            session,
            attempt=attempt,
            card=card,
            option_index=callback_data.option_index,
        )
    if not result.accepted:
        await callback.answer("Этот ответ уже обработан")
        return
    feedback = _render_feedback(card, callback_data.option_index, result.is_correct)
    status = "Карточка освоена" if result.is_correct else "Карточку лучше повторить"
    text = (
        f"{feedback}\n\n"
        f"<b>🏁 {status}</b>\n\n"
        "Прогресс сохранён автоматически."
    )
    await _safe_edit(callback.message, text, build_result(card.order))
    await callback.answer("Готово")

@router.callback_query(WordFormationActionCallback.filter(F.action == "progress"))
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
    text = (
        "<b>📊 Словообразование</b>\n\n"
        f"{progress_bar(len(completed))} {len(completed)}/{TOTAL_CARDS}\n\n"
        f"Пройдено карточек: <b>{len(completed)}</b>\n"
        f"Освоено: <b>{len(mastered)}</b>\n"
        f"Ответов: <b>{progress.total_answers}</b>\n"
        f"Точность: <b>{accuracy(progress.correct_answers, progress.total_answers)}%</b>"
    )
    await _safe_edit(callback.message, text, build_progress(progress.current_card_order))
    await callback.answer()

@router.callback_query(WordFormationActionCallback.filter(F.action == "reset_request"))
async def request_reset(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await _safe_edit(
            callback.message,
            "<b>Удалить весь прогресс по словообразованию?</b>\n\n"
            "Это действие нельзя отменить.",
            build_reset_confirmation(),
        )
    await callback.answer()

@router.callback_query(WordFormationActionCallback.filter(F.action == "reset_confirm"))
async def confirm_reset(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        await reset_course(session, callback.from_user.id)
    await _safe_edit(callback.message, COURSE_HOME_TEXT, build_course_home(has_progress=False))
    await callback.answer("Прогресс удалён")
