"""Complete A1-A2 grammar course plugin for ENGLISH В КАРМАНЕ.

Importing this package registers its SQLAlchemy models in Base.metadata and exposes
an aiogram Router for inclusion before the generic menu router.
"""

from . import models as models  # noqa: F401
from .handlers import router

__all__ = ["router"]
