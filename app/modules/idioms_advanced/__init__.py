"""Idioms Advanced module for ENGLISH В КАРМАНЕ."""

from . import models as _models  # регистрация моделей в Base.metadata
from .handlers import router

__all__ = ["router"]
