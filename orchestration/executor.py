"""Executor для выполнения инструментов агентов"""
from typing import Dict, Any, List
import asyncio
from agents.code_interpreter.tool import code_interpreter_tool
from agents.rag_engine.tool import rag_engine_tool
from agents.vision.tool import vision_tool
from agents.hardware.tool import hardware_tool


class Executor:
    """Исполнитель инструментов агентов"""
    
    def __init__(self):
        self.tools = {
            "code_interpreter": code_interpreter_tool,
            "rag_engine": rag_engine_tool,
            "vision": vision_tool,
            "hardware": hardware_tool
        }
    
    async def execute(self, agent_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить действие агента"""
        tool = self.tools.get(agent_name)
        if not tool:
            return {"error": f"Unknown agent: {agent_name}"}
        
        try:
            # Получаем метод инструмента
            method = getattr(tool, action, None)
            if not method:
                return {"error": f"Unknown action: {action} for agent {agent_name}"}
            
            # Выполняем синхронно или асинхронно
            if asyncio.iscoroutinefunction(method):
                result = await method(**params)
            else:
                result = method(**params)
            
            return {
                "agent": agent_name,
                "action": action,
                "result": result,
                "success": True
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "action": action,
                "error": str(e),
                "success": False
            }
    
    def get_available_actions(self, agent_name: str) -> List[str]:
        """Получить доступные действия агента"""
        tool = self.tools.get(agent_name)
        if not tool:
            return []
        
        # Получаем все методы, которые не являются служебными
        methods = [m for m in dir(tool) if not m.startswith("_") and callable(getattr(tool, m))]
        return methods


executor = Executor()

