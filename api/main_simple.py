"""
FastAPI приложение.
REST API для общения с агентом.
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Path as PathParam, Query, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session as DBSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_TITLE, API_VERSION, API_PORT, DEBUG
from utils.logger import logger
from utils.metrics import metrics_collector
from utils.exceptions import (
    PrinterAIAssistantException, ValidationError, DatabaseError,
    SessionNotFoundError, UserNotFoundError, LLMError, RAGError
)
import uuid
import time
from database import get_db, SessionLocal, User, Session as SessionModel
from agent import Agent

# ========== ИНИЦИАЛИЗАЦИЯ ==========

app = FastAPI(title=API_TITLE, version=API_VERSION)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware для метрик производительности
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Начинаем отслеживание
        metrics_collector.start_request(
            request_id,
            endpoint=request.url.path,
            method=request.method
        )
        
        try:
            response = await call_next(request)
            
            # Завершаем отслеживание
            metrics_collector.end_request(
                request_id,
                status_code=response.status_code
            )
            
            return response
        except Exception as e:
            metrics_collector.end_request(
                request_id,
                status_code=500,
                error=str(e)
            )
            raise


app.add_middleware(MetricsMiddleware)

# CORS - настраивается через переменные окружения
import os
from config import settings

# Получаем разрешенные домены из переменных окружения или используем дефолтные
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if ALLOWED_ORIGINS == ["*"]:
    # Для разработки разрешаем все, для production нужно указать конкретные домены
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Глобальный агент (инициализируется один раз при старте)
agent = None


@app.on_event("startup")
async def startup():
    global agent
    logger.info("Инициализация API...")
    agent = Agent()
    logger.info("✅ Agent initialized")


# ========== MODELS ==========

class ChatRequest(BaseModel):
    session_id: int = Field(..., gt=0, description="ID сессии (должен быть положительным числом)")
    message: str = Field(..., min_length=1, max_length=5000, description="Сообщение пользователя (1-5000 символов)")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Сообщение не может быть пустым')
        return v.strip()


class ChatResponse(BaseModel):
    session_id: int
    response: str
    status: str


class CreateSessionRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="ID пользователя (должен быть положительным числом)")
    printer_model: str = Field(None, max_length=100, description="Модель принтера (максимум 100 символов)")
    material: str = Field(None, max_length=50, description="Материал (максимум 50 символов)")
    
    @validator('printer_model')
    def validate_printer_model(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None
    
    @validator('material')
    def validate_material(cls, v):
        if v:
            v = v.strip().upper()
            valid_materials = ["PLA", "PETG", "ABS", "TPU", "ASA", "PC", "NYLON"]
            if v not in valid_materials:
                raise ValueError(f"Неподдерживаемый материал. Разрешены: {', '.join(valid_materials)}")
        return v


# ========== ENDPOINTS ==========

@app.get("/health")
async def health():
    """Проверка здоровья приложения"""
    return {"status": "ok", "model": "Claude 3.5 Sonnet via OpenRouter"}


@app.get("/metrics")
async def get_metrics():
    """Получить метрики производительности"""
    stats = metrics_collector.get_stats(limit=100)
    return {
        "status": "ok",
        "metrics": stats,
        "timestamp": time.time()
    }


@app.post("/sessions")
async def create_session(req: CreateSessionRequest, db: DBSession = Depends(get_db)):
    """
    Создать новую сессию (диалог) с пользователем.
    
    **Параметры запроса:**
    - `user_id` (int, обязательный): ID пользователя
    - `printer_model` (str, опционально): Модель принтера (например, "Ender 3")
    - `material` (str, опционально): Материал (PLA, PETG, ABS, TPU, ASA, PC, NYLON)
    
    **Пример запроса:**
    ```json
    {
        "user_id": 1,
        "printer_model": "Ender 3",
        "material": "PLA"
    }
    ```
    
    **Пример ответа:**
    ```json
    {
        "session_id": 123,
        "status": "created"
    }
    ```
    """
    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")
    
    session = SessionModel(
        user_id=req.user_id,
        printer_model=req.printer_model,
        material=req.material
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {"session_id": session.id, "status": "created"}


@app.post("/chat")
@limiter.limit("10/minute")  # 10 запросов в минуту
async def chat(req: ChatRequest, request: Request, db: DBSession = Depends(get_db)):
    """
    Главный эндпоинт для чата с AI-ассистентом.
    
    Обрабатывает сообщения пользователя через мультиагентную систему и возвращает
    структурированный ответ с рекомендациями, параметрами печати и ссылками на источники.
    
    **Параметры запроса:**
    - `session_id` (int, обязательный): ID сессии диалога
    - `message` (str, обязательный): Сообщение пользователя (1-5000 символов)
    
    **Пример запроса:**
    ```json
    {
        "session_id": 1,
        "message": "Почему мой пластик не прилипает к столу? Использую PLA, температура сопла 200°C"
    }
    ```
    
    **Пример ответа:**
    ```json
    {
        "session_id": 1,
        "response": "**Краткий вывод:**\\nПроблема с адгезией PLA...",
        "status": "success"
    }
    ```
    
    **Особенности:**
    - Автоматически задает уточняющие вопросы при недостатке информации
    - Использует историю диалога для контекста
    - Возвращает конкретные параметры печати и ссылки на источники
    """
    # Проверяем существование сессии
    session = db.query(SessionModel).filter(SessionModel.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
    
    # Валидация: проверяем, что сессия не завершена
    if session.ended_at:
        raise HTTPException(status_code=400, detail="Session has been ended")
    
    # Записываем user_id и session_id для метрик
    request.state.user_id = session.user_id
    request.state.session_id = req.session_id
    
    try:
        logger.info(f"Обработка сообщения для сессии {req.session_id}")
        
        # Сохраняем сообщение пользователя
        from database import Message
        user_message = Message(
            session_id=req.session_id,
            role="user",
            content=req.message
        )
        db.add(user_message)
        db.commit()
        
        # Обрабатываем через агента с отслеживанием метрик
        request_id = getattr(request.state, 'request_id', None)
        response = await agent.run(req.message, req.session_id, db, request_id=request_id)
        
        # Сохраняем ответ ассистента
        assistant_message = Message(
            session_id=req.session_id,
            role="assistant",
            content=response
        )
        db.add(assistant_message)
        db.commit()
        
        logger.info(f"✅ Сообщение обработано для сессии {req.session_id}")
        
        return ChatResponse(
            session_id=req.session_id,
            response=response,
            status="success"
        )
    except PrinterAIAssistantException as e:
        db.rollback()
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка обработки сообщения для сессии {req.session_id}: {e}", exc_info=True)
        
        # Сохраняем ошибку в БД для мониторинга
        try:
            from data.postgres.models import Error
            error_record = Error(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=None,  # Можно добавить traceback.format_exc()
                user_id=getattr(request.state, 'user_id', None),
                session_id=req.session_id,
                endpoint="/chat",
                request_id=getattr(request.state, 'request_id', None),
                severity="error"
            )
            db.add(error_record)
            db.commit()
        except Exception as db_error:
            logger.error(f"Не удалось сохранить ошибку в БД: {db_error}")
        
        # Сохраняем сообщение об ошибке
        from database import Message
        error_message = Message(
            session_id=req.session_id,
            role="system",
            content=error_msg
        )
        db.add(error_message)
        db.commit()
        
        # Завершаем отслеживание метрик
        if hasattr(request.state, 'request_id'):
            metrics_collector.end_request(
                request.state.request_id,
                status_code=500,
                user_id=getattr(request.state, 'user_id', None),
                session_id=req.session_id,
                error=str(e)
            )
        
            return ChatResponse(
                session_id=req.session_id,
                response=error_msg,
                status="error"
            )
    except Exception as e:
        db.rollback()
        error_msg = f"❌ Неожиданная ошибка: {str(e)}"
        logger.error(f"Неожиданная ошибка обработки сообщения для сессии {req.session_id}: {e}", exc_info=True)
        
        # Сохраняем ошибку в БД для мониторинга
        try:
            from data.postgres.models import Error
            error_record = Error(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=None,
                user_id=getattr(request.state, 'user_id', None),
                session_id=req.session_id,
                endpoint="/chat",
                request_id=getattr(request.state, 'request_id', None),
                severity="critical"
            )
            db.add(error_record)
            db.commit()
        except Exception as db_error:
            logger.error(f"Не удалось сохранить ошибку в БД: {db_error}")
        
        # Сохраняем сообщение об ошибке
        from database import Message
        error_message = Message(
            session_id=req.session_id,
            role="system",
            content=error_msg
        )
        db.add(error_message)
        db.commit()
        
        # Завершаем отслеживание метрик
        if hasattr(request.state, 'request_id'):
            metrics_collector.end_request(
                request.state.request_id,
                status_code=500,
                user_id=getattr(request.state, 'user_id', None),
                session_id=req.session_id,
                error=str(e)
            )
        
        return ChatResponse(
            session_id=req.session_id,
            response=error_msg,
            status="error"
        )


@app.get("/sessions/{session_id}/history")
@limiter.limit("30/minute")  # 30 запросов в минуту
async def get_history(
    request: Request,
    session_id: int = PathParam(..., gt=0, description="ID сессии (должен быть положительным числом)"),
    limit: int = Query(50, ge=1, le=200, description="Количество сообщений (1-200)"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: DBSession = Depends(get_db)
):
    """
    Получить историю диалога с пагинацией.
    
    Возвращает сообщения сессии с поддержкой пагинации для больших диалогов.
    
    **Параметры:**
    - `session_id`: ID сессии
    - `limit`: Количество сообщений (по умолчанию 50, максимум 200)
    - `offset`: Смещение для пагинации (по умолчанию 0)
    
    **Пример ответа:**
    ```json
    {
        "session_id": 1,
        "messages": [
            {
                "role": "user",
                "content": "Почему мой пластик не прилипает?",
                "created_at": "2024-01-15T10:30:00"
            }
        ],
        "total": 10,
        "limit": 50,
        "offset": 0
    }
    ```
    """
    from data.postgres.repository import MessageRepository
    
    # Проверяем существование сессии
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Используем репозиторий с пагинацией
    message_repo = MessageRepository()
    messages = message_repo.get_session_messages(db, session_id, limit=limit, offset=offset)
    total = message_repo.get_session_messages_count(db, session_id)
    
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ========== LEARNING MODE ENDPOINTS ==========

@app.get("/learning/lessons")
async def get_lessons(level: str = None, db: DBSession = Depends(get_db)):
    """Получить список уроков"""
    from agents.learning_mode.learning_engine import LearningEngine
    engine = LearningEngine(db)
    lessons = engine.get_all_lessons(level=level)
    return {
        "lessons": [
            {
                "id": lesson.id,
                "title": lesson.title,
                "level": lesson.level,
                "estimated_time_minutes": lesson.estimated_time_minutes,
                "prerequisites": lesson.prerequisites
            }
            for lesson in lessons
        ]
    }


@app.get("/learning/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, db: DBSession = Depends(get_db)):
    """Получить детали урока"""
    from agents.learning_mode.learning_engine import LearningEngine
    engine = LearningEngine(db)
    lesson = engine.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {
        "id": lesson.id,
        "title": lesson.title,
        "level": lesson.level,
        "content": lesson.content,
        "exercises": lesson.exercises,
        "quiz": lesson.quiz,
        "estimated_time_minutes": lesson.estimated_time_minutes,
        "prerequisites": lesson.prerequisites
    }


@app.post("/learning/lessons/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: str = PathParam(..., min_length=1, max_length=100, description="ID урока"),
    user_id: int = Query(..., gt=0, description="ID пользователя"),
    score: int = Query(None, ge=0, le=100, description="Оценка (0-100)"),
    db: DBSession = Depends(get_db)
):
    """Отметить урок как пройденный"""
    from agents.learning_mode.learning_engine import LearningEngine
    engine = LearningEngine(db)
    engine.complete_lesson(user_id, lesson_id, score)
    return {"status": "completed", "lesson_id": lesson_id}


@app.get("/learning/progress")
async def get_learning_progress(
    user_id: int = Query(..., gt=0, description="ID пользователя (должен быть положительным числом)"),
    db: DBSession = Depends(get_db)
):
    """Получить прогресс обучения пользователя"""
    from agents.learning_mode.learning_engine import LearningEngine
    engine = LearningEngine(db)
    progress = engine.get_user_progress(user_id)
    next_lesson = engine.get_next_lesson(user_id)
    return {
        **progress,
        "next_lesson": {
            "id": next_lesson.id,
            "title": next_lesson.title
        } if next_lesson else None
    }


# ========== PROJECT RECOMMENDATIONS ENDPOINTS ==========

@app.get("/projects/recommend")
async def recommend_projects(
    user_id: int = Query(..., gt=0, description="ID пользователя"),
    difficulty: str = Query(None, regex="^(easy|medium|hard)$", description="Сложность проекта"),
    material: str = Query(None, max_length=50, description="Материал"),
    max_time_hours: int = Query(None, ge=1, le=1000, description="Максимальное время в часах (1-1000)"),
    db: DBSession = Depends(get_db)
):
    """Получить рекомендации проектов"""
    from agents.project_recommender.recommender import ProjectRecommender
    recommender = ProjectRecommender(db)
    projects = recommender.recommend_projects(
        user_id, difficulty, material, max_time_hours
    )
    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "difficulty": p.difficulty,
                "estimated_time_hours": p.estimated_time_hours,
                "required_material": p.required_material,
                "required_skills": p.required_skills
            }
            for p in projects
        ]
    }


@app.get("/projects/{project_id}")
async def get_project(project_id: str, db: DBSession = Depends(get_db)):
    """Получить детали проекта"""
    from agents.project_recommender.recommender import ProjectRecommender
    recommender = ProjectRecommender(db)
    try:
        project = recommender.get_project(project_id)
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "difficulty": project.difficulty,
            "estimated_time_hours": project.estimated_time_hours,
            "required_material": project.required_material,
            "required_skills": project.required_skills,
            "stl_url": project.stl_url,
            "instructions": project.instructions
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/projects/{project_id}/start")
async def start_project(
    project_id: str = PathParam(..., min_length=1, max_length=100, description="ID проекта"),
    user_id: int = Query(..., gt=0, description="ID пользователя"),
    db: DBSession = Depends(get_db)
):
    """Начать проект"""
    return {"status": "started", "project_id": project_id, "user_id": user_id}


# ========== GAMIFICATION ENDPOINTS ==========

@app.get("/gamification/progress")
async def get_gamification_progress(
    user_id: int = Query(..., gt=0, description="ID пользователя"),
    db: DBSession = Depends(get_db)
):
    """Получить прогресс пользователя (уровень, опыт)"""
    from agents.gamification.level_system import LevelSystem
    level_system = LevelSystem(db)
    progress = level_system.get_user_level(user_id)
    return progress


@app.get("/gamification/achievements")
async def get_achievements(
    user_id: int = Query(None, gt=0, description="ID пользователя (опционально)"),
    db: DBSession = Depends(get_db)
):
    """Получить список достижений"""
    from agents.gamification.achievement_system import AchievementSystem
    achievement_system = AchievementSystem(db)
    
    if user_id:
        user_achievements = achievement_system.get_user_achievements(user_id)
        return {"user_achievements": user_achievements}
    else:
        all_achievements = achievement_system.get_all_achievements()
        return {"achievements": all_achievements}


@app.get("/gamification/leaderboard")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="Количество пользователей в таблице (1-100)"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: DBSession = Depends(get_db)
):
    """Получить таблицу лидеров с пагинацией"""
    from agents.gamification.leaderboard import Leaderboard
    leaderboard = Leaderboard(db)
    result = leaderboard.get_leaderboard(limit, offset)
    return result


@app.post("/upload-gcode")
@limiter.limit("5/minute")  # 5 загрузок в минуту
async def upload_gcode(
    request: Request,
    file: UploadFile = File(...),
    material: str = Field("PLA", description="Материал для анализа"),
    db: DBSession = Depends(get_db)
):
    """
    Загрузить и проанализировать G-code файл.
    
    Выполняет полный анализ G-code: парсинг, валидацию, детекцию аномалий,
    расчет метрик и генерацию рекомендаций.
    
    **Параметры:**
    - `file` (обязательный): G-code файл (.gcode, .g, .txt)
    - `material` (опционально): Материал для валидации (по умолчанию PLA)
    
    **Ограничения:**
    - Максимальный размер файла: 10MB
    - Разрешенные типы: .gcode, .g, .txt
    
    **Пример ответа:**
    ```json
    {
        "valid": true,
        "errors": [],
        "warnings": ["Line 50: High speed detected"],
        "metrics": {
            "estimated_time_hours": 2.5,
            "filament_weight_g": 25.3,
            "estimated_cost_usd": 0.51
        },
        "anomalies": [],
        "recommendations": ["Проверьте температуру сопла..."]
    }
    ```
    """
    # Валидация размера файла (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Валидация типа файла
    allowed_extensions = {'.gcode', '.g', '.txt'}
    file_extension = None
    if file.filename:
        file_extension = '.' + file.filename.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_extensions)}"
            )
    
    try:
        content = await file.read()
        
        # Проверка размера
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Декодируем содержимое
        try:
            file_content = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Файл должен быть текстовым G-code файлом (UTF-8)"
            )
        
        # Валидация материала
        valid_materials = ["PLA", "PETG", "ABS", "TPU", "ASA", "PC", "Nylon"]
        if material.upper() not in valid_materials:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый материал. Разрешены: {', '.join(valid_materials)}"
            )
        
        # Анализируем G-code
        result = agent.gcode_analyzer.analyze_gcode(
            gcode_content=file_content,
            material=material.upper(),
            printer_profile="Ender3"
        )
        
        return {
            "valid": result.get("valid", False),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
            "metrics": result.get("metrics", {}),
            "anomalies": result.get("anomalies", []),
            "recommendations": result.get("recommendations", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


# ========== ЗАПУСК ==========

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )

