"""REST API для интеграций"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from orchestration.graph import orchestration_graph
from agents.hardware.tool import hardware_tool
from data.storage import storage
import os

app = FastAPI(title="3D Printer AI Assistant API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class TemperatureRequest(BaseModel):
    bed_temp: Optional[float] = None
    nozzle_temp: Optional[float] = None


class PrintRequest(BaseModel):
    gcode_file: str


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "name": "3D Printer AI Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "POST - Отправить сообщение",
            "/status": "GET - Статус принтера",
            "/temperature": "GET/POST - Температура",
            "/print": "POST - Управление печатью",
            "/upload": "POST - Загрузить файл"
        }
    }


@app.post("/chat")
async def chat(request: MessageRequest):
    """Обработка сообщения через граф оркестрации"""
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
    uvicorn.run(app, host="0.0.0.0", port=8000)

