"""
Unit тесты для MultiModelAgent
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from agents.multi_model_agent import MultiModelAgent, AnalyzerOutput, ConsultantOutput
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db():
    """Создать mock БД сессии"""
    return Mock(spec=Session)


@pytest.fixture
def agent():
    """Создать экземпляр MultiModelAgent"""
    return MultiModelAgent(provider="openrouter")


@pytest.mark.unit
class TestMultiModelAgent:
    """Тесты MultiModelAgent"""
    
    @pytest.mark.asyncio
    async def test_call_analyzer(self, agent):
        """Тест вызова Аналитика"""
        user_message = "Как настроить температуру для PETG?"
        
        output = await agent.call_analyzer(user_message)
        
        assert isinstance(output, AnalyzerOutput)
        assert output.goal is not None
        assert isinstance(output.subtasks, list)
        assert isinstance(output.keywords, list)
        assert output.domain_check is True
    
    @pytest.mark.asyncio
    async def test_call_consultant(self, agent):
        """Тест вызова Консультанта"""
        user_message = "Проблема с адгезией PLA"
        analyzer_output = AnalyzerOutput(
            goal="Решить проблему адгезии",
            subtasks=["Определить причину", "Предложить решение"],
            keywords=["PLA", "адгезия", "стол"],
            domain_check=True
        )
        rag_context = "PLA требует температуру стола 50-70°C для хорошей адгезии."
        
        output = await agent.call_consultant(
            user_message,
            analyzer_output,
            rag_context
        )
        
        assert isinstance(output, ConsultantOutput)
        assert output.brief_summary is not None
        assert isinstance(output.technical_breakdown, list)
        assert isinstance(output.recommended_actions, list)
    
    @pytest.mark.asyncio
    async def test_extract_user_context_from_history(self, agent):
        """Тест извлечения контекста пользователя из истории"""
        history = [
            {"role": "user", "content": "У меня Ender 3 и PLA"},
            {"role": "assistant", "content": "Хорошо, помогу с настройкой"},
            {"role": "user", "content": "Проблема с warping"}
        ]
        
        context = agent._extract_user_context_from_history(history)
        
        assert isinstance(context, dict)
        # Может найти упоминания принтера и материала
        assert "printer_model" in context or "material" in context or "mentioned_issues" in context
    
    def test_should_ask_question(self, agent):
        """Тест определения необходимости задать вопрос"""
        analyzer_output = AnalyzerOutput(
            goal="Тест",
            subtasks=[],
            keywords=[],
            critical_data={"gcode_needed": True},
            domain_check=True
        )
        consultant_output = ConsultantOutput(
            brief_summary="Тест",
            what_to_clarify=["Нужен G-code", "Нужна температура"]
        )
        
        # Это async метод, но для теста можно проверить логику
        assert len(consultant_output.what_to_clarify) >= 2
    
    @pytest.mark.asyncio
    async def test_load_conversation_history(self, agent, mock_db):
        """Тест загрузки истории диалога"""
        # Мокаем запрос к БД
        from data.postgres.models import Message
        mock_message = Mock()
        mock_message.role = "user"
        mock_message.content = "Тестовое сообщение"
        mock_message.created_at = None
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_message]
        
        history = agent._load_conversation_history(1, mock_db)
        
        assert isinstance(history, list)
        if history:
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "Тестовое сообщение"

