from html import escape
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

from app.keyboards.main import get_main_menu_keyboard


router = Router(name="main_menu")

# Файл изображения должен лежать здесь:
# app/assets/logo_1.jpg
START_IMAGE_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "logo_1.jpg"
)


def build_welcome_text(message: Message) -> str:
    """Формирует приветственный текст."""
    user = message.from_user
    first_name = escape(user.first_name if user and user.first_name else "друг")

    return (
        f"👋 Привет, {first_name}!\n\n"
        "Добро пожаловать в <b>ENGLISH В КАРМАНЕ</b>!\n"
        "Я помогу тебе учить английский язык с комфортом.\n\n"
        "Выбери раздел, который хочешь изучить:"
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Команда /start: приветственная картинка, текст и главное меню."""
    welcome_text = build_welcome_text(message)

    if START_IMAGE_PATH.is_file():
        await message.answer_photo(
            photo=FSInputFile(START_IMAGE_PATH),
        )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Команда /menu: повторно открывает меню без отправки обложки."""
    await message.answer(
        "Выбери раздел, который хочешь изучить:",
        reply_markup=get_main_menu_keyboard(),
    )
