"""A1-A2 verb course plugin for ENGLISH В КАРМАНЕ."""

from . import models as models  # noqa: F401
from .handlers import router

__all__ = ["router"]
