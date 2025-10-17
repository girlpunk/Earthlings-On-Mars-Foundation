"""Lua helper functions."""

import asyncio
from collections.abc import Coroutine
from typing import Any

from lupa import LuaRuntime


class AsyncLuaRuntime(LuaRuntime):
    """Asynchronous helpers for Lua runtime."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Prepare the runtime."""
        self.loop = asyncio.get_event_loop()

        setattr(self.globals()["python"], "async", asyncio.coroutines)
        setattr(self.globals()["python"], "await", self.coroutine)

        super().__init__(*args, **kwargs)

    async def execute(self, lua_code: str, *args: Any) -> Any:  # noqa: ANN401
        """Execute lua code."""
        return await self.loop.run_in_executor(None, super().execute, lua_code, *args)

    async def compile(self, lua_code: str) -> Any:  # noqa: ANN401
        """Compile Lua code."""
        return await self.loop.run_in_executor(None, super().compile, lua_code)

    async def eval(self, lua_code: str, *args: Any) -> Any:  # noqa: ANN401
        """Evaluate Lua code."""
        return await self.loop.run_in_executor(None, super().eval, lua_code, *args)

    def coroutine(self, async_func: Coroutine) -> Any:  # noqa: ANN401
        """Await a python function from inside Lua."""
        future = asyncio.run_coroutine_threadsafe(async_func, self.loop)
        return future.result()
