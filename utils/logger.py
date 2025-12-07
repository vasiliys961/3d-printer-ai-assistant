"""
Централизованное логирование через loguru
"""
import sys
import os
from pathlib import Path
from loguru import logger
from config import settings


def setup_logging():
    """
    Настройка централизованного логирования для всего приложения.
    
    Настраивает:
    - Логирование в файл с ротацией
    - Логирование в консоль
    - Структурированное логирование для анализа
    - Разные уровни для разных окружений
    """
    # Удаляем стандартный handler loguru
    logger.remove()
    
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Определяем уровень логирования из настроек
    log_level = settings.log_level.upper() if hasattr(settings, 'log_level') else "INFO"
    
    # Формат для файлового лога (структурированный)
    file_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Формат для консольного лога (более компактный)
    console_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Логирование в файл с ротацией
    logger.add(
        log_dir / "app.log",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        level=log_level,
        format=file_format,
        enqueue=True,  # Асинхронное логирование
        backtrace=True,  # Полные трейсы для ошибок
        diagnose=True  # Детальная диагностика
    )
    
    # Отдельный файл для ошибок
    logger.add(
        log_dir / "errors.log",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
        level="ERROR",
        format=file_format,
        enqueue=True,
        backtrace=True,
        diagnose=True
    )
    
    # Логирование в консоль
    if settings.debug if hasattr(settings, 'debug') else True:
        logger.add(
            sys.stderr,
            level=log_level,
            format=console_format,
            colorize=True
        )
    else:
        # В production только WARNING и выше
        logger.add(
            sys.stderr,
            level="WARNING",
            format=console_format,
            colorize=True
        )
    
    return logger


# Инициализируем логирование при импорте модуля
setup_logging()

# Экспортируем настроенный logger
__all__ = ['logger']

