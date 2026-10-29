from aiogram.filters.callback_data import CallbackData

class PhrasalVerbActionCallback(CallbackData, prefix="pvaa"):
    action: str
    value: str

class PhrasalVerbListCallback(CallbackData, prefix="pvla"):
    group_type: str
    group_value: str
    page: int

class PhrasalVerbQuizCallback(CallbackData, prefix="pvqa"):
    attempt_id: int
    card_order: int
    option_index: int
