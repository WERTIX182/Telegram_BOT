from aiogram.filters.callback_data import CallbackData

class WordFormationActionCallback(CallbackData, prefix="wfa"):
    action: str
    value: str

class WordFormationListCallback(CallbackData, prefix="wfl"):
    group_type: str
    group_value: str
    page: int

class WordFormationQuizCallback(CallbackData, prefix="wfq"):
    attempt_id: int
    card_order: int
    option_index: int
