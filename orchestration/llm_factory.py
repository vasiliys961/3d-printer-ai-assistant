"""Фабрика для создания LLM клиентов в зависимости от провайдера"""
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from utils.exceptions import LLMError
from utils.logger import logger
import sys
import os

# Добавляем корневую директорию в путь для импорта config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def get_llm():
    """Получить LLM клиент в зависимости от настроек"""
    provider = settings.llm_provider.lower()
    
    try:
        if provider == "openrouter":
            # OpenRouter использует OpenAI-совместимый API
            if not settings.openrouter_api_key:
                raise LLMError("OPENROUTER_API_KEY не установлен в .env файле")
            
            return ChatOpenAI(
                model="anthropic/claude-3.5-sonnet",  # Модель Claude через OpenRouter
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key,
                temperature=0.7,
                max_tokens=2048,
                timeout=60.0,  # Timeout для запросов
                default_headers={
                    "HTTP-Referer": "https://github.com/your-repo",  # Опционально
                    "X-Title": "3D Printer AI Assistant"  # Опционально
                }
            )
        elif provider == "together":
            # Together.ai также использует OpenAI-совместимый API
            if not settings.together_api_key:
                raise LLMError("TOGETHER_API_KEY не установлен в .env файле")
            
            return ChatOpenAI(
                model="meta-llama/Llama-3.1-70B-Instruct-Turbo",
                base_url="https://api.together.xyz/v1",
                api_key=settings.together_api_key,
                temperature=0.7,
                max_tokens=2048,
                timeout=60.0
            )
        elif provider == "ollama":
            # Ollama локально
            return Ollama(
                base_url=settings.ollama_base_url,
                model="llama3.1:70b",
                temperature=0.7
            )
        else:
            # По умолчанию Anthropic
            if not settings.anthropic_api_key:
                raise LLMError("ANTHROPIC_API_KEY не установлен в .env файле")
            
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,
                max_tokens=2048,
                api_key=settings.anthropic_api_key,
                timeout=60.0
            )
    except Exception as e:
        logger.error(f"Ошибка создания LLM клиента: {e}", exc_info=True)
        raise LLMError(f"Не удалось создать LLM клиент: {e}") from e

