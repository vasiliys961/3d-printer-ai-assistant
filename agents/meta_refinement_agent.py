"""
MetaRefinementAgent - мета-агент для анализа логов и улучшения промптов

Мета-агент анализирует выборку логов диалогов и предлагает точечные улучшения
промптов для каждой роли мультиагентной системы.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from orchestration.llm_factory import get_llm
from langchain_core.messages import HumanMessage
import json
import re


@dataclass
class LogEntry:
    """Запись лога диалога"""
    user_query: str
    analyzer_output: Optional[Dict[str, Any]] = None
    consultant_output: Optional[str] = None
    editor_output: Optional[str] = None
    qa_output: Optional[Dict[str, Any]] = None


@dataclass
class RefinementSuggestion:
    """Предложение по улучшению промптов"""
    global_issues: List[str] = field(default_factory=list)
    agent_specific_issues: Dict[str, List[str]] = field(default_factory=dict)
    prompt_patch_suggestions: Dict[str, str] = field(default_factory=dict)


class MetaRefinementAgent:
    """
    Мета-агент по улучшению промптов мультиагентной системы.
    
    На вход получает выборку логов:
    - запросы пользователя
    - ответы Аналитика, Консультанта, Редактора и Проверяющего
    - оценки качества (correctness, completeness, clarity) и комментарии risksOrHallucinations
    
    Задача — предложить точечные улучшения текстов промптов для каждой роли.
    """
    
    def __init__(self):
        self.llm = get_llm()
    
    async def analyze_logs(self, logs: List[LogEntry]) -> RefinementSuggestion:
        """
        Анализирует выборку логов и предлагает улучшения промптов.
        
        Args:
            logs: Список записей логов диалогов
            
        Returns:
            RefinementSuggestion с предложениями по улучшению
        """
        # Формируем контекст из логов
        logs_context = self._format_logs_for_analysis(logs)
        
        prompt = f"""Ты — мета-агент по улучшению промптов мультиагентной системы.

На вход ты получаешь выборку логов диалогов с мультиагентной системой для анализа G-code и 3D-печати.

ВЫБОРКА ЛОГОВ:
{logs_context}

Твоя задача — предложить точечные улучшения текстов промптов для каждой роли и/или общего пайплайна.

Действуй по шагам:

1. ОБНАРУЖЕНИЕ ПАТТЕРНОВ ПРОБЛЕМ

Найди повторяющиеся ошибки:
- галлюцинации (выдуманные параметры, несуществующие команды G-code)
- пропуск важных шагов в рекомендациях
- непонятная структура ответа
- игнорирование RAG-контекста
- неправильная работа с неопределённостью («уверенный тон при отсутствии данных»)

Для каждого типа проблемы выпиши 1–2 показательных примера (кратко).

2. ДИАГНОСТИКА ПО РОЛЯМ

Определи, на каком этапе пайплайна возникает проблема чаще всего: Аналитик, Консультант, Редактор, Проверяющий.

Для каждой роли сформулируй, какие части её промпта слишком расплывчаты, отсутствуют или формулируют неверные приоритеты.

3. ПРЕДЛОЖЕНИЕ ИЗМЕНЕНИЙ ПРОМПТОВ

Для каждой роли предложи обновлённую версию фрагментов промпта:
- добавь недостающие ограничения (например, «никогда не выдумывай значения параметров, если их нет во входе»)
- уточни приоритет источников (RAG-контекст > общие знания > догадки)
- укажи более жёсткие требования к структуре ответа там, где она «плывёт»

Не переписывай промпт полностью без необходимости — фокусируйся на точечных, измеримых изменениях.

Верни результат в формате JSON:

{{
    "globalIssues": [
        "Краткое описание повторяющейся проблемы 1",
        "Краткое описание повторяющейся проблемы 2"
    ],
    "agentSpecificIssues": {{
        "Analyzer": ["Проблема 1", "Проблема 2"],
        "Consultant": ["Проблема 1", "Проблема 2"],
        "Editor": ["Проблема 1"],
        "QAChecker": ["Проблема 1"]
    }},
    "promptPatchSuggestions": {{
        "Analyzer": "Предлагаемый обновлённый текст или фрагмент промпта для Аналитика...",
        "Consultant": "Предлагаемый обновлённый текст или фрагмент промпта для Консультанта...",
        "Editor": "Предлагаемый обновлённый текст или фрагмент промпта для Редактора...",
        "QAChecker": "Предлагаемый обновлённый текст или фрагмент промпта для Проверяющего..."
    }}
}}

Все предложения формулируй так, чтобы их можно было прямо вставить в system-промпт соответствующего агента."""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Парсим JSON ответ
        return self._parse_refinement_suggestion(content)
    
    def _format_logs_for_analysis(self, logs: List[LogEntry]) -> str:
        """Форматирует логи для анализа"""
        formatted_logs = []
        
        for i, log in enumerate(logs, 1):
            log_text = f"\n=== ЛОГ {i} ===\n"
            log_text += f"Запрос пользователя: {log.user_query}\n"
            
            if log.analyzer_output:
                log_text += f"\nАналитик:\n{json.dumps(log.analyzer_output, ensure_ascii=False, indent=2)}\n"
            
            if log.consultant_output:
                log_text += f"\nКонсультант:\n{log.consultant_output[:500]}...\n"
            
            if log.qa_output:
                log_text += f"\nПроверяющий:\n{json.dumps(log.qa_output, ensure_ascii=False, indent=2)}\n"
            
            formatted_logs.append(log_text)
        
        return "\n".join(formatted_logs)
    
    def _parse_refinement_suggestion(self, content: str) -> RefinementSuggestion:
        """Парсит JSON ответ мета-агента"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return RefinementSuggestion(
                    global_issues=data.get("globalIssues", []),
                    agent_specific_issues=data.get("agentSpecificIssues", {}),
                    prompt_patch_suggestions=data.get("promptPatchSuggestions", {})
                )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Ошибка парсинга ответа мета-агента: {e}")
        
        # Fallback
        return RefinementSuggestion()
    
    async def suggest_improvements_from_db(
        self, 
        db_session,
        session_ids: List[int],
        limit: int = 20
    ) -> RefinementSuggestion:
        """
        Анализирует логи из базы данных и предлагает улучшения.
        
        Args:
            db_session: Сессия БД
            session_ids: Список ID сессий для анализа
            limit: Максимальное количество записей для анализа
            
        Returns:
            RefinementSuggestion с предложениями
        """
        from data.postgres.models import Message, Session
        
        logs = []
        
        # Загружаем сообщения из указанных сессий
        messages = db_session.query(Message).filter(
            Message.session_id.in_(session_ids)
        ).order_by(Message.created_at).limit(limit).all()
        
        # Группируем по сессиям и формируем LogEntry
        current_session = None
        current_log = None
        
        for msg in messages:
            if msg.role == "user":
                if current_log:
                    logs.append(current_log)
                current_log = LogEntry(user_query=msg.content)
            elif msg.role == "assistant" and current_log:
                # Пытаемся извлечь структурированные данные из ответа
                current_log.consultant_output = msg.content
        
        if current_log:
            logs.append(current_log)
        
        return await self.analyze_logs(logs)

