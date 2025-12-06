# Быстрый старт

## 1. Проверка окружения

```bash
# Убедитесь, что вы в директории проекта
cd "/Users/maxmobiles.ru/Desktop/хактон 3-д принтер"

# Активируйте виртуальное окружение
source venv/bin/activate
```

## 2. Установка зависимостей

```bash
# Установите зависимости
pip install -r requirements.txt

# Или используйте скрипт для Python 3.13
./requirements-setup.sh
```

## 3. Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env и вставьте ваши ключи:
# - OPENROUTER_API_KEY=sk-or-...
# - DATABASE_URL=postgresql://...
```

## 4. Проверка подключения к БД

```bash
# Примените миграции (если еще не применены)
alembic upgrade head
```

## 5. Запуск API

### Упрощенный API (рекомендуется):
```bash
python api/main_simple.py
```

### Полный API:
```bash
python api/main.py
```

### Или через uvicorn:
```bash
uvicorn api.main_simple:app --reload --port 8000
```

## 6. Проверка работы

Откройте в браузере:
- http://localhost:8000/health
- http://localhost:8000/docs (Swagger UI)

## Полезные команды

```bash
# Проверить статус миграций
alembic current

# Создать новую миграцию
alembic revision --autogenerate -m "описание изменений"

# Просмотреть логи
tail -f logs/app.log
```

