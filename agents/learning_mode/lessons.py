"""Структура уроков для режима обучения"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Lesson:
    """Урок для обучения"""
    id: str
    title: str
    level: str  # beginner, intermediate, advanced
    content: str
    exercises: List[Dict] = field(default_factory=list)
    quiz: List[Dict] = field(default_factory=list)
    estimated_time_minutes: int = 15
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class LessonProgress:
    """Прогресс по уроку"""
    lesson_id: str
    user_id: int
    completed: bool = False
    score: Optional[int] = None
    time_spent_minutes: int = 0


# Базовые уроки
LESSONS = [
    Lesson(
        id="lesson_001",
        title="Введение в 3D-печать",
        level="beginner",
        content="Основы 3D-печати: что это такое, как работает, основные термины.",
        exercises=[{"type": "quiz", "question": "Что такое FDM?", "options": ["Fused Deposition Modeling", "Fast Direct Manufacturing"], "correct": 0}],
        estimated_time_minutes=10
    ),
    Lesson(
        id="lesson_002",
        title="Выбор материала: PLA",
        level="beginner",
        content="PLA - самый популярный материал. Температура, настройки, особенности.",
        prerequisites=["lesson_001"],
        estimated_time_minutes=15
    ),
    Lesson(
        id="lesson_003",
        title="Калибровка стола",
        level="beginner",
        content="Как правильно откалибровать стол принтера для хорошей адгезии.",
        prerequisites=["lesson_001"],
        estimated_time_minutes=20
    ),
    Lesson(
        id="lesson_004",
        title="Решение проблемы warping",
        level="intermediate",
        content="Почему углы поднимаются и как это исправить.",
        prerequisites=["lesson_001", "lesson_002"],
        estimated_time_minutes=15
    ),
    Lesson(
        id="lesson_005",
        title="G-code команды",
        level="intermediate",
        content="Основные G-code команды: M104, M109, G28, G29 и их использование.",
        prerequisites=["lesson_001"],
        estimated_time_minutes=25
    ),
    Lesson(
        id="lesson_006",
        title="Продвинутые материалы: PETG и ABS",
        level="advanced",
        content="Работа с PETG и ABS: настройки, особенности, проблемы.",
        prerequisites=["lesson_002", "lesson_004"],
        estimated_time_minutes=30
    )
]

