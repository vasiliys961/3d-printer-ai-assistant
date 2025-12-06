# 3D Printer AI Assistant

Интеллектуальный ассистент для управления 3D-принтерами с использованием LangGraph, Claude AI и мультиагентной архитектуры.

## Архитектура

Приложение состоит из 4 основных слоев:

1. **User Interface Layer** - Telegram Bot, Streamlit Dashboard, REST API
2. **Orchestration Layer** - LangGraph с Supervisor, Router, Executor
3. **Tool/Agent Layer** - Code Interpreter, RAG Engine, Vision Pipeline, Hardware Interface
4. **Data Persistence Layer** - PostgreSQL, ChromaDB, Redis, LocalFS/S3

Подробное описание архитектуры см. в [ARCHITECTURE.md](ARCHITECTURE.md)

## Установка

### Docker (Рекомендуется)

Подробные инструкции см. в [DOCKER.md](DOCKER.md)

```bash
# 1. Скопируйте .env.example в .env и заполните переменные
cp .env.example .env

# 2. Запустите все сервисы
docker-compose up -d

# 3. Инициализируйте базу данных
docker-compose exec app alembic upgrade head

# 4. Приложение доступно на http://localhost:8000
```

### Локальная установка

Подробные инструкции по установке и настройке см. в [SETUP.md](SETUP.md)

Краткая инструкция:

1. Клонируйте репозиторий
2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

3. Настройте `.env` файл

4. Инициализируйте базы данных:
```bash
alembic upgrade head
```

## Запуск

### Docker

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f app

# Выполнение команд в контейнере
docker-compose exec app python -m ui.telegram_bot
docker-compose exec app streamlit run ui/streamlit_dashboard.py
```

### Локально

#### Telegram Bot
```bash
python -m ui.telegram_bot
```

#### Streamlit Dashboard
```bash
streamlit run ui/streamlit_dashboard.py
```

#### REST API
```bash
uvicorn api.main:app --reload
```

## Структура проекта

```
.
├── api/                    # REST API (FastAPI)
├── ui/                     # User Interface (Telegram, Streamlit)
├── orchestration/          # LangGraph Orchestration Layer
├── agents/                 # Tool/Agent Layer
│   ├── code_interpreter/  # G-code анализ
│   ├── rag_engine/        # Knowledge retrieval
│   ├── vision/            # Image analysis
│   └── hardware/         # Printer control
├── data/                  # Data Persistence Layer
│   ├── postgres/          # PostgreSQL models
│   ├── chroma/            # ChromaDB
│   └── storage/           # File storage
└── config.py              # Конфигурация

```

## Основные возможности

- Анализ и валидация G-code
- Поиск по базе знаний (RAG)
- Анализ изображений печати (YOLOv8 + Claude Vision)
- Управление принтером через Klipper/OctoPrint API
- Мультиагентная обработка запросов через LangGraph

