from aiogram.filters.callback_data import CallbackData

class VerbActionCallback(CallbackData, prefix="vma"):
    action: str
    value: str

class VerbListCallback(CallbackData, prefix="vml"):
    level: str
    page: int

class VerbQuizCallback(CallbackData, prefix="vmq"):
    attempt_id: int
    card_order: int
    option_index: int
