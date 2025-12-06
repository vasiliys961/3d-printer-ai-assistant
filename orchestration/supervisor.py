"""SUPERVISOR — основной граф LangGraph, управляющий потоком выполнения.

Логика маршрутизации:
1. User Input → Supervisor (Claude)
2. Supervisor анализирует intent и выбирает tool(ы)
3. Tool выполняется параллельно (если возможно)
4. Результат → Supervisor для финализации ответа
"""

from typing import Literal, List
from datetime import datetime
import time
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from .state import AgentState, UserContext, ToolResult
from .config import SYSTEM_PROMPT, LLM_CONFIG
from .tools import (
    GcodeAnalyzer,
    RAGEngine,
    VisionPipeline,
    HardwareInterface
)


class Supervisor:
    def __init__(self):
        self.llm = ChatAnthropic(**LLM_CONFIG)
        
        # Инициализируем все tools (объединяем все списки в один плоский список)
        self.tools = (
            GcodeAnalyzer +
            RAGEngine +
            VisionPipeline +
            HardwareInterface
        )
        
        # Биндим tools к LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Строим граф
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Построение LangGraph"""
        workflow = StateGraph(AgentState)
        
        # Узлы
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("tools", self._tools_node)  # Кастомный узел для отслеживания результатов
        workflow.add_node("formatter", self._format_response)
        
        # Ребра (edges)
        workflow.add_edge(START, "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                "tools": "tools",
                "format": "formatter",
                "end": END
            }
        )
        workflow.add_edge("tools", "supervisor")  # Feedback loop
        workflow.add_edge("formatter", END)
        
        return workflow.compile()
    
    def _tools_node(self, state: AgentState) -> dict:
        """
        Обертка над ToolNode для отслеживания результатов выполнения.
        """
        from langgraph.prebuilt import ToolNode
        
        tool_node = ToolNode(self.tools)
        
        # Засекаем время выполнения
        start_time = time.time()
        
        # Выполняем инструменты
        result = tool_node.invoke(state)
        
        # Вычисляем время выполнения
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Извлекаем информацию о вызванных инструментах
        last_msg = state["messages"][-1]
        tool_results = []
        
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            # Получаем результаты из ответа ToolNode
            tool_messages = result.get("messages", [])
            
            for tool_call in last_msg.tool_calls:
                tool_name = tool_call.get("name", "unknown")
                
                # Ищем соответствующий результат
                tool_output = None
                for msg in tool_messages:
                    if hasattr(msg, "content") and hasattr(msg, "name") and msg.name == tool_name:
                        tool_output = msg.content
                        break
                
                tool_result: ToolResult = {
                    "tool_name": tool_name,
                    "success": tool_output is not None,
                    "output": tool_output,
                    "execution_time_ms": execution_time_ms / len(last_msg.tool_calls) if last_msg.tool_calls else execution_time_ms,
                    "metadata": {
                        "tool_call_id": tool_call.get("id"),
                        "args": tool_call.get("args", {})
                    }
                }
                tool_results.append(tool_result)
        
        # Обновляем состояние
        updates = result.copy()
        current_history = state.get("tool_history", [])
        updates["tool_history"] = current_history + tool_results
        
        return updates
    
    def _supervisor_node(self, state: AgentState) -> dict:
        """
        Основной узел Supervisor.
        Анализирует ввод, выбирает инструменты.
        """
        messages = state.get("messages", [])
        
        # Инициализируем состояние если нужно
        updates = {}
        
        # Добавляем system prompt если его нет
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        # Вызываем Claude с инструментами
        response = self.llm_with_tools.invoke(messages)
        
        # Обновляем состояние
        updates["messages"] = [response]
        updates["execution_step"] = state.get("execution_step", 0) + 1
        updates["should_continue"] = True
        
        return updates
    
    def _route_decision(self, state: AgentState) -> Literal["tools", "format", "end"]:
        """
        Маршрутизация: если есть tool_calls -> tools, иначе -> format
        """
        last_msg = state["messages"][-1]
        
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        
        # Если это финальный ответ от Claude -> форматируем
        if hasattr(last_msg, "content") and last_msg.content:
            return "format"
        
        return "end"
    
    def _format_response(self, state: AgentState) -> dict:
        """
        Финализация ответа перед отправкой пользователю.
        Обогащаем метаданными (источники, уверенность).
        """
        last_msg = state["messages"][-1]
        
        # Обновляем analysis_state на основе tool_history
        analysis_state = state.get("analysis_state", {})
        tool_history = state.get("tool_history", [])
        
        # Извлекаем результаты анализа из истории инструментов
        for tool_result in tool_history:
            tool_name = tool_result.get("tool_name", "")
            output = tool_result.get("output", {})
            
            if "gcode" in tool_name.lower():
                analysis_state["gcode_analysis"] = output
            elif "vision" in tool_name.lower() or "image" in tool_name.lower():
                analysis_state["vision_analysis"] = output
            elif "rag" in tool_name.lower() or "search" in tool_name.lower():
                if "rag_search_results" not in analysis_state:
                    analysis_state["rag_search_results"] = []
                if isinstance(output, dict) and "results" in output:
                    analysis_state["rag_search_results"].extend(output.get("results", []))
        
        return {
            "messages": [last_msg],
            "response_formatted": True,
            "should_continue": False,
            "analysis_state": analysis_state
        }
    
    async def run(
        self, 
        user_input: str, 
        session_id: str = None,
        user_id: str = None,
        printer_model: str = None,
        current_material: str = None
    ) -> str:
        """
        Основной метод для запуска агента.
        """
        # Получаем историю сессии из БД
        history = self._load_session_history(session_id)
        
        # Добавляем новое сообщение
        history.append(HumanMessage(content=user_input))
        
        # Создаем начальное состояние
        initial_state: AgentState = {
            "messages": history,
            "user_context": {
                "user_id": user_id or session_id or "anonymous",
                "printer_model": printer_model,
                "current_material": current_material,
                "session_start": datetime.now(),
                "preferences": {}
            },
            "tool_history": [],
            "analysis_state": {},
            "should_continue": True,
            "response_formatted": False,
            "error_occurred": False,
            "error_message": None,
            "execution_step": 0,
            "total_steps": None
        }
        
        try:
            # Запускаем граф
            result = self.workflow.invoke(initial_state)
            
            # Сохраняем историю
            self._save_session_history(session_id, result["messages"], result.get("user_context"))
            
            # Возвращаем финальный ответ
            final_message = result["messages"][-1]
            if hasattr(final_message, "content"):
                return final_message.content
            return str(final_message)
        except Exception as e:
            # Обработка ошибок
            error_state = {
                "error_occurred": True,
                "error_message": str(e),
                "should_continue": False
            }
            return f"Произошла ошибка: {str(e)}"
    
    def _load_session_history(self, session_id: str) -> List[BaseMessage]:
        """Загрузка истории из БД"""
        if session_id:
            try:
                from data.postgres.database import SessionLocal
                from data.postgres.models import Session, Message
                from langchain_core.messages import AIMessage
                
                db = SessionLocal()
                try:
                    session = db.query(Session).filter(Session.id == int(session_id) if session_id.isdigit() else None).first()
                    if session:
                        messages = []
                        # Загружаем сообщения из БД
                        db_messages = db.query(Message).filter(Message.session_id == session.id).order_by(Message.created_at).all()
                        for msg in db_messages:
                            if msg.role == "user":
                                messages.append(HumanMessage(content=msg.content))
                            elif msg.role == "assistant":
                                messages.append(AIMessage(content=msg.content))
                            elif msg.role == "system":
                                messages.append(SystemMessage(content=msg.content))
                        
                        if messages:
                            return messages
                finally:
                    db.close()
            except Exception as e:
                print(f"Error loading session history: {e}")
        
        return [SystemMessage(content=SYSTEM_PROMPT)]
    
    def _save_session_history(
        self, 
        session_id: str, 
        messages: List[BaseMessage],
        user_context: UserContext = None
    ):
        """Сохранение истории в БД"""
        if session_id:
            try:
                from data.postgres.database import SessionLocal
                from data.postgres.models import Session, Message, User
                
                db = SessionLocal()
                try:
                    # Получаем или создаем пользователя
                    user_id = user_context.get("user_id") if user_context else None
                    user = None
                    if user_id:
                        # Пробуем найти по telegram_id или создать нового
                        user = db.query(User).filter(
                            User.telegram_id == int(user_id) if str(user_id).isdigit() else None
                        ).first()
                        
                        if not user:
                            # Создаем нового пользователя
                            user = User(
                                telegram_id=int(user_id) if str(user_id).isdigit() else None,
                                username=f"user_{user_id}",
                                email=f"user_{user_id}@example.com"
                            )
                            db.add(user)
                            db.flush()
                    
                    # Получаем или создаем сессию
                    session = None
                    if session_id.isdigit():
                        session = db.query(Session).filter(Session.id == int(session_id)).first()
                    
                    if not session:
                        # Создаем новую сессию
                        session = Session(
                            user_id=user.id if user else None,
                            printer_model=user_context.get("printer_model") if user_context else None,
                            material=user_context.get("current_material") if user_context else None
                        )
                        db.add(session)
                        db.flush()
                    else:
                        # Обновляем информацию о сессии
                        if user_context:
                            if user_context.get("printer_model"):
                                session.printer_model = user_context.get("printer_model")
                            if user_context.get("current_material"):
                                session.material = user_context.get("current_material")
                    
                    # Сохраняем сообщения
                    for msg in messages:
                        role = "system"
                        if isinstance(msg, HumanMessage):
                            role = "user"
                        elif isinstance(msg, AIMessage):
                            role = "assistant"
                        
                        content = msg.content if hasattr(msg, "content") else str(msg)
                        
                        # Проверяем, не существует ли уже такое сообщение
                        existing = db.query(Message).filter(
                            Message.session_id == session.id,
                            Message.content == content,
                            Message.role == role
                        ).first()
                        
                        if not existing:
                            message = Message(
                                session_id=session.id,
                                role=role,
                                content=content
                            )
                            db.add(message)
                    
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"Error saving session: {e}")
                finally:
                    db.close()
            except Exception as e:
                print(f"Error in _save_session_history: {e}")


# Создаем глобальный экземпляр
supervisor = Supervisor()
