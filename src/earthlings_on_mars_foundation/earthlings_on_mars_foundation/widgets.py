"""Custom editors."""

from __future__ import annotations

from typing import ClassVar

from django import forms


class LuaEditor(forms.Textarea):
    """Editor for Lua scripts."""

    def __init__(self, attrs: dict[str, str] | None = None) -> None:
        """Initialize the editor."""
        super().__init__(attrs)
        self.attrs["class"] = "lua-editor"
        self.attrs["style"] = "width: 90%; height: 100%;"

    class Media:
        """Details on where to retrieve editor files from."""

        css: ClassVar[dict[str, tuple[str]]] = {
            "all": ("https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.css",),
        }
        js: ClassVar[tuple[str]] = (
            "https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/lua/lua.min.js",
            "/static/codemirror-6.65/init.js",
        )
