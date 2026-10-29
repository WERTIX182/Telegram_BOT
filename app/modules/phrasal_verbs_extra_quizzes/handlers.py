from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .callbacks import ExtraPracticeActionCallback, ExtraPracticeQuizCallback
from .content import get_set
from .keyboards import OPTION_LABELS, build_feedback, build_quiz
from .repository import (
    get_active_attempt,
    get_attempt_for_user,
    record_answer,
    start_attempt,
)
from .service import option_order

router = Router(name=__name__)


async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise


def _render_question(practice_set, attempt_id: int, question_index: int) -> str:
    question = practice_set.questions[question_index]
    lines = []
    for display_index, canonical_index in enumerate(option_order(attempt_id, question)):
        lines.append(
            f"<b>{OPTION_LABELS[display_index]})</b> "
            f"{escape(question.options[canonical_index])}"
        )
    # Neutral header: the target phrasal verb and translation are not shown here.
    return (
        f"<b>🧠 Дополнительная практика • {escape(practice_set.level)}</b>\n"
        f"<b>Вопрос {question_index + 1} из 2</b>\n\n"
        f"{escape(question.prompt)}\n\n"
        + "\n".join(lines)
        + "\n\nНажмите букву выбранного ответа."
    )


def _render_feedback(
    practice_set,
    question_index: int,
    option_index: int,
    is_correct: bool,
) -> str:
    question = practice_set.questions[question_index]
    selected = question.options[option_index]
    correct = question.options[question.correct_index]
    icon = "✅ Верно" if is_correct else "❌ Пока неверно"
    return (
        f"<b>{icon}</b>\n\n"
        f"Ваш ответ: <b>{escape(selected)}</b>\n"
        f"Правильный ответ: <b>{escape(correct)}</b>\n\n"
        f"💡 {escape(question.explanation)}"
    )


@router.callback_query(ExtraPracticeActionCallback.filter())
async def handle_action(
    callback: CallbackQuery,
    callback_data: ExtraPracticeActionCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        practice_set = get_set(callback_data.level_code, callback_data.card_order)
    except LookupError:
        await callback.answer("Дополнительные вопросы не найдены", show_alert=True)
        return

    async with session_factory() as session:
        if callback_data.action == "start":
            active = await get_active_attempt(session, callback.from_user.id)
            if (
                active is not None
                and active.level_code == practice_set.level_code
                and active.card_order == practice_set.card_order
            ):
                attempt = active
            else:
                attempt = await start_attempt(session, callback.from_user.id, practice_set)
        elif callback_data.action == "continue":
            attempt = await get_active_attempt(session, callback.from_user.id)
            if (
                attempt is None
                or attempt.level_code != practice_set.level_code
                or attempt.card_order != practice_set.card_order
            ):
                await callback.answer("Незавершённая попытка не найдена", show_alert=True)
                return
        else:
            await callback.answer("Неизвестное действие", show_alert=True)
            return

    index = attempt.current_question_index
    await _safe_edit(
        callback.message,
        _render_question(practice_set, attempt.id, index),
        build_quiz(
            attempt.id,
            index,
            practice_set.questions[index],
            level_code=practice_set.level_code,
            card_order=practice_set.card_order,
        ),
    )
    await callback.answer("Дополнительная практика")


@router.callback_query(ExtraPracticeQuizCallback.filter())
async def answer_question(
    callback: CallbackQuery,
    callback_data: ExtraPracticeQuizCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
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
        try:
            practice_set = get_set(attempt.level_code, attempt.card_order)
            question = practice_set.questions[callback_data.question_index]
            if not 0 <= callback_data.option_index < len(question.options):
                raise IndexError
        except (LookupError, IndexError):
            await callback.answer("Задание не найдено", show_alert=True)
            return

        result = await record_answer(
            session,
            attempt=attempt,
            question_index=callback_data.question_index,
            option_index=callback_data.option_index,
        )

    if not result.accepted:
        await callback.answer("Этот ответ уже обработан")
        return

    text = _render_feedback(
        practice_set,
        callback_data.question_index,
        callback_data.option_index,
        result.is_correct,
    )
    if result.is_complete:
        text += (
            "\n\n<b>🏁 Дополнительная практика завершена</b>\n"
            f"Результат: <b>{result.score}/2</b>."
        )
    else:
        text += "\n\nОтвет сохранён. Переходим ко второму вопросу."

    await _safe_edit(
        callback.message,
        text,
        build_feedback(
            level_code=practice_set.level_code,
            card_order=practice_set.card_order,
            is_complete=result.is_complete,
        ),
    )
    await callback.answer("Ответ сохранён")