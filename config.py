"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = ""
    telegram_bot_token: str = ""
    
    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Together.ai
    together_api_key: str = ""
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    
    # LLM Provider
    llm_provider: str = "anthropic"  # "anthropic", "openrouter", "together", "ollama"
    
    # Database
    # Если указан DATABASE_URL, он будет использован вместо отдельных параметров
    database_url: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "printer_ai"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    
    # Storage
    storage_type: Literal["local", "s3"] = "local"
    s3_bucket_name: str = "printer-ai-storage"
    s3_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    
    # Hardware APIs
    klipper_api_url: str = "http://localhost:7125"
    octoprint_api_url: str = "http://localhost:5000"
    octoprint_api_key: str = ""
    
    # Application
    debug: bool = True
    log_level: str = "INFO"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Игнорировать дополнительные поля из .env


settings = Settings()

