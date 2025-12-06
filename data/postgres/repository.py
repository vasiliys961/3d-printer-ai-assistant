"""Repository для работы с БД"""
from typing import Optional, List
from sqlalchemy.orm import Session
from data.postgres.models import User, Session as DBSession, Message, Print, ToolInvocation
from datetime import datetime


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    @staticmethod
    def get_or_create_by_telegram_id(db: Session, telegram_id: int) -> User:
        """Получить или создать пользователя по Telegram ID"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=f"telegram_{telegram_id}",
                email=f"telegram_{telegram_id}@telegram.local"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return db.query(User).filter(User.id == user_id).first()


class SessionRepository:
    """Репозиторий для работы с сессиями"""
    
    @staticmethod
    def create_session(
        db: Session,
        user_id: int,
        printer_model: Optional[str] = None,
        material: Optional[str] = None
    ) -> DBSession:
        """Создать новую сессию"""
        session = DBSession(
            user_id=user_id,
            printer_model=printer_model,
            material=material
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[DBSession]:
        """Получить сессию по ID"""
        return db.query(DBSession).filter(DBSession.id == session_id).first()
    
    @staticmethod
    def end_session(db: Session, session_id: int):
        """Завершить сессию"""
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if session:
            session.ended_at = datetime.now()
            db.commit()


class MessageRepository:
    """Репозиторий для работы с сообщениями"""
    
    @staticmethod
    def add_message(
        db: Session,
        session_id: int,
        role: str,
        content: str,
        tokens_used: Optional[int] = None
    ) -> Message:
        """Добавить сообщение в сессию"""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            tokens_used=tokens_used
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def get_session_messages(db: Session, session_id: int) -> List[Message]:
        """Получить все сообщения сессии"""
        return db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()


class PrintRepository:
    """Репозиторий для работы с печатями"""
    
    @staticmethod
    def create_print(
        db: Session,
        user_id: int,
        gcode_hash: Optional[str] = None,
        material: Optional[str] = None,
        estimated_time_hours: Optional[float] = None,
        estimated_weight_g: Optional[float] = None
    ) -> Print:
        """Создать запись о печати"""
        print_record = Print(
            user_id=user_id,
            gcode_hash=gcode_hash,
            material=material,
            estimated_time_hours=estimated_time_hours,
            estimated_weight_g=estimated_weight_g
        )
        db.add(print_record)
        db.commit()
        db.refresh(print_record)
        return print_record
    
    @staticmethod
    def update_print(
        db: Session,
        print_id: int,
        success: Optional[bool] = None,
        notes: Optional[str] = None,
        images_count: Optional[int] = None
    ):
        """Обновить запись о печати"""
        print_record = db.query(Print).filter(Print.id == print_id).first()
        if print_record:
            if success is not None:
                print_record.success = success
            if notes is not None:
                print_record.notes = notes
            if images_count is not None:
                print_record.images_count = images_count
            db.commit()


class ToolInvocationRepository:
    """Репозиторий для логирования вызовов инструментов"""
    
    @staticmethod
    def log_invocation(
        db: Session,
        session_id: int,
        tool_name: str,
        input_data: dict,
        output_data: dict,
        execution_time_ms: int,
        success: bool = True
    ) -> ToolInvocation:
        """Логировать вызов инструмента"""
        invocation = ToolInvocation(
            session_id=session_id,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            execution_time_ms=execution_time_ms,
            success=success
        )
        db.add(invocation)
        db.commit()
        db.refresh(invocation)
        return invocation

