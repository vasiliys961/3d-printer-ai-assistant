"""Фабрика для создания LLM клиентов в зависимости от провайдера"""
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
import sys
import os

# Добавляем корневую директорию в путь для импорта config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def get_llm():
    """Получить LLM клиент в зависимости от настроек"""
    provider = settings.llm_provider.lower()
    
    if provider == "openrouter":
        # OpenRouter использует OpenAI-совместимый API
        return ChatOpenAI(
            model="anthropic/claude-3.5-sonnet",
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            temperature=0.7,
            max_tokens=2048
        )
    elif provider == "together":
        # Together.ai также использует OpenAI-совместимый API
        return ChatOpenAI(
            model="meta-llama/Llama-3.1-70B-Instruct-Turbo",
            base_url="https://api.together.xyz/v1",
            api_key=settings.together_api_key,
            temperature=0.7,
            max_tokens=2048
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
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2048,
            api_key=settings.anthropic_api_key
        )

