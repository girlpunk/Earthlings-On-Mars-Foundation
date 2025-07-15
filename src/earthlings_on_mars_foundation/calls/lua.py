from lupa import LuaRuntime
import asyncio

class AsyncLuaRuntime(LuaRuntime):
    def __init__(self, *args, **kwargs):
        self.loop = asyncio.get_event_loop()
        
        setattr(self.globals()['python'], 'async', asyncio.coroutines)
        setattr(self.globals()['python'], 'await', self.coroutine)

    async def execute(self, lua_code, *args):
        return await self.loop.run_in_executor(None, super().execute, lua_code, *args)

    async def compile(self, lua_code):
        return await self.loop.run_in_executor(None, super().compile, lua_code)

    async def eval(self, lua_code, *args):
        return await self.loop.run_in_executor(None, super().eval, lua_code, *args)

    def coroutine(self, async_func):
        future = asyncio.run_coroutine_threadsafe(async_func, self.loop)
        return future.result()
