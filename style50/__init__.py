from pkg_resources import get_distribution, DistributionNotFound
import os

# https://stackoverflow.com/questions/17583443/what-is-the-correct-way-to-share-package-version-with-setup-py-and-the-package
try:
    _dist = get_distribution("style50")
    # Normalize path for cross-OS compatibility.
    _dist_loc = os.path.normcase(_dist.location)
    _here = os.path.normcase(__file__)
    if not _here.startswith(os.path.join(_dist_loc, "style50")):
        # This version is not installed, but another version is.
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = "locally installed, no version information available"
else:
    __version__ = _dist.version

__all__ = ["Style50", "languages", "StyleCheck", "Error"]

from .style50 import Style50, StyleCheck, Error

# Ensure that all language checks are registered.
from . import languages
