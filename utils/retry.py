"""
Утилиты для retry логики с экспоненциальной задержкой
"""
import asyncio
import time
from typing import Callable, TypeVar, List, Optional
from functools import wraps
from utils.logger import logger
from utils.exceptions import LLMError, HardwareError, RAGError

T = TypeVar('T')


async def retry_async(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> T:
    """
    Retry логика с экспоненциальной задержкой для асинхронных функций.
    
    Args:
        func: Асинхронная функция для выполнения
        max_attempts: Максимальное количество попыток
        initial_delay: Начальная задержка в секундах
        max_delay: Максимальная задержка в секундах
        exponential_base: База для экспоненциального роста задержки
        exceptions: Кортеж исключений, при которых нужно повторять попытку
        on_retry: Функция, вызываемая при каждой попытке
    
    Returns:
        Результат выполнения функции
    
    Raises:
        Последнее исключение, если все попытки исчерпаны
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                logger.error(f"Все {max_attempts} попыток исчерпаны. Последняя ошибка: {e}")
                raise
            
            # Вычисляем задержку с экспоненциальным ростом
            delay = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)
            
            logger.warning(
                f"Попытка {attempt}/{max_attempts} не удалась: {e}. "
                f"Повтор через {delay:.2f}с..."
            )
            
            if on_retry:
                on_retry(attempt, e, delay)
            
            await asyncio.sleep(delay)
    
    # Не должно достичь сюда, но на всякий случай
    if last_exception:
        raise last_exception


def retry_sync(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> T:
    """
    Retry логика с экспоненциальной задержкой для синхронных функций.
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                logger.error(f"Все {max_attempts} попыток исчерпаны. Последняя ошибка: {e}")
                raise
            
            delay = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)
            
            logger.warning(
                f"Попытка {attempt}/{max_attempts} не удалась: {e}. "
                f"Повтор через {delay:.2f}с..."
            )
            
            if on_retry:
                on_retry(attempt, e, delay)
            
            time.sleep(delay)
    
    if last_exception:
        raise last_exception


def retry_decorator(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Декоратор для автоматического retry функций.
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_async(
                    lambda: func(*args, **kwargs),
                    max_attempts=max_attempts,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    exponential_base=exponential_base,
                    exceptions=exceptions
                )
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return retry_sync(
                    lambda: func(*args, **kwargs),
                    max_attempts=max_attempts,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    exponential_base=exponential_base,
                    exceptions=exceptions
                )
            return sync_wrapper
    return decorator

