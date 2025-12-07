"""
Конфигурация pytest с фикстурами
"""
import pytest
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data.postgres.database import Base
from data.postgres.models import User, Session, Message


# Тестовая БД (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Фикстура для тестовой БД сессии"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
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


@pytest.fixture
def test_session(db_session, test_user):
    """Создать тестовую сессию"""
    session = Session(
        user_id=test_user.id,
        printer_model="Ender 3",
        material="PLA"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session
