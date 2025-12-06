"""
FastAPI приложение.
REST API для общения с агентом.
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_TITLE, API_VERSION, API_PORT, DEBUG
from database import get_db, SessionLocal, User, Session as SessionModel
from agent import Agent

# ========== ИНИЦИАЛИЗАЦИЯ ==========

app = FastAPI(title=API_TITLE, version=API_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный агент (инициализируется один раз при старте)
agent = None


@app.on_event("startup")
async def startup():
    global agent
    agent = Agent()
    print("✅ Agent initialized")


# ========== MODELS ==========

class ChatRequest(BaseModel):
    session_id: int
    message: str


class ChatResponse(BaseModel):
    session_id: int
    response: str
    status: str


class CreateSessionRequest(BaseModel):
    user_id: int
    printer_model: str = None
    material: str = None


# ========== ENDPOINTS ==========

@app.get("/health")
async def health():
    """Проверка здоровья приложения"""
    return {"status": "ok", "model": "Claude 3.5 Sonnet via OpenRouter"}


@app.post("/sessions")
async def create_session(req: CreateSessionRequest, db: DBSession = Depends(get_db)):
    """Создать новую сессию (диалог)"""
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
async def chat(req: ChatRequest, db: DBSession = Depends(get_db)):
    """
    POST /chat
    Главный эндпоинт для чата.
    
    {
        "session_id": 1,
        "message": "Почему мой пластик в воздухе висит? Вот G-code..."
    }
    """
    # Проверяем существование сессии
    session = db.query(SessionModel).filter(SessionModel.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
    
    try:
        # Сохраняем сообщение пользователя
        from database import Message
        user_message = Message(
            session_id=req.session_id,
            role="user",
            content=req.message
        )
        db.add(user_message)
        db.commit()
        
        # Обрабатываем через агента
        response = await agent.run(req.message, req.session_id, db)
        
        # Сохраняем ответ ассистента
        assistant_message = Message(
            session_id=req.session_id,
            role="assistant",
            content=response
        )
        db.add(assistant_message)
        db.commit()
        
        return ChatResponse(
            session_id=req.session_id,
            response=response,
            status="success"
        )
    except Exception as e:
        db.rollback()
        error_msg = f"❌ Error: {str(e)}"
        
        # Сохраняем сообщение об ошибке
        from database import Message
        error_message = Message(
            session_id=req.session_id,
            role="system",
            content=error_msg
        )
        db.add(error_message)
        db.commit()
        
        return ChatResponse(
            session_id=req.session_id,
            response=error_msg,
            status="error"
        )


@app.get("/sessions/{session_id}/history")
async def get_history(session_id: int, db: DBSession = Depends(get_db)):
    """Получить историю диалога"""
    from database import Message
    
    # Проверяем существование сессии
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.id).all()
    
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]
    }


@app.post("/upload-gcode")
async def upload_gcode(
    file: UploadFile = File(...),
    material: str = "PLA",
    db: DBSession = Depends(get_db)
):
    """Загрузить и анализировать G-code файл"""
    try:
        content = await file.read()
        file_content = content.decode("utf-8")
        
        # Анализируем G-code
        result = agent.gcode_analyzer.analyze_gcode(
            gcode_content=file_content,
            material=material,
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
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Файл должен быть текстовым G-code файлом (UTF-8)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

