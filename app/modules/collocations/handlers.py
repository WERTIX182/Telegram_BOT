from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.callbacks import SectionCallback

router = Router(name="collocations")

@router.callback_query(SectionCallback.filter(F.name == "collocations"))
async def collocations_entry(callback: CallbackQuery):
    await callback.answer("Раздел Коллокации в разработке.")
