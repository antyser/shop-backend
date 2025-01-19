import logfire
from loguru import logger


def init_logfire() -> None:
    logfire.configure(send_to_logfire="if-token-present")
    logfire.instrument_pydantic()
    logfire.instrument_httpx()

    logger.configure(handlers=[logfire.loguru_handler()])
