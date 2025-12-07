"""Тесты режима обучения"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.learning_mode.learning_engine import LearningEngine
from agents.learning_mode.lessons import LESSONS


def test_learning_mode():
    """Тест режима обучения"""
    print("🧪 Тестирование режима обучения...")
    
    # Создаем mock DB session
    class MockDB:
        pass
    
    engine = LearningEngine(MockDB())
    
    # Получить все уроки
    all_lessons = engine.get_all_lessons()
    print(f"✅ Всего уроков: {len(all_lessons)}")
    
    # Получить уроки по уровню
    beginner_lessons = engine.get_all_lessons(level="beginner")
    print(f"✅ Базовых уроков: {len(beginner_lessons)}")
    
    # Получить конкретный урок
    lesson = engine.get_lesson("lesson_001")
    if lesson:
        print(f"✅ Урок найден: {lesson.title}")
    
    # Прогресс пользователя
    progress = engine.get_user_progress(1)
    print(f"✅ Прогресс пользователя: {progress}")
    
    print("✅ Тест режима обучения пройден!")


if __name__ == "__main__":
    test_learning_mode()

