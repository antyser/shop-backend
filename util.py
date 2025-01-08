import time
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from loguru import logger

T = TypeVar("T")
P = ParamSpec("P")


def timer(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator for timing synchronous functions"""

    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds")
        return result

    return sync_wrapper


def atimer(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    """Decorator for timing asynchronous functions"""

    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds")
        return result

    return async_wrapper
