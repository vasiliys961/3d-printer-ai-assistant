"""LangGraph граф оркестрации - обертка над Supervisor"""
from typing import Dict, Any
from orchestration.supervisor import Supervisor


class OrchestrationGraph:
    """Граф оркестрации агентов - использует новый Supervisor"""
    
    def __init__(self):
        self.supervisor = Supervisor()
    
    async def process(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Обработать запрос пользователя"""
        context = context or {}
        session_id = context.get("session_id")
        user_id = context.get("user_id")
        printer_model = context.get("printer_model")
        current_material = context.get("current_material")
        
        try:
            # Запускаем Supervisor с расширенными параметрами
            response = await self.supervisor.run(
                user_message, 
                session_id=session_id,
                user_id=user_id,
                printer_model=printer_model,
                current_material=current_material
            )
            
            return {
                "response": response,
                "tool_results": [],  # Supervisor сам управляет tool results через state
                "state": {"messages": []}
            }
        except Exception as e:
            return {
                "response": f"Произошла ошибка при обработке запроса: {str(e)}",
                "tool_results": [],
                "state": {}
            }


# Создаем глобальный экземпляр для обратной совместимости
orchestration_graph = OrchestrationGraph()
