import re
from typing import TypeVar, Type, Any
from datetime import datetime
from collections.abc import Callable
from loguru import logger


def timestamp_as_file_name(file_extension: str) -> str:
    """
    Return the current timestamp as a file name.

    Args:
        file_extension: The file extension (without the dot)

    Example:
            timestamp_as_file_name("pdf") -> "121629.628.pdf"
    """
    now = datetime.now()
    return f"{now.strftime("%H%M%S.%f")}.{file_extension}"


def retry(func: Callable, max_attempts: int = 1, catch=(Exception,)) -> Any:
    """
        Call a zero-argument callable, retrying on selected exceptions.
        Runs ``func()`` up to ``max_attempts`` times. On each failure that matches
        ``catch``, logs a warning and tries again. On the final failed attempt,
        logs an error and re-raises the exception.
        Args:
            func: Callable with no parameters (often a closure). Its return value
                is returned on success.
            max_attempts: Maximum number of execution attempts. Defaults to 1
                (no retries unless increased).
            catch: Exception type or tuple of types to treat as retryable.
                Defaults to ``(Exception,)``.
        Returns:
            Whatever ``func()`` returns on the first successful attempt.
        Raises:
            catch: Re-raises the last caught exception when all attempts are
                exhausted.
        Example:
            >>> def flaky():
            ...     ...
            >>> retry(func=flaky, max_attempts=3)
    """
    for attempt in range(max_attempts):
        try:
            return func()
        except catch as exc:
            f = func.__name__
            e = type(exc).__name__
            msg = f"Function {f} failed to run because it raised an {e} error."
            if attempt == max_attempts - 1:
                logger.error(msg)
                raise exc
            logger.warning(f"{msg} Retrying... (Attempt {attempt + 1}/{max_attempts})")

    return None  # Just to silence IDE warnings
