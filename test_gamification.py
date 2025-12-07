"""Тесты геймификации"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.gamification.achievement_system import AchievementSystem
from agents.gamification.level_system import LevelSystem
from agents.gamification.leaderboard import Leaderboard


def test_gamification():
    """Тест геймификации"""
    print("🧪 Тестирование геймификации...")
    
    # Создаем mock DB session
    class MockDB:
        pass
    
    # Тест системы достижений
    achievement_system = AchievementSystem(MockDB())
    achievements = achievement_system.get_all_achievements()
    print(f"✅ Всего достижений: {len(achievements)}")
    
    # Тест системы уровней
    level_system = LevelSystem(MockDB())
    level = level_system.get_user_level(1)
    print(f"✅ Уровень пользователя: {level['level']}")
    
    # Тест таблицы лидеров
    leaderboard = Leaderboard(MockDB())
    top_users = leaderboard.get_leaderboard(limit=5)
    print(f"✅ Пользователей в таблице лидеров: {len(top_users)}")
    
    print("✅ Тест геймификации пройден!")


if __name__ == "__main__":
    test_gamification()

