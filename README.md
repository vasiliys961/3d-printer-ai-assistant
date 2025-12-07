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

## База знаний

Проект включает расширенную базу знаний по 3D-печати:

- **Материалы**: PLA, PETG, ABS, TPU, ASA, PC, Nylon (7 документов)
- **Troubleshooting**: warping, stringing, layer shift, under/over extrusion, bed adhesion, elephant foot, zits/blobs (8 документов)
- **Профили принтеров**: Ender 3, Prusa i3, Bamboo Lab X1, Voron, RatRig (5 документов)
- **G-code команды**: температура, движение, выравнивание стола, продвинутые команды (4 документа)
- **Калибровка**: bed leveling, flow rate, temperature tower, retraction test, speed test (5 документов)
- **Настройки слайсеров**: Cura, PrusaSlicer (2 документа)

**Всего: ~32 документа**

Подробнее см. [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md)

## Креативные функции

### Режим обучения
Пошаговые уроки для начинающих и продвинутых пользователей с отслеживанием прогресса.

### Подбор проектов
Рекомендательная система для выбора проектов для печати на основе навыков пользователя.

### Геймификация
Система достижений, уровней и таблицы лидеров для мотивации.

Подробнее см. [CREATIVE_FEATURES.md](CREATIVE_FEATURES.md)

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

## Мультиагентная архитектура

Проект поддерживает две архитектуры агентов:

1. **Supervisor-based** (по умолчанию) - LangGraph с автоматическим выбором инструментов
2. **MultiModel** - детальная мультиагентная система с 4 ролями

Подробное описание см. в [AGENT_ARCHITECTURES.md](AGENT_ARCHITECTURES.md)

### Особенности MultiModel архитектуры:

- **Аналитик** - анализирует запрос, разбивает на подзадачи (внутренний)
- **Консультант** - единственный, кто общается с пользователем
- **Редактор** - упрощает для новичков (внутренняя валидация)
- **Проверяющий** - оценивает качество в JSON (внутренняя валидация)

**Важно:** В MultiModel архитектуре только Консультант общается с пользователем напрямую. Остальные агенты работают внутренне для анализа и валидации.

## Тестирование

Для проверки работоспособности мультиагентной системы:

```bash
python test_multi_model_agent.py
```

Тесты проверяют:
- Работу Аналитика (разбивка на подзадачи, формирование ключевых слов)
- Работу Консультанта (структурированный ответ в строгом формате)
- Полный пайплайн обработки запроса
- Оценку качества ответов (QA Checker с метриками correctness, completeness, clarity)

Все тесты должны проходить успешно для подтверждения работоспособности системы.

## Воспроизводимость результатов

Для обеспечения воспроизводимости результатов:

1. **Установка зависимостей:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройка окружения:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env и заполните необходимые API ключи
   ```

3. **Инициализация БД:**
   ```bash
   alembic upgrade head
   ```

4. **Загрузка базы знаний:**
   ```bash
   python scripts/ingest_knowledge.py
   ```

5. **Проверка работоспособности:**
   ```bash
   python test_multi_model_agent.py
   ```

Все тесты должны проходить успешно. Для детального описания архитектуры см. [ARCHITECTURE.md](ARCHITECTURE.md) и [AGENT_ARCHITECTURES.md](AGENT_ARCHITECTURES.md).

