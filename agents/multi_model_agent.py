"""
MultiModelAgent - мульти-модельная архитектура с ролями

Архитектура:
1. Аналитик - анализирует запрос, разбивает на подзадачи, формирует ключевые слова (внутренний)
2. Консультант - готовит технический ответ для пользователя (единственный, кто общается с пользователем)
3. Редактор - упрощает для новичков (внутренний, для валидации)
4. Проверяющий - оценивает качество в JSON (внутренний)

Только Консультант общается с пользователем напрямую.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from orchestration.llm_factory import get_llm
from agents.rag_engine.engine import RAGEngine
from agents.code_interpreter.tool import CodeInterpreterTool
from sqlalchemy.orm import Session as DBSession
from data.postgres.models import Message
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio
import json
import re


@dataclass
class AnalyzerOutput:
    """Структурированный вывод Аналитика"""
    goal: str  # Цель запроса (высокоуровневая формулировка)
    subtasks: List[str] = field(default_factory=list)  # 3-10 конкретных подзадач
    keywords: List[str] = field(default_factory=list)  # Ключевые слова для RAG поиска
    critical_data: Dict[str, Any] = field(default_factory=dict)  # Критически важные данные (G-code, параметры принтера, материалы)
    domain_check: bool = True  # В домене ли запрос (G-code, 3D-печать, параметры слайсера, механика/электроника принтера)
    missing_info: List[str] = field(default_factory=list)  # Что нужно уточнить


@dataclass
class ConsultantOutput:
    """Структурированный вывод Консультанта"""
    brief_summary: str  # Краткий вывод (2-4 предложения)
    technical_breakdown: List[str] = field(default_factory=list)  # Технический разбор по пунктам
    recommended_actions: List[str] = field(default_factory=list)  # Нумерованный список шагов
    print_parameters: Dict[str, Any] = field(default_factory=dict)  # Конкретные параметры печати
    sources: List[str] = field(default_factory=list)  # Ссылки на источники
    what_to_clarify: List[str] = field(default_factory=list)  # Недостающие данные (если есть)


@dataclass
class EditorOutput:
    """Структурированный вывод Редактора (для внутренней валидации)"""
    what_happens: str  # Что происходит
    step_by_step: List[str] = field(default_factory=list)  # Что делать по шагам
    attention_points: List[str] = field(default_factory=list)  # На что обратить внимание (риски, ограничения)


@dataclass
class QACheckerOutput:
    """Структурированный вывод Проверяющего"""
    correctness: int  # 1-10
    completeness: int  # 1-10
    clarity: int  # 1-10
    comments: Dict[str, List[str]] = field(default_factory=dict)  # strengths, issues, risksOrHallucinations


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
    
    async def call_analyzer(self, user_message: str) -> AnalyzerOutput:
        """
        Агент-Аналитик: понимает запрос, разбивает на подзадачи, формирует ключевые слова.
        
        Обязанности:
        - Уточнять цель пользователя, формулировать высокоуровневую «Цель запроса»
        - Разбивать задачу на 3–10 конкретных подзадач
        - Формировать список ключевых слов и фраз для поиска по базе знаний (RAG) и логам G-code
        - Определять, какие фрагменты G-code, параметры принтера, материалы, прошивки критически важны
        - Если запрос вне домена — честно отмечать это
        """
        prompt = f"""Ты — Агент-Аналитик для анализа G-code, 3D-печати и связанных вопросов.

Твоя задача — понять запрос пользователя, разложить его на подзадачи и задать контекст для поиска.

Запрос пользователя: {user_message}

Проанализируй запрос и верни ответ в формате JSON:

{{
    "goal": "Высокоуровневая цель запроса (1-2 предложения)",
    "subtasks": [
        "Подзадача 1",
        "Подзадача 2",
        "Подзадача 3"
    ],
    "keywords": ["ключевое слово 1", "ключевое слово 2", "фраза для поиска"],
    "critical_data": {{
        "gcode_needed": true/false,
        "printer_params": ["параметр1", "параметр2"],
        "materials": ["материал1"],
        "firmware": "название прошивки или null"
    }},
    "domain_check": true/false,
    "missing_info": ["что нужно уточнить 1", "что нужно уточнить 2"]
}}

