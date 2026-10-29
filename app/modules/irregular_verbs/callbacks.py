from aiogram.filters.callback_data import CallbackData


class IrregularVerbActionCallback(CallbackData, prefix="iva"):
    action: str
    value: str


class IrregularVerbListCallback(CallbackData, prefix="ivl"):
    group_type: str
    group_value: str
    page: int


class IrregularVerbQuizCallback(CallbackData, prefix="ivq"):
    attempt_id: int
    card_order: int
    option_index: int
