"""Определение типов состояний для LangGraph.

Это Single Source of Truth для всей информации, циркулирующей в графе.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from datetime import datetime
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ToolResult(TypedDict):
    """Результат выполнения инструмента"""
    tool_name: str
    success: bool
    output: Any
    execution_time_ms: float
    metadata: Dict[str, Any]


class UserContext(TypedDict):
    """Контекст пользователя"""
    user_id: str
    printer_model: Optional[str]  # Ender 3, Prusa i3, Bamboo Lab X1...
    current_material: Optional[str]  # PLA, PETG, ABS...
    session_start: datetime
    preferences: Dict[str, Any]  # Язык, уровень детали ответа


class AgentState(TypedDict):
    """
    Главное состояние агента.
    Управляется LangGraph, передается между узлами.
    """
    
    # Основной поток сообщений (управляется add_messages)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Контекст пользователя
    user_context: UserContext
    
    # История выполненных инструментов в этой сессии
    tool_history: List[ToolResult]
    
    # Текущее состояние анализа
    analysis_state: Dict[str, Any]
    # Структура:
    # {
    #     "gcode_analysis": Optional[Dict],
    #     "vision_analysis": Optional[Dict],
    #     "rag_search_results": List[Dict],
    # }
    
    # Флаги управления процессом
    should_continue: bool
    response_formatted: bool
    error_occurred: bool
    error_message: Optional[str]
    
    # Метаметаданные
    execution_step: int
    total_steps: Optional[int]
