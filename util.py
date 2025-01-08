import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from loguru import logger

# Define a generic type variable for the function
T = TypeVar("T")


def timer(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def timer_wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds")
        return result

    return timer_wrapper
