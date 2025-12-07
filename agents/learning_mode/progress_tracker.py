"""Отслеживание прогресса обучения"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from data.postgres.repository import LessonRepository
from data.postgres.models import UserLesson, Lesson
from agents.learning_mode.lessons import Lesson as LessonData, LESSONS


class ProgressTracker:
    """Трекер прогресса обучения"""
    
    def __init__(self, db: Session):
        self.db = db
        self.lesson_repo = LessonRepository()
    
    def get_user_progress(self, user_id: int) -> Dict:
        """Получить прогресс пользователя"""
        # Получаем все уроки из БД
        all_lessons = self.lesson_repo.get_all_lessons(self.db)
        
        # Получаем пройденные уроки пользователя
        user_lessons = self.lesson_repo.get_user_lessons(self.db, user_id)
        completed_lesson_ids = {
            ul.lesson.lesson_id for ul in user_lessons if ul.completed
        }
        
        # Находим текущий урок (первый непройденный)
        current_lesson = None
        for lesson in all_lessons:
            if lesson.lesson_id not in completed_lesson_ids:
                # Проверяем prerequisites (упрощенная версия)
                current_lesson = {
                    "id": lesson.lesson_id,
                    "title": lesson.title,
                    "level": lesson.level
                }
                break
        
        total_lessons = len(all_lessons)
        progress_percent = (len(completed_lesson_ids) / total_lessons * 100) if total_lessons > 0 else 0
        
        return {
            "user_id": user_id,
            "completed_lessons": list(completed_lesson_ids),
            "current_lesson": current_lesson,
            "total_lessons": total_lessons,
            "progress_percent": round(progress_percent, 2)
        }
    
    def mark_lesson_complete(
        self, 
        user_id: int, 
        lesson_id: str, 
        score: Optional[int] = None,
        time_spent_minutes: int = 0
    ) -> Dict:
        """Отметить урок как пройденный"""
        user_lesson = self.lesson_repo.mark_lesson_complete(
            self.db, user_id, lesson_id, score, time_spent_minutes
        )
        
        return {
            "user_id": user_id,
            "lesson_id": lesson_id,
            "completed": user_lesson.completed,
            "score": user_lesson.score,
            "time_spent_minutes": user_lesson.time_spent_minutes,
            "completed_at": user_lesson.completed_at
        }
    
    def get_next_lesson(self, user_id: int) -> Optional[Dict]:
        """Получить следующий урок для пользователя"""
        progress = self.get_user_progress(user_id)
        completed = set(progress["completed_lessons"])
        
        # Получаем все уроки из БД
        all_lessons = self.lesson_repo.get_all_lessons(self.db)
        
        # Сортируем уроки по уровню и ищем первый непройденный
        sorted_lessons = sorted(all_lessons, key=lambda l: (l.level, l.id))
        
        for lesson in sorted_lessons:
            if lesson.lesson_id not in completed:
                # Упрощенная проверка prerequisites - можно улучшить
                return {
                    "id": lesson.lesson_id,
                    "title": lesson.title,
                    "level": lesson.level,
                    "description": lesson.content[:200] if lesson.content else "",
                    "estimated_time_minutes": lesson.estimated_time_minutes
                }
        
        return None

