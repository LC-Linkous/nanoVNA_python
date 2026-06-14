"""
nvnapython - Unofficial Python package for the NanoVNA series of vector network analyzers.
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("nvnapython")
except PackageNotFoundError:  # not installed (e.g. running from a source tree)
    __version__ = "0.0.0+local"

from .core import nanoVNA

__all__ = ["nanoVNA", "__version__"]
