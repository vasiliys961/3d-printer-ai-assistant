"""
Кэширование через Redis
"""
import json
import hashlib
from typing import Optional, Any
import redis
from config import settings
from utils.logger import logger


class RedisCache:
    """Кэш через Redis"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        
        try:
            # Пытаемся подключиться к Redis
            if hasattr(settings, 'redis_host'):
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Проверяем подключение
                self.redis_client.ping()
                self.enabled = True
                logger.info("Redis cache enabled")
            else:
                logger.warning("Redis settings not found, cache disabled")
        except Exception as e:
            logger.warning(f"Redis connection failed, cache disabled: {e}")
            self.enabled = False
    
    def _make_key(self, prefix: str, query: str) -> str:
        """Создать ключ кэша из запроса"""
        # Нормализуем запрос (убираем лишние пробелы, приводим к нижнему регистру)
        normalized = " ".join(query.lower().split())
        # Создаем хэш для длинных запросов
        if len(normalized) > 100:
            hash_obj = hashlib.md5(normalized.encode())
            return f"{prefix}:{hash_obj.hexdigest()}"
        return f"{prefix}:{normalized}"
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}", exc_info=True)
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Установить значение в кэш с TTL (по умолчанию 1 час)"""
        if not self.enabled:
            return
        
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Error setting cache: {e}", exc_info=True)
    
    def delete(self, key: str):
        """Удалить значение из кэша"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}", exc_info=True)
    
    def clear_pattern(self, pattern: str):
        """Очистить все ключи по паттерну"""
        if not self.enabled:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys matching {pattern}")
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}", exc_info=True)


# Глобальный экземпляр кэша
cache = RedisCache()

