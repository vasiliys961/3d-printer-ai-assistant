"""Router для маршрутизации между агентами"""
from typing import Dict, Any
from orchestration.supervisor import supervisor


class Router:
    """Роутер для маршрутизации запросов"""
    
    def route(self, state: Dict[str, Any]) -> str:
        """Маршрутизация запроса к нужному агенту"""
        messages = state.get("messages", [])
        if not messages:
            return "end"
        
        last_message = messages[-1]
        user_message = last_message.get("content", "") if isinstance(last_message, dict) else str(last_message)
        
        available_agents = ["code_interpreter", "rag_engine", "vision", "hardware"]
        context = state.get("context", {})
        
        next_agent = supervisor.decide_next_agent(user_message, context, available_agents)
        
        return next_agent


router = Router()

