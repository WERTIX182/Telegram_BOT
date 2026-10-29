from aiogram.filters.callback_data import CallbackData

class ModalVerbActionCallback(CallbackData, prefix="mva"):
    action: str
    value: str

class ModalVerbListCallback(CallbackData, prefix="mvl"):
    group_type: str
    group_value: str
    page: int

class ModalVerbQuizCallback(CallbackData, prefix="mvq"):
    attempt_id: int
    topic_order: int
    quiz_index: int
    option_index: int
