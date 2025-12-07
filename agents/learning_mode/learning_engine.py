"""Движок обучения с уроками"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from agents.learning_mode.lessons import Lesson, LESSONS
from agents.learning_mode.progress_tracker import ProgressTracker


class LearningEngine:
    """Движок режима обучения"""
    
    def __init__(self, db: Session):
        self.db = db
        self.progress_tracker = ProgressTracker(db)
    
    def get_all_lessons(self, level: Optional[str] = None) -> List[Lesson]:
        """Получить все уроки, опционально отфильтрованные по уровню"""
        if level:
            return [lesson for lesson in LESSONS if lesson.level == level]
        return LESSONS
    
    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Получить урок по ID"""
        for lesson in LESSONS:
            if lesson.id == lesson_id:
                return lesson
        return None
    
    def get_user_progress(self, user_id: int) -> Dict:
        """Получить прогресс пользователя"""
        return self.progress_tracker.get_user_progress(user_id)
    
    def complete_lesson(self, user_id: int, lesson_id: str, score: Optional[int] = None):
        """Отметить урок как пройденный"""
        self.progress_tracker.mark_lesson_complete(user_id, lesson_id, score)
    
    def get_next_lesson(self, user_id: int) -> Optional[Lesson]:
        """Получить следующий урок для пользователя"""
        return self.progress_tracker.get_next_lesson(user_id)

