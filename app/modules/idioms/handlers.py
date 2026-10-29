from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.callbacks import SectionCallback

router = Router(name="idioms")

@router.callback_query(SectionCallback.filter(F.name == "idioms"))
async def idioms_entry(callback: CallbackQuery):
    await callback.answer("Раздел Идиомы в разработке.")
