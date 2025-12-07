"""Рекомендательная система проектов"""
from typing import List, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import func
from agents.project_recommender.project_database import Project, PROJECTS
from data.postgres.models import UserLesson, Lesson, Print, ToolInvocation, UserAchievement, Achievement


class ProjectRecommender:
    """Рекомендательная система для проектов"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_skills(self, user_id: int) -> Set[str]:
        """Получить навыки пользователя на основе его активности"""
        skills = set()
        
        # 1. Навыки из пройденных уроков
        completed_lessons = self.db.query(UserLesson).join(
            Lesson, UserLesson.lesson_id == Lesson.id
        ).filter(
            UserLesson.user_id == user_id,
            UserLesson.completed == True
        ).all()
        
        for user_lesson in completed_lessons:
            lesson = user_lesson.lesson
            # Извлекаем навыки из названия урока
            if "gcode" in lesson.title.lower() or "g-code" in lesson.title.lower():
                skills.add("gcode_basics")
            if "калибровка" in lesson.title.lower() or "calibration" in lesson.title.lower():
                skills.add("calibration")
            if "материал" in lesson.title.lower() or "material" in lesson.title.lower():
                skills.add("material_selection")
            if "настройка" in lesson.title.lower() or "settings" in lesson.title.lower():
                skills.add("slicer_settings")
        
        # 2. Навыки из успешных печатей
        successful_prints = self.db.query(func.count(Print.id)).filter(
            Print.user_id == user_id,
            Print.success == True
        ).scalar()
        
        if successful_prints >= 1:
            skills.add("basic_printing")
        if successful_prints >= 10:
            skills.add("experienced_printing")
        if successful_prints >= 50:
            skills.add("expert_printing")
        
        # 3. Навыки из использования инструментов
        gcode_analyses = self.db.query(func.count(ToolInvocation.id)).join(
            ToolInvocation.session
        ).filter(
            ToolInvocation.session.has(user_id=user_id),
            ToolInvocation.tool_name == "gcode_analyzer",
            ToolInvocation.success == True
        ).scalar()
        
        if gcode_analyses >= 5:
            skills.add("gcode_analysis")
        if gcode_analyses >= 20:
            skills.add("gcode_expert")
        
        # 4. Навыки из достижений
        achievements = self.db.query(UserAchievement).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).filter(
            UserAchievement.user_id == user_id
        ).all()
        
        for user_achievement in achievements:
            achievement = user_achievement.achievement
            if "gcode" in achievement.achievement_id.lower():
                skills.add("gcode_expert")
            if "lessons" in achievement.achievement_id.lower() or "базовые" in achievement.name.lower():
                skills.add("basic_knowledge")
        
        return skills
    
    def recommend_projects(
        self,
        user_id: int,
        difficulty: str = None,
        material: str = None,
        max_time_hours: int = None,
        limit: int = 5
    ) -> List[Project]:
        """Рекомендовать проекты на основе навыков пользователя"""
        user_skills = self.get_user_skills(user_id)
        
        recommended = []
        scored_projects = []
        
        for project in PROJECTS:
            # Фильтрация по сложности
            if difficulty and project.difficulty != difficulty:
                continue
            
            # Фильтрация по материалу
            if material and project.required_material != material:
                continue
            
            # Фильтрация по времени
            if max_time_hours and project.estimated_time_hours > max_time_hours:
                continue
            
            # Подсчитываем совпадение навыков
            required_skills = set(project.required_skills) if hasattr(project, 'required_skills') else set()
            matching_skills = required_skills.intersection(user_skills)
            score = len(matching_skills)
            
            # Если все требуемые навыки есть, добавляем в рекомендованные
            if not required_skills or matching_skills == required_skills:
                scored_projects.append((score, project))
        
        # Сортируем по score (больше совпадений = выше)
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        recommended = [project for _, project in scored_projects[:limit]]
        
        # Если не нашли по навыкам, возвращаем простые проекты
        if not recommended:
            recommended = [p for p in PROJECTS if p.difficulty == "easy"][:limit]
        
        return recommended
    
    def get_project(self, project_id: str) -> Project:
        """Получить проект по ID"""
        for project in PROJECTS:
            if project.id == project_id:
                return project
        raise ValueError(f"Project {project_id} not found")

