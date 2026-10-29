from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import SectionCallback

from .callbacks import VerbPatternActionCallback, VerbPatternListCallback, VerbPatternQuizCallback
from .content import TOTAL_TOPICS
from .schemas import VerbPatternTopic
from .service import option_order

OPTION_LABELS = ("A", "B", "C", "D")


def action(action_name: str, value: str = "0") -> str:
    return VerbPatternActionCallback(action=action_name, value=value).pack()


def build_course_home(*, has_progress: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_progress:
        builder.button(text="▶️ Продолжить обучение", callback_data=action("continue"))
    builder.button(text="🚀 Начать с первой темы", callback_data=action("open", "1"))
    builder.button(text="🟢 A2–B1", callback_data=VerbPatternListCallback(group_type="level", group_value="A2-B1", page=0))
    builder.button(text="🔴 B1–B2", callback_data=VerbPatternListCallback(group_type="level", group_value="B1-B2", page=0))
    builder.button(text="🔵 B2–C1", callback_data=VerbPatternListCallback(group_type="level", group_value="B2-C1", page=0))
    builder.button(text="🗂 По типам моделей", callback_data=action("categories"))
    builder.button(text="🎲 Случайная тема", callback_data=action("random"))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="🧹 Сбросить прогресс", callback_data=action("reset_request"))
    builder.button(text="← К разделам глаголов", callback_data=SectionCallback(name="verbs"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1, 3, 1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def build_categories() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    labels = {
        "CORE": "Основные модели",
        "MEANING": "Изменение значения",
        "COMPLEX": "Сложные модели",
        "ADVANCED": "Продвинутые модели",
    }
    for category, label in labels.items():
        builder.button(text=label, callback_data=VerbPatternListCallback(group_type="category", group_value=category, page=0))
    builder.button(text="← В глагольные модели", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()


def build_topic_list(*, topics: tuple[VerbPatternTopic, ...], completed: set[int], mastered: set[int], group_type: str, group_value: str, page: int, page_size: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * page_size
    for topic in topics[start:start + page_size]:
        marker = "✅" if topic.order in mastered else "☑️" if topic.order in completed else "▫️"
        builder.button(text=f"{marker} {topic.order}. {topic.title_ru}", callback_data=action("open", str(topic.order)))
    builder.adjust(1)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="←", callback_data=VerbPatternListCallback(group_type=group_type, group_value=group_value, page=page-1).pack()))
    if start + page_size < len(topics):
        nav.append(InlineKeyboardButton(text="→", callback_data=VerbPatternListCallback(group_type=group_type, group_value=group_value, page=page+1).pack()))
    if nav:
        builder.row(*nav)
    back = action("categories") if group_type == "category" else action("home")
    builder.row(InlineKeyboardButton(text="← Назад", callback_data=back))
    return builder.as_markup()


def build_topic_card(topic_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Выполнить 2 задания", callback_data=action("start_quiz", str(topic_order)))
    if topic_order > 1:
        builder.button(text="← Предыдущая", callback_data=action("open", str(topic_order-1)))
    if topic_order < TOTAL_TOPICS:
        builder.button(text="Следующая →", callback_data=action("open", str(topic_order+1)))
    builder.button(text="📋 Темы моего уровня", callback_data=action("level_list", str(topic_order)))
    builder.button(text="← В глагольные модели", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1, 2, 1, 1, 1)
    return builder.as_markup()


def build_quiz(attempt_id: int, topic: VerbPatternTopic, quiz_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for display_index, canonical_index in enumerate(option_order(attempt_id, topic, quiz_index)):
        builder.button(text=OPTION_LABELS[display_index], callback_data=VerbPatternQuizCallback(attempt_id=attempt_id, topic_order=topic.order, quiz_index=quiz_index, option_index=canonical_index))
    builder.adjust(2, 2)
    builder.row(InlineKeyboardButton(text="💾 Сохранить и выйти", callback_data=SectionCallback(name="main_menu").pack()))
    return builder.as_markup()


def build_feedback(attempt_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Следующее задание →", callback_data=action("next_quiz", str(attempt_id)))
    builder.button(text="💾 Сохранить и выйти", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def build_result(topic_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить тему", callback_data=action("start_quiz", str(topic_order)))
    if topic_order < TOTAL_TOPICS:
        builder.button(text="Следующая тема →", callback_data=action("open", str(topic_order+1)))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="← В глагольные модели", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def build_progress(current_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Продолжить", callback_data=action("open", str(current_order)))
    builder.button(text="← В глагольные модели", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def build_reset_confirmation() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, удалить прогресс", callback_data=action("reset_confirm"))
    builder.button(text="Отмена", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()
