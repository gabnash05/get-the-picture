"""Guesser data tools and their public image-reader API."""

from typing import Any

__version__ = "0.1.0"
__all__ = ["IndexedDrawings", "preprocess"]


def __getattr__(name: str) -> Any:
    from .common import load_step

    if name == "IndexedDrawings":
        return load_step("05-loader").IndexedDrawings
    if name == "preprocess":
        return load_step("06-images").preprocess
    raise AttributeError(name)
