# Orchestration Layer

## Новый подход с Supervisor

Orchestration Layer использует современный подход с LangChain и LangGraph:

### Архитектура

```
User Input → Supervisor (Claude) → Tool Selection → ToolNode → Results → Supervisor → Formatter → Response
```

### Компоненты

1. **Supervisor** (`supervisor.py`) - Основной граф LangGraph
   - Анализирует intent пользователя
   - Выбирает нужные инструменты
   - Управляет потоком выполнения

2. **State** (`state.py`) - Состояние графа
   - `messages` - История сообщений (LangChain BaseMessage)
   - `response_formatted` - Флаг форматирования ответа

3. **Tools** (`tools.py`) - Все инструменты как LangChain StructuredTool
   - GcodeAnalyzer (4 функции)
   - RAGEngine (1 функция)
   - VisionPipeline (2 функции)
   - HardwareInterface (8 функций)

4. **Config** (`config.py`) - Конфигурация
   - SYSTEM_PROMPT
   - LLM_CONFIG

### Использование

```python
from orchestration.supervisor import Supervisor

supervisor = Supervisor()
response = await supervisor.run("Какой статус принтера?", session_id="user123")
```

### Инструменты

Все инструменты автоматически доступны Claude через `bind_tools()`. Claude сам решает, какие инструменты использовать на основе запроса пользователя.

### Feedback Loop

После выполнения инструментов результаты возвращаются в Supervisor, который может:
- Использовать результаты для генерации ответа
- Вызвать дополнительные инструменты при необходимости
- Форматировать финальный ответ

