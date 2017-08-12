__all__ = ["Style50", "languages", "StyleCheck", "Error"]

from .style50 import Style50, StyleCheck, Error

# Ensure that all language checks are registered
from . import languages