ВАЖНО:
- Если запрос вне домена (не про G-code, 3D-печать, параметры слайсера, механика/электроника принтера) — установи "domain_check": false
- Не придумывай несуществующие детали
- Формируй 3-10 конкретных подзадач
- Ключевые слова должны быть релевантны для поиска в базе знаний"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Парсим JSON ответ
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return AnalyzerOutput(
                    goal=data.get("goal", ""),
                    subtasks=data.get("subtasks", []),
                    keywords=data.get("keywords", []),
                    critical_data=data.get("critical_data", {}),
                    domain_check=data.get("domain_check", True),
                    missing_info=data.get("missing_info", [])
                )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Ошибка парсинга ответа Аналитика: {e}")
        
        # Fallback: создаем базовый вывод
        return AnalyzerOutput(
            goal="Анализ запроса пользователя",
            subtasks=[],
            keywords=[],
            critical_data={},
            domain_check=True,
            missing_info=[]
        )
    
    async def call_consultant(
        self, 
        user_message: str, 
        analyzer_output: AnalyzerOutput,
        rag_context: str = "",
        user_context: Dict[str, Any] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> ConsultantOutput:
        """
        Агент-Консультант (Эксперт): готовит технически корректный ответ для опытного пользователя.
        
        Обязанности:
        - Опираться на запрос пользователя, вывод Аналитика и RAG-контекст
        - Использовать историю диалога и контекст пользователя
        - Давать подробное инженерное объяснение
        - Приоритизировать данный контекст (база знаний, реальные фрагменты G-code) над общими догадками
        - Явно указывать, если информации не хватает
        - Не придумывать значения параметров и не описывать поведение оборудования, если это не следует из контекста
        - Предоставлять конкретные параметры печати, ссылки на источники
        """
        if user_context is None:
            user_context = {}
        if conversation_history is None:
            conversation_history = []
        
        # Формируем контекст истории
        history_context = ""
        if conversation_history:
            recent_history = conversation_history[-3:]  # Последние 3 сообщения
            history_context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in recent_history
            ])
        
        # Формируем контекст пользователя
        user_context_str = ""
        if user_context.get("printer_model"):
            user_context_str += f"- Принтер: {user_context['printer_model']}\n"
        if user_context.get("material"):
            user_context_str += f"- Материал: {user_context['material']}\n"
        if user_context.get("mentioned_issues"):
            user_context_str += f"- Упомянутые проблемы: {', '.join(user_context['mentioned_issues'])}\n"
        
        prompt = f"""Ты — Агент-Консультант (Эксперт по 3D-печати).

Твоя цель — подготовить технически корректный и практический ответ для опытного пользователя.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{user_message}

КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ (из истории диалога):
{user_context_str if user_context_str else "Контекст не указан"}

ИСТОРИЯ ДИАЛОГА (последние сообщения):
{history_context if history_context else "История отсутствует"}

АНАЛИЗ ОТ АНАЛИТИКА:
- Цель: {analyzer_output.goal}
- Подзадачи: {', '.join(analyzer_output.subtasks[:5])}
- Критически важные данные: {json.dumps(analyzer_output.critical_data, ensure_ascii=False)}

КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ (RAG):
{rag_context if rag_context else "Контекст не найден"}

Строго следуй формату ответа:

**Краткий вывод:**
[2-4 предложения с основным выводом]

**Технический разбор:**
1. [Пункт 1 - структурированное объяснение]
2. [Пункт 2 - структурированное объяснение]
3. [Пункт 3 - структурированное объяснение]

**Рекомендуемые действия:**
1. [Шаг 1 - конкретный шаг с параметрами]
2. [Шаг 2 - конкретный шаг с параметрами]
3. [Шаг 3 - конкретный шаг с параметрами]

**Конкретные параметры печати:**
- Температура сопла: [значение]°C (если известно из контекста)
- Температура стола: [значение]°C (если известно из контекста)
- Скорость печати: [значение] мм/с (если известно из контекста)
- Другие параметры: [если есть в контексте]

**Что уточнить:**
- [Недостающая информация 1]
- [Недостающая информация 2]

**Источники информации:**
- [Ссылка на раздел базы знаний или статью, если есть в RAG-контексте]

КРИТИЧЕСКИ ВАЖНО:
- Приоритет: RAG-контекст > история диалога > общие знания > догадки
- Используй информацию из истории диалога для адаптации ответа
- Если информации не хватает — явно укажи это в разделе "Что уточнить"
- Предоставляй КОНКРЕТНЫЕ параметры печати, если они есть в контексте
- НЕ придумывай значения параметров, если их нет во входе
- НЕ описывай поведение оборудования, если это не следует из контекста
- Если запрос вне домена — честно скажи об этом"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Парсим структурированный ответ
        return self._parse_consultant_output(content)
    
    def _parse_consultant_output(self, content: str) -> ConsultantOutput:
        """Парсинг структурированного ответа Консультанта"""
        brief_summary = ""
        technical_breakdown = []
        recommended_actions = []
        print_parameters = {}
        sources = []
        what_to_clarify = []
        
        # Извлекаем "Краткий вывод"
        brief_match = re.search(r'\*\*Краткий вывод:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if brief_match:
            brief_summary = brief_match.group(1).strip()
        
        # Извлекаем "Технический разбор"
        breakdown_match = re.search(r'\*\*Технический разбор:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if breakdown_match:
            breakdown_text = breakdown_match.group(1)
            # Ищем нумерованные пункты
            technical_breakdown = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', breakdown_text, re.DOTALL)
            technical_breakdown = [item.strip() for item in technical_breakdown if item.strip()]
        
        # Извлекаем "Рекомендуемые действия"
        actions_match = re.search(r'\*\*Рекомендуемые действия:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if actions_match:
            actions_text = actions_match.group(1)
            recommended_actions = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', actions_text, re.DOTALL)
            recommended_actions = [item.strip() for item in recommended_actions if item.strip()]
        
        # Извлекаем "Конкретные параметры печати"
        params_match = re.search(r'\*\*Конкретные параметры печати:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if params_match:
            params_text = params_match.group(1)
            # Ищем параметры в формате "Параметр: значение"
            temp_nozzle = re.search(r'Температура сопла[:\s]+(\d+)', params_text, re.IGNORECASE)
            temp_bed = re.search(r'Температура стола[:\s]+(\d+)', params_text, re.IGNORECASE)
            speed = re.search(r'Скорость печати[:\s]+(\d+)', params_text, re.IGNORECASE)
            
            if temp_nozzle:
                print_parameters["nozzle_temp"] = int(temp_nozzle.group(1))
            if temp_bed:
                print_parameters["bed_temp"] = int(temp_bed.group(1))
            if speed:
                print_parameters["print_speed"] = int(speed.group(1))
        
        # Извлекаем "Источники информации"
        sources_match = re.search(r'\*\*Источники информации:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1)
            sources = re.findall(r'[-•]\s*(.+?)(?=[-•]|$)', sources_text, re.DOTALL)
            sources = [item.strip() for item in sources if item.strip()]
        
        # Извлекаем "Что уточнить"
        clarify_match = re.search(r'\*\*Что уточнить:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if clarify_match:
            clarify_text = clarify_match.group(1)
            what_to_clarify = re.findall(r'[-•]\s*(.+?)(?=[-•]|$)', clarify_text, re.DOTALL)
            what_to_clarify = [item.strip() for item in what_to_clarify if item.strip()]
        
        # Если не удалось распарсить, используем весь контент как краткий вывод
        if not brief_summary:
            brief_summary = content[:500]
        
        return ConsultantOutput(
            brief_summary=brief_summary,
            technical_breakdown=technical_breakdown,
            recommended_actions=recommended_actions,
            print_parameters=print_parameters,
            sources=sources,
            what_to_clarify=what_to_clarify
        )
    
    async def call_editor(self, consultant_output: ConsultantOutput) -> EditorOutput:
        """
        Агент-Редактор: переписывает ответ Консультанта простым языком для новичков.
        
        Обязанности:
        - Упрощать формулировки, разбивать объяснения на логичные блоки
        - Сохранять все ключевые технические моменты, указания по безопасности и ограничения
        - Объяснять термины в скобках при первом упоминании
        - Не добавлять новых фактов и не менять технический смысл
        """
        consultant_text = f"""Краткий вывод:
{consultant_output.brief_summary}

Технический разбор:
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(consultant_output.technical_breakdown))}

Рекомендуемые действия:
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(consultant_output.recommended_actions))}
"""
        
        prompt = f"""Ты — Агент-Редактор (Объяснитель для новичков).

Твоя цель — переписать технический ответ простым языком для новичка, без потери важных ограничений и рисков.

ИСХОДНЫЙ ОТВЕТ ОТ КОНСУЛЬТАНТА:
{consultant_text}

Строго следуй формату ответа:

**Что происходит:**
[Простое объяснение ситуации, что происходит, почему это важно]

**Что делать по шагам:**
1. [Шаг 1 простым языком]
2. [Шаг 2 простым языком]
3. [Шаг 3 простым языком]

**На что обратить внимание (риски, ограничения):**
- [Важный момент 1 - объясни простыми словами]
- [Важный момент 2 - объясни простыми словами]

КРИТИЧЕСКИ ВАЖНО:
- Объясняй термины в скобках при первом упоминании (например: "экструдер (устройство, которое плавит пластик)")
- Сохраняй ВСЕ ключевые технические моменты, указания по безопасности и ограничения
- НЕ добавляй новых фактов
- НЕ меняй технический смысл
- Используй простые аналогии и примеры"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Парсим структурированный ответ
        return self._parse_editor_output(content)
    
    def _parse_editor_output(self, content: str) -> EditorOutput:
        """Парсинг структурированного ответа Редактора"""
        what_happens = ""
        step_by_step = []
        attention_points = []
        
        # Извлекаем "Что происходит"
        happens_match = re.search(r'\*\*Что происходит:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if happens_match:
            what_happens = happens_match.group(1).strip()
        
        # Извлекаем "Что делать по шагам"
        steps_match = re.search(r'\*\*Что делать по шагам:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if steps_match:
            steps_text = steps_match.group(1)
            step_by_step = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', steps_text, re.DOTALL)
            step_by_step = [item.strip() for item in step_by_step if item.strip()]
        
        # Извлекаем "На что обратить внимание"
        attention_match = re.search(r'\*\*На что обратить внимание.*?:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if attention_match:
            attention_text = attention_match.group(1)
            attention_points = re.findall(r'[-•]\s*(.+?)(?=[-•]|$)', attention_text, re.DOTALL)
            attention_points = [item.strip() for item in attention_points if item.strip()]
        
        # Если не удалось распарсить, используем весь контент
        if not what_happens:
            what_happens = content[:500]
        
        return EditorOutput(
            what_happens=what_happens,
            step_by_step=step_by_step,
            attention_points=attention_points
        )
    
    async def call_qa_checker(self, consultant_output: ConsultantOutput) -> QACheckerOutput:
        """
        Агент-Проверяющий: оценивает качество ответа Консультанта и подсвечивает риски.
        
        Обязанности:
        - Выставлять оценки correctness, completeness, clarity по шкале 1–10
        - Кратко перечислять сильные стороны ответа, проблемы и возможные галлюцинации/опасные советы
        """
        consultant_text = f"""Краткий вывод:
{consultant_output.brief_summary}

Технический разбор:
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(consultant_output.technical_breakdown))}

Рекомендуемые действия:
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(consultant_output.recommended_actions))}

Что уточнить:
{chr(10).join(f"- {item}" for item in consultant_output.what_to_clarify)}
"""
        
        prompt = f"""Ты — Агент-Проверяющий (QA-оценщик).

Твоя цель — оценить качество ответа Консультанта и подсветить риски.

ОТВЕТ КОНСУЛЬТАНТА:
{consultant_text}

Оцени ответ по 3 критериям (1-10) и верни результат в формате JSON:

{{
    "correctness": <1-10>,
    "completeness": <1-10>,
    "clarity": <1-10>,
    "comments": {{
        "strengths": ["сильная сторона 1", "сильная сторона 2"],
        "issues": ["проблема 1", "проблема 2"],
        "risksOrHallucinations": ["риск/галлюцинация 1", "риск/галлюцинация 2"]
    }}
}}

Критерии оценки:
- correctness: техническая корректность, отсутствие выдуманных фактов
- completeness: полнота ответа, покрытие всех аспектов вопроса
- clarity: ясность изложения, структурированность

В comments укажи:
- strengths: что сделано хорошо
- issues: что можно улучшить
- risksOrHallucinations: возможные галлюцинации, выдуманные параметры, опасные советы"""
        
        response_obj = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        # Парсим JSON из ответа
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return QACheckerOutput(
                    correctness=data.get("correctness", 7),
                    completeness=data.get("completeness", 7),
                    clarity=data.get("clarity", 7),
                    comments=data.get("comments", {
                        "strengths": [],
                        "issues": [],
                        "risksOrHallucinations": []
                    })
                )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Ошибка парсинга ответа Проверяющего: {e}")
        
        # Если не удалось распарсить, возвращаем дефолтные значения
        return QACheckerOutput(
            correctness=7,
            completeness=7,
            clarity=7,
            comments={
                "strengths": [],
                "issues": [],
                "risksOrHallucinations": []
            }
        )
    
    def _load_conversation_history(self, session_id: int, db: DBSession) -> List[Dict[str, str]]:
        """Загрузка истории диалога из БД"""
        if not db or not session_id:
            return []
        
        try:
            from data.postgres.models import Message
            messages = db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at).all()
            
            history = []
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            return history
        except Exception as e:
            print(f"⚠️ Ошибка загрузки истории: {e}")
            return []
    
    def _extract_user_context_from_history(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Извлечение контекста пользователя из истории диалога"""
        context = {
            "printer_model": None,
            "material": None,
            "mentioned_issues": [],
            "mentioned_settings": {}
        }
        
        # Анализируем историю для извлечения информации
        for msg in history:
            if msg["role"] == "user":
                content = msg["content"].lower()
                
                # Ищем упоминания принтера
                printer_keywords = ["ender", "prusa", "bamboo", "принтер", "printer"]
                for keyword in printer_keywords:
                    if keyword in content:
                        # Пытаемся извлечь модель
                        words = msg["content"].split()
                        for i, word in enumerate(words):
                            if keyword in word.lower():
                                if i + 1 < len(words):
                                    context["printer_model"] = words[i+1] if i+1 < len(words) else None
                                break
                
                # Ищем упоминания материала
                material_keywords = ["pla", "petg", "abs", "tpu", "пластик", "материал"]
                for keyword in material_keywords:
                    if keyword in content:
                        context["material"] = keyword.upper()
                
                # Ищем упоминания проблем
                issue_keywords = ["warping", "stringing", "layer shift", "adhesion", "трещин", "отслоен", "сопли"]
                for keyword in issue_keywords:
                    if keyword in content:
                        context["mentioned_issues"].append(keyword)
        
        return context
    
    async def _should_ask_question(self, analyzer_output: AnalyzerOutput, consultant_output: ConsultantOutput) -> bool:
        """Определяет, нужно ли задать вопрос вместо ответа"""
        # Если есть критически важные данные, которые не указаны
        if analyzer_output.critical_data:
            if analyzer_output.critical_data.get("gcode_needed") and not any("g-code" in item.lower() or "gcode" in item.lower() for item in analyzer_output.missing_info):
                return True
        
        # Если много недостающей информации
        if len(consultant_output.what_to_clarify) >= 3:
            return True
        
        # Если нет контекста из RAG и запрос требует специфических знаний
        if not analyzer_output.keywords and len(analyzer_output.subtasks) > 5:
            return True
        
        return False
    
    async def _generate_clarifying_question(self, analyzer_output: AnalyzerOutput, consultant_output: ConsultantOutput, user_context: Dict[str, Any]) -> str:
        """Генерация уточняющего вопроса"""
        # Определяем, какой вопрос задать
        questions = []
        
        # Проверяем принтер
        if not user_context.get("printer_model"):
            questions.append("Какой у вас принтер? (например, Ender 3, Prusa i3, Bamboo Lab X1)")
        
        # Проверяем материал
        if not user_context.get("material"):
            questions.append("Какой пластик вы используете? (PLA, PETG, ABS, TPU)")
        
        # Проверяем конкретную проблему
        if analyzer_output.critical_data.get("gcode_needed") and not any("g-code" in item.lower() for item in consultant_output.what_to_clarify):
            questions.append("Можете приложить G-code файл или описать параметры печати?")
        
        # Если есть другие важные вопросы
        if consultant_output.what_to_clarify:
            # Берем первый вопрос из списка
            first_clarify = consultant_output.what_to_clarify[0]
            if "температур" in first_clarify.lower() or "temp" in first_clarify.lower():
                questions.append("Какая температура сопла и стола у вас установлена?")
            elif "скорост" in first_clarify.lower() or "speed" in first_clarify.lower():
                questions.append("Какая скорость печати используется?")
            elif "дефект" in first_clarify.lower() or "проблем" in first_clarify.lower():
                questions.append("Что именно вы видите на детали? (трещины, отслоение, сопли, смещение слоев)")
        
        if questions:
            return questions[0]  # Возвращаем первый вопрос
        
        # Если нет конкретных вопросов, задаем общий
        return "Можете уточнить детали вашей проблемы? Например, какой принтер, материал и что именно происходит?"
    
    async def run(self, user_message: str, session_id: int, db: DBSession) -> str:
        """
        Главный pipeline мультиагентной системы с поддержкой интерактивного диалога.
        
        Цикл работы:
        1. Загрузка истории диалога
        2. Аналитик → формулирует цель, подзадачи, ключевые слова, требования к контексту
        3. RAG поиск → на основе ключевых слов от Аналитика + истории диалога
        4. Консультант → строит технический ответ (единственный, кто общается с пользователем)
        5. Проверка: нужно ли задать вопрос вместо ответа
        6. Редактор → создает упрощенную версию (внутренняя валидация)
        7. Проверяющий → оценивает ответ Консультанта (внутренняя валидация)
        
        Пользователю возвращается только ответ Консультанта или уточняющий вопрос.
        """
        
        print("\n🔄 Multi-Model Pipeline Started...")
        
        # ===== ШАГ 0: ЗАГРУЗКА ИСТОРИИ ДИАЛОГА =====
        conversation_history = self._load_conversation_history(session_id, db)
        user_context = self._extract_user_context_from_history(conversation_history)
        
        # Обогащаем контекст информацией из сессии
        if db and session_id:
            from data.postgres.models import Session as SessionModel
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                if session.printer_model and not user_context.get("printer_model"):
                    user_context["printer_model"] = session.printer_model
                if session.material and not user_context.get("material"):
                    user_context["material"] = session.material
        
        print(f"   📜 История диалога: {len(conversation_history)} сообщений")
        print(f"   🖨️  Принтер: {user_context.get('printer_model', 'не указан')}")
        print(f"   🧪 Материал: {user_context.get('material', 'не указан')}")
        
        # Формируем контекст для Аналитика (включая историю)
        full_context = user_message
        if conversation_history:
            # Добавляем последние 3 сообщения из истории для контекста
            recent_history = conversation_history[-3:]
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])
            full_context = f"Контекст предыдущего диалога:\n{history_text}\n\nТекущий запрос: {user_message}"
        
        # ===== ШАГ 1: АНАЛИТИК (внутренний) =====
        print("1️⃣ Analyzer: Анализирую запрос...")
        analyzer_output = await self.call_analyzer(full_context)
        print(f"   → Цель: {analyzer_output.goal[:80]}...")
        print(f"   → Подзадач: {len(analyzer_output.subtasks)}")
        print(f"   → Ключевых слов: {len(analyzer_output.keywords)}")
        
        if not analyzer_output.domain_check:
            return "Извините, ваш запрос выходит за рамки моей компетенции (G-code, 3D-печать, параметры слайсера, механика/электроника принтера). Я могу помочь только с вопросами в этой области."
        
        # ===== ШАГ 2: ПОИСК В KB (на основе ключевых слов от Аналитика + истории) =====
        print("2️⃣ RAG: Ищу в базе знаний...")
        rag_context = ""
        rag_sources = []
        try:
            # Используем ключевые слова от Аналитика для поиска
            search_query = " ".join(analyzer_output.keywords) if analyzer_output.keywords else user_message
            
            # Обогащаем запрос информацией из истории
            if user_context.get("printer_model"):
                search_query += f" {user_context['printer_model']}"
            if user_context.get("material"):
                search_query += f" {user_context['material']}"
            if user_context.get("mentioned_issues"):
                search_query += " " + " ".join(user_context["mentioned_issues"])
            
            kb_results = await self.rag.search(search_query, top_k=5)
            rag_context = kb_results.augmented_context if hasattr(kb_results, 'augmented_context') else ""
            rag_sources = kb_results.sources if hasattr(kb_results, 'sources') else []
            total_results = kb_results.total_results if hasattr(kb_results, 'total_results') else 0
            
            # Добавляем источники в контекст для Консультанта
            if rag_sources:
                sources_text = "\n".join([f"- {source.get('source', 'unknown')}" for source in rag_sources[:3]])
                rag_context += f"\n\nИсточники:\n{sources_text}"
            print(f"   → Найдено {total_results} релевантных документов")
        except Exception as e:
            print(f"   ⚠️ Ошибка RAG: {e}")
            rag_context = ""
        
        # ===== ШАГ 3: КОНСУЛЬТАНТ (единственный, кто общается с пользователем) =====
        print("3️⃣ Consultant: Готовлю технический ответ...")
        consultant_output = await self.call_consultant(
            user_message, 
            analyzer_output, 
            rag_context,
            user_context,
            conversation_history
        )
        print(f"   → Краткий вывод: {consultant_output.brief_summary[:80]}...")
        
        # Добавляем источники из RAG в ответ Консультанта
        if rag_sources:
            consultant_output.sources.extend([
                source.get('source', 'unknown') 
                for source in rag_sources[:3]
            ])
        
        # ===== ШАГ 3.5: ПРОВЕРКА - НУЖНО ЛИ ЗАДАТЬ ВОПРОС? =====
        should_ask = await self._should_ask_question(analyzer_output, consultant_output)
        if should_ask and len(conversation_history) < 5:  # Задаем вопросы только в начале диалога
            question = await self._generate_clarifying_question(analyzer_output, consultant_output, user_context)
            print(f"   ❓ Задаю уточняющий вопрос вместо ответа")
            return f"Чтобы дать вам более точную рекомендацию, мне нужно уточнить:\n\n**{question}**\n\nПосле вашего ответа я смогу предоставить конкретные параметры печати и шаги по решению проблемы."
        
        # ===== ШАГ 4: РЕДАКТОР (внутренняя валидация) =====
        print("4️⃣ Editor: Создаю упрощенную версию (внутренняя валидация)...")
        editor_output = await self.call_editor(consultant_output)
        # Редактор работает внутренне, его вывод не идет пользователю напрямую
        
        # ===== ШАГ 5: ПРОВЕРЯЮЩИЙ (внутренняя валидация) =====
        print("5️⃣ QA Checker: Оцениваю качество (внутренняя валидация)...")
        qa_output = await self.call_qa_checker(consultant_output)
        # Проверяющий работает внутренне, его вывод используется для мета-информации
        
        # ===== ФОРМИРОВАНИЕ ФИНАЛЬНОГО ОТВЕТА =====
        # Пользователю возвращается только ответ Консультанта
        final_response_parts = []
        
        # Краткий вывод
        if consultant_output.brief_summary:
            final_response_parts.append(f"**Краткий вывод:**\n{consultant_output.brief_summary}")
        
        # Технический разбор
        if consultant_output.technical_breakdown:
            final_response_parts.append("\n**Технический разбор:**")
            for i, item in enumerate(consultant_output.technical_breakdown, 1):
                final_response_parts.append(f"{i}. {item}")
        
        # Рекомендуемые действия
        if consultant_output.recommended_actions:
            final_response_parts.append("\n**Рекомендуемые действия:**")
            for i, item in enumerate(consultant_output.recommended_actions, 1):
                final_response_parts.append(f"{i}. {item}")
        
        # Конкретные параметры печати
        if consultant_output.print_parameters:
            final_response_parts.append("\n**Конкретные параметры печати:**")
            if consultant_output.print_parameters.get("nozzle_temp"):
                final_response_parts.append(f"- Температура сопла: {consultant_output.print_parameters['nozzle_temp']}°C")
            if consultant_output.print_parameters.get("bed_temp"):
                final_response_parts.append(f"- Температура стола: {consultant_output.print_parameters['bed_temp']}°C")
            if consultant_output.print_parameters.get("print_speed"):
                final_response_parts.append(f"- Скорость печати: {consultant_output.print_parameters['print_speed']} мм/с")
            for key, value in consultant_output.print_parameters.items():
                if key not in ["nozzle_temp", "bed_temp", "print_speed"]:
                    final_response_parts.append(f"- {key}: {value}")
        
        # Источники информации
        if consultant_output.sources:
            final_response_parts.append("\n**Источники информации:**")
            for source in consultant_output.sources:
                final_response_parts.append(f"- {source}")
        
        # Что уточнить
        if consultant_output.what_to_clarify:
            final_response_parts.append("\n**Что уточнить:**")
            for item in consultant_output.what_to_clarify:
                final_response_parts.append(f"- {item}")
        
        # Мета-информация об оценке качества (опционально, можно убрать)
        if qa_output.correctness < 7 or qa_output.completeness < 7:
            final_response_parts.append(f"\n---\n*Оценка качества: Корректность {qa_output.correctness}/10, Полнота {qa_output.completeness}/10*")
        
        final_response = "\n".join(final_response_parts)
        
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

