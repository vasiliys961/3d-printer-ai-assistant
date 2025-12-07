"""Главная точка входа приложения"""
import asyncio
from utils.logger import logger


async def main():
    """Главная функция"""
    logger.info("Запуск 3D Printer AI Assistant...")
    
    # Здесь можно добавить инициализацию всех компонентов
    # Например, проверку подключений к БД, загрузку моделей и т.д.
    
    logger.info("Приложение готово к работе")
    logger.info("Используйте:")
    logger.info("  - python -m ui.telegram_bot  для запуска Telegram бота")
    logger.info("  - streamlit run ui/streamlit_dashboard.py  для запуска Dashboard")
    logger.info("  - uvicorn api.main:app --reload  для запуска REST API")


if __name__ == "__main__":
    asyncio.run(main())

