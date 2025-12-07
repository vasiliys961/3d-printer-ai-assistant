"""Repository для работы с БД"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, func
from data.postgres.models import (
    User, Session as DBSession, Message, Print, ToolInvocation,
    UserProgress, Achievement, UserAchievement, Lesson, UserLesson
)
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
    def get_session_messages(
        db: Session, 
        session_id: int,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """Получить сообщения сессии с пагинацией (оптимизировано)"""
        query = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc())
        
        # По умолчанию ограничиваем 100 сообщениями для производительности
        if limit is None:
            limit = 100
        elif limit > 1000:
            limit = 1000  # Максимум 1000 сообщений за раз
        
        query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def get_session_messages_count(db: Session, session_id: int) -> int:
        """Получить количество сообщений в сессии"""
        return db.query(func.count(Message.id)).filter(
            Message.session_id == session_id
        ).scalar()


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


class UserProgressRepository:
    """Репозиторий для работы с прогрессом пользователя"""
    
    @staticmethod
    def get_or_create_progress(db: Session, user_id: int) -> UserProgress:
        """Получить или создать прогресс пользователя"""
        progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        if not progress:
            progress = UserProgress(user_id=user_id, level=1, experience=0)
            db.add(progress)
            db.commit()
            db.refresh(progress)
        return progress
    
    @staticmethod
    def get_progress(db: Session, user_id: int) -> Optional[UserProgress]:
        """Получить прогресс пользователя"""
        return db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
    
    @staticmethod
    def add_experience(db: Session, user_id: int, exp: int) -> UserProgress:
        """Добавить опыт пользователю"""
        progress = UserProgressRepository.get_or_create_progress(db, user_id)
        progress.experience += exp
        # Пересчитываем уровень
        EXP_PER_LEVEL = 100
        new_level = (progress.experience // EXP_PER_LEVEL) + 1
        if new_level > progress.level:
            progress.level = new_level
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def get_leaderboard(db: Session, limit: int = 10, offset: int = 0) -> Tuple[List[dict], int]:
        """Получить таблицу лидеров с пагинацией"""
        # Используем joinedload для оптимизации
        query = db.query(
            UserProgress,
            User.username
        ).join(
            User, UserProgress.user_id == User.id
        ).order_by(
            desc(UserProgress.experience)
        )
        
        # Получаем общее количество
        total = query.count()
        
        # Применяем пагинацию
        results = query.limit(limit).offset(offset).all()
        
        leaderboard = []
        for rank, (progress, username) in enumerate(results, offset + 1, 1):
            leaderboard.append({
                "user_id": progress.user_id,
                "username": username,
                "level": progress.level,
                "experience": progress.experience,
                "rank": rank
            })
        return leaderboard, total
    
    @staticmethod
    def get_user_rank(db: Session, user_id: int) -> dict:
        """Получить ранг пользователя"""
        user_progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        if not user_progress:
            return {"user_id": user_id, "rank": None, "total_users": 0}
        
        # Подсчитываем количество пользователей с большим опытом
        rank = db.query(func.count(UserProgress.id)).filter(
            UserProgress.experience > user_progress.experience
        ).scalar() + 1
        
        total_users = db.query(func.count(UserProgress.id)).scalar()
        
        return {
            "user_id": user_id,
            "rank": rank,
            "total_users": total_users
        }


class AchievementRepository:
    """Репозиторий для работы с достижениями"""
    
    @staticmethod
    def get_or_create_achievement(
        db: Session,
        achievement_id: str,
        name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None
    ) -> Achievement:
        """Получить или создать достижение"""
        achievement = db.query(Achievement).filter(
            Achievement.achievement_id == achievement_id
        ).first()
        if not achievement:
            achievement = Achievement(
                achievement_id=achievement_id,
                name=name,
                description=description,
                icon=icon
            )
            db.add(achievement)
            db.commit()
            db.refresh(achievement)
        return achievement
    
    @staticmethod
    def get_all_achievements(db: Session) -> List[Achievement]:
        """Получить все достижения"""
        return db.query(Achievement).all()
    
    @staticmethod
    def get_user_achievements(db: Session, user_id: int) -> List[dict]:
        """Получить достижения пользователя"""
        # Используем joinedload для оптимизации
        results = db.query(
            UserAchievement
        ).options(
            joinedload(UserAchievement.achievement)
        ).filter(
            UserAchievement.user_id == user_id
        ).all()
        
        return [
            {
                "id": user_achievement.achievement.achievement_id,
                "name": user_achievement.achievement.name,
                "description": user_achievement.achievement.description,
                "icon": user_achievement.achievement.icon,
                "earned_at": user_achievement.earned_at
            }
            for user_achievement in results
        ]
    
    @staticmethod
    def award_achievement(
        db: Session,
        user_id: int,
        achievement_id: str
    ) -> Optional[UserAchievement]:
        """Наградить пользователя достижением"""
        # Проверяем, есть ли уже это достижение
        achievement = db.query(Achievement).filter(
            Achievement.achievement_id == achievement_id
        ).first()
        if not achievement:
            return None
        
        existing = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement.id
        ).first()
        if existing:
            return existing
        
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id
        )
        db.add(user_achievement)
        db.commit()
        db.refresh(user_achievement)
        return user_achievement
    
    @staticmethod
    def has_achievement(db: Session, user_id: int, achievement_id: str) -> bool:
        """Проверить, есть ли у пользователя достижение"""
        achievement = db.query(Achievement).filter(
            Achievement.achievement_id == achievement_id
        ).first()
        if not achievement:
            return False
        
        return db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement.id
        ).first() is not None


class LessonRepository:
    """Репозиторий для работы с уроками"""
    
    @staticmethod
    def get_lesson_by_id(db: Session, lesson_id: str) -> Optional[Lesson]:
        """Получить урок по lesson_id"""
        return db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    
    @staticmethod
    def get_all_lessons(db: Session) -> List[Lesson]:
        """Получить все уроки"""
        return db.query(Lesson).all()
    
    @staticmethod
    def get_user_lessons(db: Session, user_id: int) -> List[UserLesson]:
        """Получить уроки пользователя (оптимизировано с joinedload)"""
        return db.query(UserLesson).options(
            joinedload(UserLesson.lesson)
        ).filter(UserLesson.user_id == user_id).all()
    
    @staticmethod
    def mark_lesson_complete(
        db: Session,
        user_id: int,
        lesson_id: str,
        score: Optional[int] = None,
        time_spent_minutes: int = 0
    ) -> UserLesson:
        """Отметить урок как пройденный"""
        lesson = LessonRepository.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise ValueError(f"Lesson {lesson_id} not found")
        
        user_lesson = db.query(UserLesson).filter(
            UserLesson.user_id == user_id,
            UserLesson.lesson_id == lesson.id
        ).first()
        
        if user_lesson:
            user_lesson.completed = True
            user_lesson.completed_at = datetime.now()
            if score is not None:
                user_lesson.score = score
            user_lesson.time_spent_minutes = time_spent_minutes
        else:
            user_lesson = UserLesson(
                user_id=user_id,
                lesson_id=lesson.id,
                completed=True,
                score=score,
                time_spent_minutes=time_spent_minutes,
                completed_at=datetime.now()
            )
            db.add(user_lesson)
        
        db.commit()
        db.refresh(user_lesson)
        return user_lesson

