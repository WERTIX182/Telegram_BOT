from __future__ import annotations

from app.modules.idioms_extra_quizzes.integration import extra_practice_callback

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import ExtraPracticeActionCallback, ExtraPracticeQuizCallback
from .schemas import ExtraQuestion
from .service import option_order

OPTION_LABELS = ("A", "B", "C", "D")

def action(action_name: str, level_code: str, card_order: int) -> str:
    return ExtraPracticeActionCallback(
        action=action_name,
        level_code=level_code,
        card_order=card_order,
    ).pack()

def _base_card_callback(level_code: str, card_order: int) -> str:
    # Compatible with the source modules used to build this add-on.
    prefix = "idia" if level_code == "i" else "idaa"
    return f"{prefix}:open:{card_order}"

def build_quiz(
    attempt_id: int,
    question_index: int,
    question: ExtraQuestion,
    *,
    level_code: str,
    card_order: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for display_index, canonical_index in enumerate(option_order(attempt_id, question)):
        builder.button(
            text=OPTION_LABELS[display_index],
            callback_data=ExtraPracticeQuizCallback(
                attempt_id=attempt_id,
                question_index=question_index,
                option_index=canonical_index,
            ),
        )
    builder.adjust(2, 2)
    builder.row(InlineKeyboardButton(
        text="💾 Сохранить и выйти",
        callback_data=_base_card_callback(level_code, card_order),
    ))
    return builder.as_markup()

def build_feedback(
    *,
    level_code: str,
    card_order: int,
    is_complete: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_complete:
        builder.button(
            text="Следующий вопрос →",
            callback_data=action("continue", level_code, card_order),
        )
    else:
        builder.button(
            text="🔄 Повторить два вопроса",
            callback_data=action("start", level_code, card_order),
        )
        builder.button(
            text="← Вернуться к карточке",
            callback_data=_base_card_callback(level_code, card_order),
        )
    builder.adjust(1)
    return builder.as_markup()