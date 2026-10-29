from aiogram.filters.callback_data import CallbackData

class PhrasalVerbActionCallback(CallbackData, prefix="pva"):
    action: str
    value: str

class PhrasalVerbListCallback(CallbackData, prefix="pvl"):
    group_type: str
    group_value: str
    page: int

class PhrasalVerbQuizCallback(CallbackData, prefix="pvq"):
    attempt_id: int
    card_order: int
    option_index: int
