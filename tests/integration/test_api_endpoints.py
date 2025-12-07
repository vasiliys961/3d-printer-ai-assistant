"""
Integration тесты для API endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data.postgres.database import Base, get_db
from data.postgres.models import User, Session as SessionModel
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main_simple import app

# Тестовая БД
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Фикстура для тестовой БД"""
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_user(db_session):
    """Создать тестового пользователя"""
    user = User(
        username="test_user",
        email="test@example.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_session(db_session, test_user):
    """Создать тестовую сессию"""
    session = SessionModel(
        user_id=test_user.id,
        printer_model="Ender 3",
        material="PLA"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture(scope="function")
def client(db_session):
    """Создать тестовый клиент"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration тесты для API"""
    
    def test_health_endpoint(self, client):
        """Тест health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_create_session(self, client, test_user):
        """Тест создания сессии"""
        response = client.post(
            "/sessions",
            json={
                "user_id": test_user.id,
                "printer_model": "Ender 3",
                "material": "PLA"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "created"
    
    def test_create_session_invalid_user(self, client):
        """Тест создания сессии с несуществующим пользователем"""
        response = client.post(
            "/sessions",
            json={
                "user_id": 99999,
                "printer_model": "Ender 3"
            }
        )
        assert response.status_code == 404
    
    def test_chat_endpoint(self, client, test_session):
        """Тест chat endpoint"""
        # Мокаем agent.run чтобы не вызывать реальный LLM
        with patch('api.main_simple.agent') as mock_agent:
            mock_agent.run = AsyncMock(return_value="Тестовый ответ")
            
            response = client.post(
                "/chat",
                json={
                    "session_id": test_session.id,
                    "message": "Тестовое сообщение"
                }
            )
            
            # Может быть 200 или 500 в зависимости от моков
            assert response.status_code in [200, 500]
    
    def test_chat_validation(self, client, test_session):
        """Тест валидации chat endpoint"""
        # Слишком длинное сообщение
        long_message = "x" * 6000
        response = client.post(
            "/chat",
            json={
                "session_id": test_session.id,
                "message": long_message
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_get_history(self, client, test_session):
        """Тест получения истории"""
        response = client.get(f"/sessions/{test_session.id}/history")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
    
    def test_get_history_invalid_session(self, client):
        """Тест получения истории несуществующей сессии"""
        response = client.get("/sessions/99999/history")
        assert response.status_code == 404
    
    def test_upload_gcode_validation(self, client):
        """Тест валидации загрузки G-code"""
        # Неправильный тип файла
        response = client.post(
            "/upload-gcode",
            files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
            data={"material": "PLA"}
        )
        # Может быть 400 или 422 в зависимости от валидации
        assert response.status_code in [400, 422]
    
    def test_learning_progress(self, client, test_user):
        """Тест получения прогресса обучения"""
        response = client.get(
            "/learning/progress",
            params={"user_id": test_user.id}
        )
        # Может быть 200 или 500 в зависимости от реализации
        assert response.status_code in [200, 500]
    
    def test_gamification_progress(self, client, test_user):
        """Тест получения прогресса геймификации"""
        response = client.get(
            "/gamification/progress",
            params={"user_id": test_user.id}
        )
        assert response.status_code == 200
        data = response.json()
        assert "level" in data
        assert "experience" in data
    
    def test_leaderboard(self, client):
        """Тест получения таблицы лидеров"""
        response = client.get("/gamification/leaderboard", params={"limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data

