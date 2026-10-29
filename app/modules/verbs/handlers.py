from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.callbacks import SectionCallback

router = Router(name="verbs")

@router.callback_query(SectionCallback.filter(F.name == "verbs"))
async def verbs_entry(callback: CallbackQuery):
    await callback.answer("Раздел Глаголы в разработке.")
