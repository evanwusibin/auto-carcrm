# -*- coding: utf-8 -*-
import time
import functools
from typing import TypeVar, Callable, Any
from app.shared.runtime.logger import logger

T = TypeVar('T')


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """通用重试装饰器，支持指数退避。"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc = None
            current_delay = delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        logger.warning(
                            f"[retry] {func.__name__} 第{attempt}次失败: {exc}, "
                            f"{current_delay:.1f}s 后重试"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[retry] {func.__name__} 第{attempt}次失败: {exc}, 重试耗尽"
                        )
            raise last_exc
        return wrapper
    return decorator


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """异步通用重试装饰器。"""
    import asyncio

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            current_delay = delay
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        logger.warning(
                            f"[async_retry] {func.__name__} 第{attempt}次失败: {exc}, "
                            f"{current_delay:.1f}s 后重试"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[async_retry] {func.__name__} 第{attempt}次失败: {exc}, 重试耗尽"
                        )
            raise last_exc
        return wrapper
    return decorator
