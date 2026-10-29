from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import SectionCallback

from .callbacks import LevelPlacementActionCallback, LevelPlacementAnswerCallback

OPTION_LABELS = ("A", "B", "C", "D")

def action(action_name: str, value: str = "0") -> str:
    return LevelPlacementActionCallback(action=action_name, value=value).pack()

def level_test_entry_callback() -> str:
    """Recommended direct main-menu callback: lpa:home:0."""
    return action("home")

def build_home(*, has_active: bool, has_completed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_active:
        builder.button(text="▶️ Продолжить тест", callback_data=action("continue"))
        builder.button(text="🔄 Начать заново", callback_data=action("restart"))
    else:
        builder.button(
            text="🔄 Пройти тест ещё раз" if has_completed else "🚀 Начать тест",
            callback_data=action("start"),
        )
    if has_completed:
        builder.button(text="📋 Последний результат", callback_data=action("last_result"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_question(*, attempt_id: int, position: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for display_option, label in enumerate(OPTION_LABELS):
        builder.button(
            text=label,
            callback_data=LevelPlacementAnswerCallback(
                attempt_id=attempt_id,
                position=position,
                display_option=display_option,
            ),
        )
    builder.adjust(2, 2)
    builder.row(
        InlineKeyboardButton(
            text="💾 Сохранить и выйти",
            callback_data=SectionCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()

def build_result() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📘 Перейти к обучению", callback_data=SectionCallback(name="grammar"))
    builder.button(text="🔄 Пройти ещё раз", callback_data=action("restart"))
    builder.button(text="← К тесту", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()
