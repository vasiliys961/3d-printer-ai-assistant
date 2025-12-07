"""Система достижений"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from data.postgres.repository import AchievementRepository
from data.postgres.models import Print, Message, UserLesson, Lesson


class AchievementSystem:
    """Система достижений"""
    
    ACHIEVEMENTS = [
        {"id": "first_print", "name": "Первая печать", "description": "Успешно завершите первую печать", "icon": "🎯"},
        {"id": "ten_prints", "name": "Десять печатей", "description": "Завершите 10 успешных печатей", "icon": "🏆"},
        {"id": "warping_solver", "name": "Решатель warping", "description": "Решите проблему warping", "icon": "🔧"},
        {"id": "basic_lessons", "name": "Базовые знания", "description": "Пройдите все базовые уроки", "icon": "📚"},
        {"id": "gcode_expert", "name": "Эксперт G-code", "description": "Изучите все G-code команды", "icon": "💻"}
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.achievement_repo = AchievementRepository()
        self._initialize_achievements()
    
    def _initialize_achievements(self):
        """Инициализировать достижения в БД"""
        for achievement in self.ACHIEVEMENTS:
            self.achievement_repo.get_or_create_achievement(
                self.db,
                achievement["id"],
                achievement["name"],
                achievement["description"],
                achievement["icon"]
            )
    
    def get_all_achievements(self) -> List[Dict]:
        """Получить все достижения"""
        achievements = self.achievement_repo.get_all_achievements(self.db)
        return [
            {
                "id": a.achievement_id,
                "name": a.name,
                "description": a.description,
                "icon": a.icon
            }
            for a in achievements
        ]
    
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Получить достижения пользователя"""
        return self.achievement_repo.get_user_achievements(self.db, user_id)
    
    def check_and_award(self, user_id: int, achievement_id: str) -> Optional[Dict]:
        """Проверить и наградить достижением"""
        # Проверяем, есть ли уже это достижение
        if self.achievement_repo.has_achievement(self.db, user_id, achievement_id):
            return None
        
        # Проверяем условия для каждого достижения
        if achievement_id == "first_print":
            if self._check_first_print(user_id):
                user_achievement = self.achievement_repo.award_achievement(self.db, user_id, achievement_id)
                if user_achievement:
                    return {"achievement_id": achievement_id, "awarded": True}
        
        elif achievement_id == "ten_prints":
            if self._check_ten_prints(user_id):
                user_achievement = self.achievement_repo.award_achievement(self.db, user_id, achievement_id)
                if user_achievement:
                    return {"achievement_id": achievement_id, "awarded": True}
        
        elif achievement_id == "warping_solver":
            if self._check_warping_solver(user_id):
                user_achievement = self.achievement_repo.award_achievement(self.db, user_id, achievement_id)
                if user_achievement:
                    return {"achievement_id": achievement_id, "awarded": True}
        
        elif achievement_id == "basic_lessons":
            if self._check_basic_lessons(user_id):
                user_achievement = self.achievement_repo.award_achievement(self.db, user_id, achievement_id)
                if user_achievement:
                    return {"achievement_id": achievement_id, "awarded": True}
        
        elif achievement_id == "gcode_expert":
            if self._check_gcode_expert(user_id):
                user_achievement = self.achievement_repo.award_achievement(self.db, user_id, achievement_id)
                if user_achievement:
                    return {"achievement_id": achievement_id, "awarded": True}
        
        return None
    
    def _check_first_print(self, user_id: int) -> bool:
        """Проверить, есть ли первая успешная печать"""
        successful_prints = self.db.query(func.count(Print.id)).filter(
            Print.user_id == user_id,
            Print.success == True
        ).scalar()
        return successful_prints >= 1
    
    def _check_ten_prints(self, user_id: int) -> bool:
        """Проверить, есть ли 10 успешных печатей"""
        successful_prints = self.db.query(func.count(Print.id)).filter(
            Print.user_id == user_id,
            Print.success == True
        ).scalar()
        return successful_prints >= 10
    
    def _check_warping_solver(self, user_id: int) -> bool:
        """Проверить, решена ли проблема warping"""
        # Ищем сообщения, где упоминается warping и решение
        messages = self.db.query(Message).join(
            Message.session
        ).filter(
            Message.session.has(user_id=user_id),
            Message.role == "assistant"
        ).all()
        
        for message in messages:
            content_lower = message.content.lower()
            if "warping" in content_lower or "деформация" in content_lower:
                if any(word in content_lower for word in ["решен", "решить", "исправлен", "устранен"]):
                    return True
        return False
    
    def _check_basic_lessons(self, user_id: int) -> bool:
        """Проверить, пройдены ли все базовые уроки"""
        basic_lessons = self.db.query(Lesson).filter(Lesson.level == "beginner").all()
        if not basic_lessons:
            return False
        
        completed_lessons = self.db.query(func.count(UserLesson.id)).join(
            Lesson, UserLesson.lesson_id == Lesson.id
        ).filter(
            UserLesson.user_id == user_id,
            UserLesson.completed == True,
            Lesson.level == "beginner"
        ).scalar()
        
        return completed_lessons >= len(basic_lessons)
    
    def _check_gcode_expert(self, user_id: int) -> bool:
        """Проверить, изучены ли все G-code команды"""
        # Проверяем, использовался ли инструмент gcode_analyzer достаточно много раз
        from data.postgres.models import ToolInvocation
        gcode_analyses = self.db.query(func.count(ToolInvocation.id)).filter(
            ToolInvocation.session.has(user_id=user_id),
            ToolInvocation.tool_name == "gcode_analyzer",
            ToolInvocation.success == True
        ).scalar()
        
        # Если пользователь проанализировал G-code более 20 раз, считаем его экспертом
        return gcode_analyses >= 20
    
    def check_all_achievements(self, user_id: int) -> List[Dict]:
        """Проверить все достижения для пользователя"""
        awarded = []
        for achievement in self.ACHIEVEMENTS:
            result = self.check_and_award(user_id, achievement["id"])
            if result:
                awarded.append(result)
        return awarded

