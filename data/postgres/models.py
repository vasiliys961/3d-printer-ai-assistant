"""PostgreSQL models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from data.postgres.database import Base


class User(Base):
    """Пользователь системы"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telegram_id = Column(Integer, unique=True, nullable=True, index=True)  # Для Telegram бота
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    preferences = Column(JSONB, default={}, server_default='{}')
    
    sessions = relationship("Session", back_populates="user")
    prints = relationship("Print", back_populates="user")


class Session(Base):
    """Сессия (диалог) с пользователем"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    printer_model = Column(String(100), nullable=True)
    material = Column(String(50), nullable=True)
    
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    tool_invocations = relationship("ToolInvocation", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Сообщение в истории диалога"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tokens_used = Column(Integer, nullable=True)
    
    session = relationship("Session", back_populates="messages")


class Print(Base):
    """Запись о печати"""
    __tablename__ = "prints"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    gcode_hash = Column(String(64), nullable=True, index=True)  # SHA256 файла
    material = Column(String(50), nullable=True)
    estimated_time_hours = Column(Float, nullable=True)
    estimated_weight_g = Column(Float, nullable=True)
    success = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    images_count = Column(Integer, default=0, server_default='0')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="prints")
    images = relationship("PrintImage", back_populates="print", cascade="all, delete-orphan")


class PrintImage(Base):
    """Изображения печати"""
    __tablename__ = "print_images"
    
    id = Column(Integer, primary_key=True, index=True)
    print_id = Column(Integer, ForeignKey("prints.id"), nullable=False)
    image_path = Column(String, nullable=False)
    analysis_result = Column(JSONB, nullable=True)  # Результаты анализа изображения
    defect_detected = Column(Boolean, default=False, server_default='false')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    print = relationship("Print", back_populates="images")


class ToolInvocation(Base):
    """Логирование вызовов инструментов"""
    __tablename__ = "tool_invocations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="tool_invocations")


# Индексы для производительности
Index('idx_sessions_user_id', Session.user_id)
Index('idx_messages_session_id', Message.session_id)
Index('idx_prints_user_id', Print.user_id)
Index('idx_tool_invocations_session_id', ToolInvocation.session_id)
