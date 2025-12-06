# Инструкция по установке и запуску

## Предварительные требования

### Для Docker (Рекомендуется)
1. Docker и Docker Compose
2. API ключи (см. ниже)

### Для локальной установки
1. Python 3.10-3.13 (рекомендуется 3.11 или 3.12 для лучшей совместимости)
   - **Примечание**: Для Python 3.13 требуется установка torch через PyTorch index
2. PostgreSQL 14+
3. Redis (опционально, для кэширования)
4. API ключи:
   - Anthropic API key (для Claude)
   - Telegram Bot Token (для Telegram бота)

## Установка

### Вариант 1: Docker (Рекомендуется)

См. [DOCKER.md](DOCKER.md) для подробных инструкций.

```bash
# 1. Клонируйте репозиторий
git clone <repo-url>
cd "хактон 3-д принтер"

# 2. Настройте .env файл
cp .env.example .env
# Отредактируйте .env и заполните ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN

# 3. Запустите все сервисы
docker-compose up -d

# 4. Инициализируйте базу данных
docker-compose exec app alembic upgrade head

# 5. Готово! API доступен на http://localhost:8000
```

### Вариант 2: Локальная установка

### 1. Клонирование и настройка окружения

```bash
# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
# Для Python 3.13 используйте скрипт:
./requirements-setup.sh

# Или вручную:
# 1. Сначала установите PyTorch (для Python 3.13)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 2. Затем остальные зависимости
pip install -r requirements.txt
```

### 2. Настройка базы данных

```bash
# Создайте базу данных PostgreSQL
createdb printer_ai

# Или через psql:
psql -U postgres
CREATE DATABASE printer_ai;
```

### 3. Настройка переменных окружения

```bash
# Скопируйте пример файла окружения
cp .env.example .env

# Отредактируйте .env и заполните необходимые значения:
# - ANTHROPIC_API_KEY
# - TELEGRAM_BOT_TOKEN
# - Настройки базы данных
# - Настройки принтера (Klipper/OctoPrint)
```

### 4. Инициализация базы данных

```bash
# Создайте миграции
alembic revision --autogenerate -m "Initial migration"

# Примените миграции
alembic upgrade head
```

### 5. Инициализация ChromaDB

ChromaDB автоматически создастся при первом запуске в директории `data/chroma`.

## Запуск

### Telegram Bot

```bash
python -m ui.telegram_bot
```

### Streamlit Dashboard

```bash
streamlit run ui/streamlit_dashboard.py
```

Откройте браузер и перейдите на http://localhost:8501

### REST API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступен на http://localhost:8000
Документация: http://localhost:8000/docs

## Структура проекта

```
.
├── api/                    # REST API (FastAPI)
│   └── main.py
├── ui/                     # User Interface
│   ├── telegram_bot.py    # Telegram бот
│   └── streamlit_dashboard.py  # Web dashboard
├── orchestration/          # LangGraph Orchestration
│   ├── graph.py           # Основной граф
│   ├── supervisor.py      # Supervisor агент
│   ├── router.py          # Роутер
│   └── executor.py        # Исполнитель
├── agents/                 # Tool/Agent Layer
│   ├── code_interpreter/  # G-code анализ
│   ├── rag_engine/        # RAG поиск
│   ├── vision/            # Анализ изображений
│   └── hardware/          # Управление принтером
├── data/                   # Data Persistence
│   ├── postgres/          # PostgreSQL модели
│   ├── chroma_db.py       # ChromaDB
│   ├── redis_cache.py     # Redis
│   └── storage.py         # File storage
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости
└── README.md              # Документация
```

## Использование

### Через Telegram

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Задавайте вопросы или отправляйте файлы

Примеры запросов:
- "Какой статус принтера?"
- "Проанализируй этот G-code" (прикрепите файл)
- "Что делать при засорении сопла?"

### Через REST API

```bash
# Отправить сообщение
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Какой статус принтера?"}'

# Получить статус
curl http://localhost:8000/status

# Установить температуру
curl -X POST http://localhost:8000/temperature \
  -H "Content-Type: application/json" \
  -d '{"bed_temp": 60, "nozzle_temp": 200}'
```

### Через Streamlit Dashboard

1. Откройте http://localhost:8501
2. Используйте вкладки для навигации:
   - **Мониторинг**: Просмотр статуса принтера
   - **Управление**: Управление принтером
   - **Анализ**: Анализ G-code и изображений
   - **База знаний**: Поиск в базе знаний

## Добавление знаний в базу

```python
from agents.rag_engine.tool import rag_engine_tool

rag_engine_tool.add_knowledge(
    text="Ваш текст с информацией о 3D-печати",
    metadata={"source": "manual", "topic": "troubleshooting"}
)
```

## Устранение неполадок

### Ошибка подключения к PostgreSQL
- Проверьте, что PostgreSQL запущен
- Проверьте настройки в `.env`
- Убедитесь, что база данных создана

### Ошибка подключения к принтеру
- Проверьте URL API в `.env`
- Убедитесь, что Klipper/OctoPrint доступны
- Проверьте API ключи

### Ошибки с ChromaDB
- Убедитесь, что директория `data/chroma` доступна для записи
- Проверьте права доступа

## Разработка

Для разработки рекомендуется:

1. Использовать виртуальное окружение
2. Включить DEBUG режим в `.env`
3. Использовать `--reload` для FastAPI
4. Проверять логи в `logs/app.log`

## Поддержка

При возникновении проблем проверьте:
- Логи приложения
- Настройки в `.env`
- Версии зависимостей в `requirements.txt`

