# Креативные функции

## Режим обучения

Система пошагового обучения с уроками разного уровня сложности.

### API Endpoints

- `GET /learning/lessons` - список всех уроков
- `GET /learning/lessons/{lesson_id}` - детали урока
- `POST /learning/lessons/{lesson_id}/complete` - отметить урок как пройденный
- `GET /learning/progress` - прогресс пользователя

### Уровни обучения

- **Beginner** - базовые уроки для начинающих
- **Intermediate** - продвинутые темы
- **Advanced** - экспертный уровень

### Пример использования

```python
# Получить все уроки
GET /learning/lessons

# Получить урок
GET /learning/lessons/lesson_001

# Отметить как пройденный
POST /learning/lessons/lesson_001/complete
{
  "user_id": 1,
  "score": 85
}
```

## Подбор проектов

Рекомендательная система для выбора проектов для печати на основе навыков пользователя.

### API Endpoints

- `GET /projects/recommend` - получить рекомендации
- `GET /projects/{project_id}` - детали проекта
- `POST /projects/{project_id}/start` - начать проект

### Параметры рекомендаций

- `difficulty` - сложность (easy, medium, hard)
- `material` - требуемый материал
- `max_time_hours` - максимальное время

### Пример использования

```python
# Получить рекомендации
GET /projects/recommend?user_id=1&difficulty=easy&material=PLA

# Получить детали проекта
GET /projects/project_001

# Начать проект
POST /projects/project_001/start
{
  "user_id": 1
}
```

## Геймификация

Система достижений, уровней и таблицы лидеров для мотивации пользователей.

### API Endpoints

- `GET /gamification/progress` - прогресс пользователя (уровень, опыт)
- `GET /gamification/achievements` - список достижений
- `GET /gamification/leaderboard` - таблица лидеров

### Достижения

- Первая печать
- 10 успешных печатей
- Решение проблемы warping
- Прохождение всех базовых уроков
- Эксперт по G-code

### Система уровней

- Опыт начисляется за действия (печать, уроки, решение проблем)
- Каждый уровень требует 100 опыта
- Уровень = (опыт / 100) + 1

### Пример использования

```python
# Получить прогресс
GET /gamification/progress?user_id=1

# Получить достижения
GET /gamification/achievements?user_id=1

# Таблица лидеров
GET /gamification/leaderboard?limit=10
```

## Интеграция

Все креативные функции интегрированы с MultiModelAgent и могут использоваться в ответах Консультанта.

