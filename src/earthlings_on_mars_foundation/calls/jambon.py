"""Jambonz helper functions."""

from __future__ import annotations
from typing import Union, Any


def gather(text: str, callback: str, digits: int | None = None, min_digits: int | None = None, max_digits: int | None = None) -> dict[str, Union[str, dict[str, str]]]:
    """Get DTMF digits from the player."""
    data: dict[str, Any] = {
        "verb": "gather",
        "actionHook": callback,
        "input": ["digits"],  # Can also include "speech"
        "bargein": False,
        "dtmfBargein": True,
        "finishOnKey": "#",
        "say": say(text),
        "interDigitTimeout": 5,
    }

    del data["say"]["verb"]

    if digits is not None:
        data["numDigits"] = digits
    if min_digits is not None:
        data["minDigits"] = min_digits
    if max_digits is not None:
        data["maxDigits"] = max_digits

    return data

    # self.timeout = 8

    # self.  "recognizer": {
    # self.    "vendor": "Google",
    # self.    "language": "en-US",
    # self.    "hints": ["sales", "support"],
    # self.    "hintsBoost": 10
    # self.  },


def say(text: str) -> dict[str, str]:
    """Read text to the player."""
    return {"verb": "say", "text": text}
