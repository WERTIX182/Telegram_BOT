from aiogram.filters.callback_data import CallbackData

class LevelPlacementActionCallback(CallbackData, prefix="lpa"):
    action: str
    value: str

class LevelPlacementAnswerCallback(CallbackData, prefix="lpq"):
    attempt_id: int
    position: int
    display_option: int
