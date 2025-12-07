# Тесты для 3D Printer AI Assistant

## Структура

- `tests/unit/` - Unit тесты для отдельных компонентов
- `tests/integration/` - Integration тесты для взаимодействия компонентов
- `tests/e2e/` - End-to-end тесты для полных сценариев

## Запуск тестов

```bash
# Все тесты
pytest

# Только unit тесты
pytest tests/unit/

# Только integration тесты
pytest tests/integration/

# С покрытием кода
pytest --cov=. --cov-report=html

# Только быстрые тесты (без slow)
pytest -m "not slow"
```

## Фикстуры

- `test_db_session` - Тестовая БД сессия (in-memory SQLite)
- `mock_llm` - Мок LLM для тестирования без реальных вызовов
- `sample_gcode` - Пример G-code для тестов
- `sample_kb_document` - Пример документа базы знаний

