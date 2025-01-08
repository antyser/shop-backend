import asyncio
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, Coroutine, ParamSpec, TypeVar, cast

from loguru import logger

T = TypeVar("T")
P = ParamSpec("P")


def timer(
    func: Callable[P, Coroutine[Any, Any, T] | T]
) -> Callable[P, Coroutine[Any, Any, T] | T]:
    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(
            f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds"
        )
        return result

    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)  # type: ignore
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(
            f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds"
        )
        return result

    if asyncio.iscoroutinefunction(func):
        return cast(Callable[P, Coroutine[Any, Any, T]], async_wrapper)
    return cast(Callable[P, T], sync_wrapper)
