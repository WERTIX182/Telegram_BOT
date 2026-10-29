from aiogram.filters.callback_data import CallbackData


class CollocationActionCallback(CallbackData, prefix="caa"):
    action: str
    value: str


class CollocationListCallback(CallbackData, prefix="cal"):
    group_type: str
    group_value: str
    page: int


class CollocationQuizCallback(CallbackData, prefix="caq"):
    attempt_id: int
    card_order: int
    option_index: int
