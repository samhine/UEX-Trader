# tools.py
import asyncio


def create_async_callback(async_func, *args, **kwargs):
    def wrapper():
        asyncio.create_task(async_func(*args, **kwargs))
    return wrapper
