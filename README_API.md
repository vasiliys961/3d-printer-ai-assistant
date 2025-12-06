# API Документация

## Два варианта API

### 1. Полный API (`api/main.py`)
Расширенная версия с поддержкой всех функций:
- Управление принтером (температура, печать)
- Загрузка файлов
- Полная интеграция с графом оркестрации

### 2. Упрощенный API (`api/main_simple.py`)
Простая версия для базового чата:
- Создание сессий
- Чат с агентом
- История диалогов
- Анализ G-code

## Запуск

### Упрощенный API (рекомендуется для начала):
```bash
python api/main_simple.py
```

### Полный API:
```bash
python api/main.py
```

Или через uvicorn:
```bash
uvicorn api.main_simple:app --reload --port 8000
```

## Эндпоинты

### POST /sessions
Создать новую сессию
```json
{
  "user_id": 1,
  "printer_model": "Ender 3",
  "material": "PLA"
}
```

### POST /chat
Отправить сообщение
```json
{
  "session_id": 1,
  "message": "Почему мой пластик в воздухе висит?"
}
```

### GET /sessions/{session_id}/history
Получить историю диалога

### POST /upload-gcode
Загрузить и проанализировать G-code файл
- Form-data: `file` (G-code файл), `material` (PLA/PETG/ABS)

### GET /health
Проверка здоровья приложения
