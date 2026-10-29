from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.callbacks import SectionCallback

router = Router(name="phrasal_verbs")

@router.callback_query(SectionCallback.filter(F.name == "phrasal_verbs"))
async def phrasal_verbs_entry(callback: CallbackQuery):
    await callback.answer("Раздел Фразовые глаголы в разработке.")
