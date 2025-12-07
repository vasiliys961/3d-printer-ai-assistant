"""Тесты рекомендаций проектов"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.project_recommender.recommender import ProjectRecommender
from agents.project_recommender.project_database import PROJECTS


def test_project_recommender():
    """Тест рекомендаций проектов"""
    print("🧪 Тестирование рекомендаций проектов...")
    
    # Создаем mock DB session
    class MockDB:
        pass
    
    recommender = ProjectRecommender(MockDB())
    
    # Получить рекомендации
    projects = recommender.recommend_projects(
        user_id=1,
        difficulty="easy",
        material="PLA",
        limit=3
    )
    print(f"✅ Рекомендовано проектов: {len(projects)}")
    
    for project in projects:
        print(f"  - {project.name} ({project.difficulty})")
    
    # Получить конкретный проект
    project = recommender.get_project("project_001")
    print(f"✅ Проект найден: {project.name}")
    
    print("✅ Тест рекомендаций проектов пройден!")


if __name__ == "__main__":
    test_project_recommender()

