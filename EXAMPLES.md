# Примеры использования 3D Printer AI Assistant

## API Примеры

### 1. Создание сессии и отправка сообщения

```bash
# 1. Создать сессию
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "printer_model": "Ender 3",
    "material": "PLA"
  }'

# Ответ:
# {"session_id": 1, "status": "created"}

# 2. Отправить сообщение
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "message": "Почему мой первый слой не прилипает к столу?"
  }'
```

### 2. Анализ G-code файла

```bash
curl -X POST http://localhost:8000/upload-gcode \
  -F "file=@my_print.gcode" \
  -F "material=PLA"
```

### 3. Получение истории диалога

```bash
curl http://localhost:8000/sessions/1/history
```

### 4. Режим обучения

```bash
# Получить прогресс обучения
curl "http://localhost:8000/learning/progress?user_id=1"

# Отметить урок как пройденный
curl -X POST http://localhost:8000/learning/complete/lesson_001 \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "score": 85
  }'
```

### 5. Рекомендации проектов

```bash
curl "http://localhost:8000/projects/recommend?user_id=1&difficulty=easy&material=PLA"
```

### 6. Геймификация

```bash
# Получить прогресс пользователя
curl "http://localhost:8000/gamification/progress?user_id=1"

# Получить достижения
curl "http://localhost:8000/gamification/achievements?user_id=1"

# Получить таблицу лидеров
curl "http://localhost:8000/gamification/leaderboard?limit=10"
```

## Python Примеры

### Использование MultiModelAgent напрямую

```python
from agents.multi_model_agent import MultiModelAgent
from database import SessionLocal

# Создаем агента
agent = MultiModelAgent(provider="openrouter")

# Получаем сессию БД
db = SessionLocal()

# Отправляем сообщение
response = await agent.run(
    user_message="Как настроить температуру для PETG?",
    session_id=1,
    db=db
)

print(response)
```

### Использование RAG Engine

```python
from agents.rag_engine.engine import RAGEngine

# Инициализируем RAG engine
rag = RAGEngine()

# Загружаем базу знаний
rag.ingest_knowledge_base("./data/knowledge_base")

# Выполняем поиск
result = await rag.search("Как решить проблему warping?", top_k=5)

print(f"Найдено результатов: {result.total_results}")
for i, chunk in enumerate(result.relevant_chunks, 1):
    print(f"{i}. {chunk[:100]}...")
    print(f"   Источник: {result.sources[i-1].get('source_url', 'N/A')}")
```

### Использование G-code Analyzer

```python
from agents.code_interpreter.tool import CodeInterpreterTool

analyzer = CodeInterpreterTool()

# Анализируем G-code
with open("print.gcode", "r") as f:
    gcode_content = f.read()

result = analyzer.analyze_gcode(
    gcode_content=gcode_content,
    material="PLA",
    printer_profile="Ender3"
)

print(f"Валидность: {result['valid']}")
print(f"Ошибки: {result['errors']}")
print(f"Предупреждения: {result['warnings']}")
print(f"Метрики: {result['metrics']}")
print(f"Рекомендации: {result['recommendations']}")
```

## Примеры вопросов для ассистента

### Вопросы о материалах

- "Какая температура нужна для PETG?"
- "В чем разница между PLA и ABS?"
- "Какой материал лучше для деталей на улице?"

### Вопросы о проблемах печати

- "Почему мой пластик не прилипает к столу?"
- "Что делать, если слои смещаются?"
- "Как избавиться от stringing?"

### Вопросы о настройках

- "Как откалибровать стол принтера?"
- "Какие настройки слайсера для PLA?"
- "Как настроить retraction?"

### Вопросы о G-code

- "Что означает команда M104?"
- "Как проверить G-code на ошибки?"
- "Какие параметры влияют на скорость печати?"

## Интеграция с Telegram ботом

```python
from ui.telegram_bot import TelegramBot

bot = TelegramBot(token="YOUR_TELEGRAM_BOT_TOKEN")
bot.start_polling()
```

## Использование Streamlit Dashboard

```bash
streamlit run ui/streamlit_dashboard.py
```

Откройте браузер на `http://localhost:8501` для доступа к dashboard.
