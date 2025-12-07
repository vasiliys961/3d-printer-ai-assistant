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
    progress = relationship("UserProgress", back_populates="user", uselist=False)
    achievements = relationship("UserAchievement", back_populates="user")
    lessons = relationship("UserLesson", back_populates="user")
    projects = relationship("UserProject", back_populates="user")


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


class UserProgress(Base):
    """Прогресс пользователя"""
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    level = Column(Integer, default=1, server_default='1')
    experience = Column(Integer, default=0, server_default='0')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="progress")


class Achievement(Base):
    """Достижение"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    achievement_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAchievement(Base):
    """Связь пользователь-достижение"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False, index=True)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")


class Lesson(Base):
    """Урок"""
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    level = Column(String(50), nullable=False)  # beginner, intermediate, advanced
    content = Column(Text, nullable=False)
    estimated_time_minutes = Column(Integer, default=15)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserLesson(Base):
    """Прогресс пользователя по уроку"""
    __tablename__ = "user_lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    completed = Column(Boolean, default=False, server_default='false')
    score = Column(Integer, nullable=True)
    time_spent_minutes = Column(Integer, default=0, server_default='0')
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="lessons")
    lesson = relationship("Lesson")


class Project(Base):
    """Проект для печати"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=False)  # easy, medium, hard
    estimated_time_hours = Column(Integer, nullable=False)
    required_material = Column(String(50), nullable=True)
    stl_url = Column(String(500), nullable=True)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserProject(Base):
    """Начатый проект пользователя"""
    __tablename__ = "user_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="started", server_default='started')  # started, completed, abandoned
    
    user = relationship("User", back_populates="projects")
    project = relationship("Project")


class Error(Base):
    """Логирование ошибок для мониторинга"""
    __tablename__ = "errors"
    
    id = Column(Integer, primary_key=True, index=True)
    error_type = Column(String(100), nullable=False, index=True)  # LLMError, RAGError, DatabaseError и т.д.
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)
    endpoint = Column(String(255), nullable=True)  # API endpoint где произошла ошибка
    request_id = Column(String(100), nullable=True, index=True)  # ID запроса для связи с метриками
    severity = Column(String(20), default="error", server_default='error')  # error, warning, critical
    resolved = Column(Boolean, default=False, server_default='false')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User")
    session = relationship("Session")


# Индексы для производительности
Index('idx_sessions_user_id', Session.user_id)
Index('idx_messages_session_id', Message.session_id)
Index('idx_messages_created_at', Message.created_at)  # Для сортировки по дате
Index('idx_prints_user_id', Print.user_id)
Index('idx_prints_created_at', Print.created_at)  # Для фильтрации по дате
Index('idx_tool_invocations_session_id', ToolInvocation.session_id)
Index('idx_tool_invocations_tool_name', ToolInvocation.tool_name)  # Для фильтрации по инструменту
Index('idx_user_progress_user_id', UserProgress.user_id)
Index('idx_user_progress_experience', UserProgress.experience)  # Для сортировки leaderboard
Index('idx_user_achievements_user_id', UserAchievement.user_id)
Index('idx_user_lessons_user_id', UserLesson.user_id)
Index('idx_user_lessons_completed', UserLesson.completed)  # Для фильтрации пройденных уроков
Index('idx_errors_created_at', Error.created_at)  # Для фильтрации по дате
Index('idx_errors_severity', Error.severity)  # Для фильтрации по серьезности
