import sys
from importlib.metadata import PackageNotFoundError, version

# Require Python 3.8+
if sys.version_info < (3, 8):
    sys.exit("You have an old version of python. Install version 3.8 or higher.")

# Get version
try:
    __version__ = version("style50")
except PackageNotFoundError:
    __version__ = "UNKNOWN"


__all__ = ["Style50", "languages", "StyleCheck", "Error"]

from ._api import Style50, StyleCheck, Error

# Ensure that all language checks are registered.
from . import languages
