from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import SectionCallback

from .callbacks import IrregularVerbActionCallback, IrregularVerbListCallback, IrregularVerbQuizCallback
from .content import TOTAL_CARDS
from .schemas import IrregularVerbCard
from .service import option_order

OPTION_LABELS = ("A", "B", "C", "D")


def action(action_name: str, value: str = "0") -> str:
    return IrregularVerbActionCallback(action=action_name, value=value).pack()


def build_course_home(*, has_progress: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_progress:
        builder.button(text="▶️ Продолжить обучение", callback_data=action("continue"))
    builder.button(text="🚀 Начать с первого глагола", callback_data=action("open", "1"))
    builder.button(text="🟢 A1–A2", callback_data=IrregularVerbListCallback(group_type="level", group_value="A1-A2", page=0))
    builder.button(text="🔴 B1", callback_data=IrregularVerbListCallback(group_type="level", group_value="B1", page=0))
    builder.button(text="🔵 B2–C1", callback_data=IrregularVerbListCallback(group_type="level", group_value="B2-C1", page=0))
    builder.button(text="🧩 По моделям форм", callback_data=action("patterns"))
    builder.button(text="🎲 Случайный глагол", callback_data=action("random"))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="🧹 Сбросить прогресс", callback_data=action("reset_request"))
    builder.button(text="← К разделам глаголов", callback_data=SectionCallback(name="verbs"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def build_patterns() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    labels = {
        "AAA": "AAA — cut–cut–cut",
        "ABB": "ABB — build–built–built",
        "ABA": "ABA — come–came–come",
        "ABC": "ABC — write–wrote–written",
        "SPECIAL": "Особые случаи",
    }
    for pattern, label in labels.items():
        builder.button(text=label, callback_data=IrregularVerbListCallback(group_type="pattern", group_value=pattern, page=0))
    builder.button(text="← В неправильные глаголы", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()


def build_card_list(*, cards: tuple[IrregularVerbCard, ...], completed: set[int], mastered: set[int], group_type: str, group_value: str, page: int, page_size: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * page_size
    page_cards = cards[start:start + page_size]
    for card in page_cards:
        marker = "✅" if card.order in mastered else "☑️" if card.order in completed else "▫️"
        builder.button(text=f"{marker} {card.infinitive} — {card.past_simple} — {card.past_participle}", callback_data=action("open", str(card.order)))
    builder.adjust(1)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="←", callback_data=IrregularVerbListCallback(group_type=group_type, group_value=group_value, page=page-1).pack()))
    if start + page_size < len(cards):
        nav.append(InlineKeyboardButton(text="→", callback_data=IrregularVerbListCallback(group_type=group_type, group_value=group_value, page=page+1).pack()))
    if nav:
        builder.row(*nav)
    back = action("patterns") if group_type == "pattern" else action("home")
    builder.row(InlineKeyboardButton(text="← Назад", callback_data=back))
    return builder.as_markup()


def build_card(card_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Мини-квиз", callback_data=action("start_quiz", str(card_order)))
    if card_order > 1:
        builder.button(text="← Предыдущий", callback_data=action("open", str(card_order-1)))
    if card_order < TOTAL_CARDS:
        builder.button(text="Следующий →", callback_data=action("open", str(card_order+1)))
    builder.button(text="📋 Мой уровень", callback_data=action("level_list", str(card_order)))
    builder.button(text="← В неправильные глаголы", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1, 2, 1, 1, 1)
    return builder.as_markup()


def build_quiz(attempt_id: int, card: IrregularVerbCard) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for display_index, canonical_index in enumerate(option_order(attempt_id, card)):
        builder.button(
            text=OPTION_LABELS[display_index],
            callback_data=IrregularVerbQuizCallback(
                attempt_id=attempt_id,
                card_order=card.order,
                option_index=canonical_index,
            ),
        )
    builder.adjust(2, 2)
    builder.row(InlineKeyboardButton(text="💾 Сохранить и выйти", callback_data=SectionCallback(name="main_menu").pack()))
    return builder.as_markup()


def build_result(card_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить", callback_data=action("start_quiz", str(card_order)))
    if card_order < TOTAL_CARDS:
        builder.button(text="Следующий глагол →", callback_data=action("open", str(card_order+1)))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="← В неправильные глаголы", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def build_progress(current_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Продолжить", callback_data=action("open", str(current_order)))
    builder.button(text="← В неправильные глаголы", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def build_reset_confirmation() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, удалить прогресс", callback_data=action("reset_confirm"))
    builder.button(text="Отмена", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()
