"""REST API для интеграций"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
import asyncio
from orchestration.graph import orchestration_graph
from agents.hardware.tool import hardware_tool
from agents.code_interpreter.tool import CodeInterpreterTool
from data.storage import storage
from data.postgres.database import get_db
from data.postgres.models import Session as SessionModel, Message, User
from data.postgres.repository import SessionRepository, UserRepository
from config import API_TITLE, API_VERSION, API_PORT, DEBUG
import os

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
gcode_analyzer = CodeInterpreterTool()


@app.on_event("startup")
async def startup():
    """Инициализация при старте приложения"""
    print("✅ API initialized")
    print(f"✅ Using LLM Provider: {orchestration_graph.supervisor.llm.__class__.__name__}")


class MessageRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    session_id: int
    message: str


class ChatResponse(BaseModel):
    session_id: int
    response: str
    status: str


class CreateSessionRequest(BaseModel):
    user_id: int
    printer_model: Optional[str] = None
    material: Optional[str] = None


class TemperatureRequest(BaseModel):
    bed_temp: Optional[float] = None
    nozzle_temp: Optional[float] = None


class PrintRequest(BaseModel):
    gcode_file: str


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "endpoints": {
            "/health": "GET - Проверка здоровья",
            "/chat": "POST - Отправить сообщение (legacy)",
            "/sessions": "POST - Создать сессию",
            "/chat": "POST - Чат с сессией",
            "/sessions/{id}/history": "GET - История сессии",
            "/status": "GET - Статус принтера",
            "/temperature": "GET/POST - Температура",
            "/print": "POST - Управление печатью",
            "/upload": "POST - Загрузить файл",
            "/upload-gcode": "POST - Загрузить и анализировать G-code"
        }
    }


@app.get("/health")
async def health():
    """Проверка здоровья приложения"""
    return {
        "status": "ok",
        "version": API_VERSION,
        "llm_provider": "OpenRouter"  # Будет определяться динамически
    }


@app.post("/sessions")
async def create_session(req: CreateSessionRequest, db: DBSession = Depends(get_db)):
    """Создать новую сессию (диалог)"""
    # Проверяем существование пользователя
    user = UserRepository.get_by_id(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")
    
    session = SessionRepository.create_session(
        db=db,
        user_id=req.user_id,
        printer_model=req.printer_model,
        material=req.material
    )
    
    return {"session_id": session.id, "status": "created"}


@app.post("/chat")
async def chat(
    req: ChatRequest, 
    db: DBSession = Depends(get_db)
):
    """
    POST /chat
    Главный эндпоинт для чата с поддержкой сессий.
    
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
        user_message = Message(
            session_id=req.session_id,
            role="user",
            content=req.message
        )
        db.add(user_message)
        db.commit()
        
        # Обрабатываем через граф оркестрации
        result = await orchestration_graph.process(
            req.message,
            context={
                "session_id": str(req.session_id),
                "user_id": str(session.user_id),
                "printer_model": session.printer_model,
                "current_material": session.material
            }
        )
        
        response_text = result.get("response", "")
        
        # Сохраняем ответ ассистента
        assistant_message = Message(
            session_id=req.session_id,
            role="assistant",
            content=response_text
        )
        db.add(assistant_message)
        db.commit()
        
        return ChatResponse(
            session_id=req.session_id,
            response=response_text,
            status="success"
        )
    except Exception as e:
        db.rollback()
        error_msg = f"❌ Error: {str(e)}"
        
        # Сохраняем сообщение об ошибке
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


@app.post("/chat/legacy")
async def chat_legacy(request: MessageRequest):
    """Обработка сообщения через граф оркестрации (legacy без сессий)"""
    try:
        result = await orchestration_graph.process(
            request.message,
            context=request.context or {}
        )
        return {
            "response": result.get("response", ""),
            "tool_results": result.get("tool_results", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Получить статус принтера"""
    try:
        status = await hardware_tool.get_status()
        temp = await hardware_tool.get_temperature()
        return {
            "status": status,
            "temperature": temp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/temperature")
async def get_temperature():
    """Получить температуру"""
    try:
        temp = await hardware_tool.get_temperature()
        return temp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/temperature")
async def set_temperature(request: TemperatureRequest):
    """Установить температуру"""
    try:
        result = await hardware_tool.set_temperature(
            bed_temp=request.bed_temp,
            nozzle_temp=request.nozzle_temp
        )
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/print/start")
async def start_print(request: PrintRequest):
    """Начать печать"""
    try:
        result = await hardware_tool.start_print(request.gcode_file)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/print/stop")
async def stop_print():
    """Остановить печать"""
    try:
        result = await hardware_tool.stop_print()
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/print/pause")
async def pause_print():
    """Приостановить печать"""
    try:
        result = await hardware_tool.pause_print()
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/print/resume")
async def resume_print():
    """Возобновить печать"""
    try:
        result = await hardware_tool.resume_print()
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/history")
async def get_history(session_id: int, db: DBSession = Depends(get_db)):
    """Получить историю диалога"""
    # Проверяем существование сессии
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.id).all()
    
    return {
        "session_id": session_id,
        "user_id": session.user_id,
        "printer_model": session.printer_model,
        "material": session.material,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "messages": [
            {
                "id": m.id,
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
        gcode_content = content.decode("utf-8")
        
        # Анализируем G-code
        result = gcode_analyzer.analyze_gcode(
            gcode_content=gcode_content,
            material=material,
            printer_profile="Ender3"
        )
        
        return {
            "filename": file.filename,
            "valid": result.get("valid", False),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
            "metrics": result.get("metrics", {}),
            "anomalies": result.get("anomalies", []),
            "recommendations": result.get("recommendations", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузить файл (G-code или изображение)"""
    try:
        content = await file.read()
        file_path = f"uploads/{file.filename}"
        
        saved_path = storage.save_file(content, file_path)
        
        return {
            "filename": file.filename,
            "path": saved_path,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )

