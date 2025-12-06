"""
MultiModelAgent - мульти-модельная архитектура с ролями

Архитектура:
1. Аналитик - анализирует запрос, ищет информацию
2. Консультант - готовит подробный ответ
3. Редактор - упрощает для новичков
4. Проверяющий - оценивает качество (опционально)
"""

from orchestration.llm_factory import get_llm
from agents.rag_engine.engine import RAGEngine
from agents.code_interpreter.tool import CodeInterpreterTool
from sqlalchemy.orm import Session as DBSession
from data.postgres.models import Message
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio


class MultiModelAgent:
    """
    Агент с использованием 2+ моделей:
    
    1. Аналитик - анализирует запрос, ищет информацию
    2. Консультант - готовит подробный ответ
    3. Редактор - упрощает для новичков
    4. Проверяющий - оценивает качество (опционально)
    """
    
    def __init__(self, provider: str = "openrouter"):
        self.llm = get_llm()  # Основная модель
        self.rag = RAGEngine()
        self.gcode_analyzer = CodeInterpreterTool()
    
    async def call_analyzer(self, user_message: str) -> str:
        """Аналитик: анализирует запрос и определяет, какая информация нужна"""
        prompt = f"""Ты - аналитик запросов о 3D-печати. 
Проанализируй следующий запрос пользователя и определи:
1. Тип вопроса (материалы, дефекты, настройки, G-code)
2. Какая информация нужна для ответа
3. Нужны ли дополнительные данные (G-code, изображения)

Запрос пользователя: {user_message}

Ответь кратко (2-3 предложения) о том, что нужно для ответа."""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content if hasattr(response, 'content') else str(response)
    
    async def call_consultant(self, user_message: str, context: str = "") -> str:
        """Консультант: готовит подробный ответ на основе найденной информации"""
        prompt = f"""Ты - эксперт по 3D-печати. Дай подробный, технически точный ответ.

Контекст из базы знаний:
{context}

Вопрос пользователя: {user_message}

Дай развернутый ответ с конкретными рекомендациями, температурами, настройками."""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content if hasattr(response, 'content') else str(response)
    
    async def call_editor(self, consultant_response: str) -> str:
        """Редактор: упрощает ответ для новичков"""
        prompt = f"""Ты - редактор, который упрощает технические тексты для новичков.

Исходный ответ:
{consultant_response}

Перепиши этот ответ простым языком, без сложных терминов, с примерами.
Сделай его понятным для человека, который только начал заниматься 3D-печатью."""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content if hasattr(response, 'content') else str(response)
    
    async def call_qa_checker(self, response: str) -> dict:
        """Проверяющий: оценивает качество ответа"""
        prompt = f"""Оцени качество следующего ответа по 3 критериям (по 10-балльной шкале):

Ответ:
{response}

Верни оценку в формате JSON:
{{
    "correctness": число от 1 до 10,
    "completeness": число от 1 до 10,
    "clarity": число от 1 до 10
}}"""
        
        response_obj = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        # Парсим JSON из ответа
        import json
        import re
        try:
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Если не удалось распарсить, возвращаем дефолтные значения
        return {"correctness": 7, "completeness": 7, "clarity": 7}
    
    async def run(self, user_message: str, session_id: int, db: DBSession) -> str:
        """
        Главный pipeline:
        
        1. Аналитик → понимает запрос, ищет документы
        2. Консультант → готовит подробный ответ на основе найденной информации
        3. Редактор → упрощает для новичков
        4. Проверяющий → проверяет качество (опционально)
        """
        
        print("\n🔄 Multi-Model Pipeline Started...")
        
        # ===== ШАГ 1: АНАЛИТИК =====
        print("1️⃣ Analyzer: Анализирую запрос...")
        analysis = await self.call_analyzer(user_message)
        print(f"   → {analysis[:100]}...")
        
        # ===== ШАГ 2: ПОИСК В KB =====
        print("2️⃣ RAG: Ищу в базе знаний...")
        kb_results = await self.rag.search(user_message, top_k=3)
        context = kb_results.augmented_context if hasattr(kb_results, 'augmented_context') else ""
        print(f"   → Найдено {kb_results.total_results if hasattr(kb_results, 'total_results') else 0} релевантных документов")
        
        # ===== ШАГ 3: КОНСУЛЬТАНТ =====
        print("3️⃣ Consultant: Готовлю подробный ответ...")
        consultant_response = await self.call_consultant(user_message, context)
        print(f"   → {consultant_response[:100]}...")
        
        # ===== ШАГ 4: РЕДАКТОР (упрощение) =====
        print("4️⃣ Editor: Упрощаю для новичков...")
        simplified = await self.call_editor(consultant_response)
        
        # ===== ШАГ 5: ПРОВЕРЯЮЩИЙ (опционально) =====
        print("5️⃣ QA Checker: Проверяю качество...")
        qa_result = await self.call_qa_checker(consultant_response)
        
        # Формируем финальный ответ
        final_response = f"""{consultant_response}

---

📊 **Оценка качества ответа:**
- Корректность: {qa_result.get('correctness', 5)}/10
- Полнота: {qa_result.get('completeness', 5)}/10
- Ясность: {qa_result.get('clarity', 5)}/10

**Упрощенная версия для новичков:**
{simplified}""".strip()
        
        # Сохраняем в БД
        if db and session_id:
            msg_user = Message(session_id=session_id, role="user", content=user_message)
            msg_assistant = Message(
                session_id=session_id, 
                role="assistant", 
                content=final_response
            )
            
            db.add(msg_user)
            db.add(msg_assistant)
            db.commit()
        
        return final_response

