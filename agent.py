"""
Agent - обертка над Supervisor для обратной совместимости с API
Поддерживает два режима:
1. Supervisor-based (по умолчанию) - LangGraph с инструментами
2. MultiModel - мульти-модельная архитектура с ролями
"""
from orchestration.supervisor import Supervisor
from agents.code_interpreter.tool import CodeInterpreterTool
from agents.multi_model_agent import MultiModelAgent
from sqlalchemy.orm import Session as DBSession
from config import settings


class Agent:
    """Агент для обработки запросов пользователей"""
    
    def __init__(self, use_multi_model: bool = False):
        """
        Инициализация агента
        
        Args:
            use_multi_model: Если True, использует MultiModelAgent вместо Supervisor
        """
        self.use_multi_model = use_multi_model or getattr(settings, 'use_multi_model_agent', False)
        
        if self.use_multi_model:
            self.multi_model_agent = MultiModelAgent(provider=settings.llm_provider)
        else:
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
        
        # Выбираем режим работы
        if self.use_multi_model:
            # Мульти-модельная архитектура
            response = await self.multi_model_agent.run(
                user_message=message,
                session_id=session_id,
                db=db
            )
        else:
            # Supervisor-based архитектура (по умолчанию)
            response = await self.supervisor.run(
                user_input=message,
                session_id=str(session_id) if session_id else None,
                user_id=user_id,
                printer_model=printer_model,
                current_material=material
            )
        
        return response

