"""Таблица лидеров"""
from typing import List, Dict
from sqlalchemy.orm import Session
from data.postgres.repository import UserProgressRepository


class Leaderboard:
    """Таблица лидеров"""
    
    def __init__(self, db: Session):
        self.db = db
        self.progress_repo = UserProgressRepository()
    
    def get_leaderboard(self, limit: int = 10, offset: int = 0) -> Dict:
        """Получить таблицу лидеров с пагинацией"""
        leaderboard, total = self.progress_repo.get_leaderboard(self.db, limit, offset)
        return {
            "leaderboard": leaderboard,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_user_rank(self, user_id: int) -> Dict:
        """Получить ранг пользователя"""
        return self.progress_repo.get_user_rank(self.db, user_id)

