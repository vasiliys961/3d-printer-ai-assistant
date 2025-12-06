# Docker Setup

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните необходимые переменные:
```bash
cp .env.example .env
```

2. Запустите все сервисы:
```bash
docker-compose up -d
```

3. Инициализируйте базу данных:
```bash
docker-compose exec app alembic upgrade head
```

4. Приложение будет доступно на:
   - REST API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

## Сервисы

### PostgreSQL
- Порт: 5432
- Пользователь: 3dp_user
- Пароль: secure_password
- База данных: 3d_print_assistant

### Redis
- Порт: 6379
- Используется для кэширования

### App
- Порт: 8000
- Основное приложение

## Команды

### Запуск
```bash
docker-compose up -d
```

### Остановка
```bash
docker-compose down
```

### Просмотр логов
```bash
docker-compose logs -f app
```

### Выполнение команд в контейнере
```bash
docker-compose exec app bash
docker-compose exec app python -m ui.telegram_bot
```

### Пересборка образа
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Очистка данных
```bash
docker-compose down -v  # Удалит все volumes
```

## Разработка

Для разработки создайте `docker-compose.override.yml`:
```yaml
version: '3.8'

services:
  app:
    volumes:
      - .:/app
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DEBUG: "True"
```

## Переменные окружения

Основные переменные (устанавливаются в `.env`):
- `ANTHROPIC_API_KEY` - API ключ Claude
- `TELEGRAM_BOT_TOKEN` - Токен Telegram бота
- `KLIPPER_API_URL` - URL Klipper/Moonraker API
- `OCTOPRINT_API_URL` - URL OctoPrint API
- `OCTOPRINT_API_KEY` - API ключ OctoPrint

## Volumes

- `postgres_data` - данные PostgreSQL
- `redis_data` - данные Redis
- `./data` - ChromaDB, файлы хранилища
- `./logs` - логи приложения

## Health Checks

PostgreSQL и Redis имеют health checks, поэтому приложение будет ждать их готовности перед запуском.

## Troubleshooting

### Проблемы с подключением к БД
```bash
docker-compose exec postgres psql -U 3dp_user -d 3d_print_assistant
```

### Просмотр логов PostgreSQL
```bash
docker-compose logs postgres
```

### Перезапуск сервиса
```bash
docker-compose restart app
```

