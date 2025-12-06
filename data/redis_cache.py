"""Redis для кэширования"""
import redis
import json
from typing import Optional, Any
from config import settings


class RedisCache:
    """Менеджер для работы с Redis"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        value = self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def set(self, key: str, value: Any, ex: int = 3600):
        """Установить значение в кэш"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self.client.setex(key, ex, value)
    
    def delete(self, key: str):
        """Удалить ключ из кэша"""
        self.client.delete(key)
    
    def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        return bool(self.client.exists(key))


redis_cache = RedisCache()

