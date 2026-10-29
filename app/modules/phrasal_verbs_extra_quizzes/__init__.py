from __future__ import annotations

__all__ = ["router", "extra_practice_callback"]


def __getattr__(name: str):
    if name == "router":
        from .handlers import router
        return router
    if name == "extra_practice_callback":
        from .integration import extra_practice_callback
        return extra_practice_callback
    raise AttributeError(name)