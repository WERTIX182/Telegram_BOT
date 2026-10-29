"""Intermediate collocations course plugin for ENGLISH В КАРМАНЕ."""

from . import models as _models  # noqa: F401
from .handlers import router

__all__ = ["router"]
