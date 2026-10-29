from __future__ import annotations

__all__ = [
    "router",
    "level_test_entry_callback",
    "PlacementTestAttempt",
    "PlacementTestAnswer",
]

def __getattr__(name: str):
    if name == "router":
        from .handlers import router
        return router
    if name == "level_test_entry_callback":
        from .keyboards import level_test_entry_callback
        return level_test_entry_callback
    if name in {"PlacementTestAttempt", "PlacementTestAnswer"}:
        from .models import PlacementTestAnswer, PlacementTestAttempt
        return {
            "PlacementTestAttempt": PlacementTestAttempt,
            "PlacementTestAnswer": PlacementTestAnswer,
        }[name]
    raise AttributeError(name)
