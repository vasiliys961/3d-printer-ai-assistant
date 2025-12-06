"""
Agent - обертка над Supervisor для обратной совместимости с API
"""
from orchestration.supervisor import Supervisor
from agents.code_interpreter.tool import CodeInterpreterTool
from sqlalchemy.orm import Session as DBSession


class Agent:
    """Агент для обработки запросов пользователей"""
    
    def __init__(self):
        """Инициализация агента"""
        self.supervisor = Supervisor()
        self.gcode_analyzer = CodeInterpreterTool()
    
    async def run(
        self,
        message: str,
        session_id: int = None,
        db: DBSession = None
    ) -> str:
        """
        Обработать сообщение пользователя
        
        Args:
            message: Текст сообщения
            session_id: ID сессии (опционально)
            db: Сессия БД (опционально)
        
        Returns:
            Ответ агента
        """
        # Получаем информацию о сессии из БД, если доступна
        user_id = None
        printer_model = None
        material = None
        
        if db and session_id:
            from data.postgres.models import Session as SessionModel
            session = db.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            
            if session:
                user_id = str(session.user_id)
                printer_model = session.printer_model
                material = session.material
        
        # Запускаем Supervisor
        response = await self.supervisor.run(
            user_input=message,
            session_id=str(session_id) if session_id else None,
            user_id=user_id,
            printer_model=printer_model,
            current_material=material
        )
        
        return response

