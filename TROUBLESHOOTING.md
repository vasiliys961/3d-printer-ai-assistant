# Решение проблем (Troubleshooting)

## Проблемы с установкой

### Ошибка: `ModuleNotFoundError: No module named 'xxx'`

**Решение:**
```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### Ошибка: `ERROR: Could not find a version that satisfies the requirement`

**Решение:**
- Убедитесь, что используете Python 3.13
- Для `torch` и `torchvision` установите через PyTorch index:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## Проблемы с базой данных

### Ошибка: `connection to server at "localhost" failed`

**Решение:**
1. Проверьте, что PostgreSQL запущен
2. Проверьте `DATABASE_URL` в `.env`
3. Для Neon.tech убедитесь, что используете правильный connection string с `?sslmode=require`

### Ошибка: `relation "users" does not exist`

**Решение:**
```bash
# Примените миграции
alembic upgrade head
```

### Ошибка при миграциях

**Решение:**
```bash
# Проверьте подключение к БД
alembic check

# Если нужно, создайте новую миграцию
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Проблемы с API

### Ошибка: `Form data requires "python-multipart"`

**Решение:**
```bash
pip install python-multipart
```

### Ошибка: `Rate limit exceeded`

**Решение:**
- Это нормально - API имеет rate limiting (10 запросов в минуту для `/chat`)
- Подождите минуту или увеличьте лимит в коде

### Ошибка: `Session not found`

**Решение:**
- Убедитесь, что сессия существует
- Проверьте, что `session_id` правильный
- Сессия может быть завершена (`ended_at` не null)

## Проблемы с LLM

### Ошибка: `API key not found`

**Решение:**
1. Проверьте `.env` файл
2. Убедитесь, что указан правильный API ключ:
   - `OPENROUTER_API_KEY` для OpenRouter
   - `ANTHROPIC_API_KEY` для Anthropic
   - `TOGETHER_API_KEY` для Together.ai

### Ошибка: `Connection timeout`

**Решение:**
- Проверьте интернет-соединение
- Для OpenRouter убедитесь, что используете правильный `OPENROUTER_BASE_URL`
- Попробуйте другой провайдер LLM

## Проблемы с RAG Engine

### Ошибка: `No documents found in knowledge base`

**Решение:**
```bash
# Загрузите базу знаний
python scripts/ingest_knowledge.py
```

### Ошибка: `ChromaDB collection not found`

**Решение:**
- Удалите директорию `./data/chroma` и загрузите базу знаний заново
- Проверьте права доступа к директории

## Проблемы с Redis (кэширование)

### Ошибка: `Redis connection failed`

**Решение:**
- Redis не обязателен - кэширование отключится автоматически
- Если нужен Redis:
  ```bash
  # Установите Redis
  # macOS: brew install redis
  # Linux: sudo apt-get install redis-server
  
  # Запустите Redis
  redis-server
  ```

## Проблемы с ChromaDB

### Ошибка: `Permission denied` при записи в ChromaDB

**Решение:**
```bash
# Проверьте права доступа
chmod -R 755 ./data/chroma
```

## Проблемы с Docker

### Ошибка: `Cannot connect to Docker daemon`

**Решение:**
- Убедитесь, что Docker запущен
- Проверьте права доступа: `sudo usermod -aG docker $USER`

### Ошибка при сборке образа

**Решение:**
```bash
# Очистите кэш Docker
docker system prune -a

# Пересоберите образ
docker-compose build --no-cache
```

## Проблемы с тестами

### Ошибка: `pytest not found`

**Решение:**
```bash
pip install pytest pytest-asyncio
```

### Тесты падают с ошибками БД

**Решение:**
- Тесты используют in-memory SQLite, не требуют реальной БД
- Проверьте, что все фикстуры в `tests/conftest.py` правильно настроены

## Общие проблемы

### Приложение работает медленно

**Решения:**
1. Используйте кэширование Redis для RAG запросов
2. Оптимизируйте запросы к БД (используйте индексы)
3. Уменьшите `top_k` в RAG поиске
4. Используйте более быстрый LLM провайдер

### Высокое потребление памяти

**Решения:**
1. Уменьшите размер батчей в RAG ingestion
2. Ограничьте размер истории диалогов
3. Используйте более легкие модели для embeddings

### Логи не создаются

**Решение:**
```bash
# Создайте директорию для логов
mkdir -p logs

# Проверьте права доступа
chmod -R 755 logs
```

## Получение помощи

Если проблема не решена:

1. Проверьте логи в `logs/app.log` и `logs/errors.log`
2. Включите DEBUG режим в `.env`: `DEBUG=True`, `LOG_LEVEL=DEBUG`
3. Проверьте метрики: `GET /metrics`
4. Создайте issue в GitHub с описанием проблемы и логами
