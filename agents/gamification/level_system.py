"""Система уровней"""
from typing import Dict
from sqlalchemy.orm import Session
from data.postgres.repository import UserProgressRepository


class LevelSystem:
    """Система уровней и опыта"""
    
    EXP_PER_LEVEL = 100  # Опыт для каждого уровня
    
    def __init__(self, db: Session):
        self.db = db
        self.progress_repo = UserProgressRepository()
    
    def get_user_level(self, user_id: int) -> Dict:
        """Получить уровень пользователя"""
        progress = self.progress_repo.get_or_create_progress(self.db, user_id)
        experience_to_next = self.EXP_PER_LEVEL - (progress.experience % self.EXP_PER_LEVEL)
        return {
            "user_id": user_id,
            "level": progress.level,
            "experience": progress.experience,
            "experience_to_next": experience_to_next
        }
    
    def add_experience(self, user_id: int, exp: int) -> Dict:
        """Добавить опыт пользователю"""
        # Получаем текущий прогресс для проверки уровня до добавления опыта
        old_progress = self.progress_repo.get_progress(self.db, user_id)
        old_level = old_progress.level if old_progress else 1
        
        # Добавляем опыт
        progress = self.progress_repo.add_experience(self.db, user_id, exp)
        experience_to_next = self.EXP_PER_LEVEL - (progress.experience % self.EXP_PER_LEVEL)
        
        return {
            "user_id": user_id,
            "level": progress.level,
            "experience": progress.experience,
            "experience_to_next": experience_to_next,
            "leveled_up": progress.level > old_level
        }
    
    def calculate_level(self, experience: int) -> int:
        """Рассчитать уровень на основе опыта"""
        return (experience // self.EXP_PER_LEVEL) + 1

