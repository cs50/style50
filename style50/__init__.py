__all__ = ["Style50", "checks", "StyleCheck"]

from .core import Style50, StyleCheck

# Ensure that checks are registered
from . import checks
