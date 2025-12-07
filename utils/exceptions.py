"""
Кастомные исключения для приложения
"""


class PrinterAIAssistantException(Exception):
    """Базовое исключение для приложения"""
    pass


class ValidationError(PrinterAIAssistantException):
    """Ошибка валидации входных данных"""
    pass


class DatabaseError(PrinterAIAssistantException):
    """Ошибка работы с базой данных"""
    pass


class RAGError(PrinterAIAssistantException):
    """Ошибка RAG поиска"""
    pass


class LLMError(PrinterAIAssistantException):
    """Ошибка вызова LLM"""
    pass


class GCodeError(PrinterAIAssistantException):
    """Ошибка анализа G-code"""
    pass


class HardwareError(PrinterAIAssistantException):
    """Ошибка подключения к принтеру"""
    pass


class SessionNotFoundError(PrinterAIAssistantException):
    """Сессия не найдена"""
    pass


class UserNotFoundError(PrinterAIAssistantException):
    """Пользователь не найден"""
    pass

