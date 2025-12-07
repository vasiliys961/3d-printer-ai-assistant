"""Streamlit Web Dashboard для мониторинга"""
import streamlit as st
import asyncio
import sys
import os
import requests
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.graph import orchestration_graph
from agents.hardware.tool import hardware_tool
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import API_PORT

API_BASE_URL = f"http://localhost:{API_PORT}"


st.set_page_config(
    page_title="3D Printer AI Assistant",
    page_icon="🖨️",
    layout="wide"
)


async def get_printer_status():
    """Получить статус принтера"""
    status = await hardware_tool.get_status()
    temp = await hardware_tool.get_temperature()
    return status, temp


def main():
    """Главная функция dashboard"""
    st.title("🖨️ 3D Printer AI Assistant Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("Навигация")
        page = st.radio(
            "Выберите страницу",
            ["Мониторинг", "Управление", "Анализ", "База знаний", "История диалогов", "Обучение", "Метрики"]
        )
        
        # Выбор пользователя для просмотра данных
        user_id = st.number_input("User ID", min_value=1, value=1, step=1)
        st.session_state.user_id = user_id
    
    if page == "Мониторинг":
        show_monitoring()
    elif page == "Управление":
        show_control()
    elif page == "Анализ":
        show_analysis()
    elif page == "База знаний":
        show_knowledge_base()
    elif page == "История диалогов":
        show_chat_history()
    elif page == "Обучение":
        show_learning_progress()
    elif page == "Метрики":
        show_metrics()


def show_monitoring():
    """Страница мониторинга"""
    st.header("Мониторинг принтера")
    
    # Обновление статуса
    if st.button("Обновить статус"):
        status, temp = asyncio.run(get_printer_status())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Температура стола", f"{temp.get('bed', 0):.1f}°C")
        
        with col2:
            st.metric("Температура сопла", f"{temp.get('nozzle', 0):.1f}°C")
        
        with col3:
            st.metric("Статус", "🟢 Активен" if status else "🔴 Недоступен")
        
        # График температуры (заглушка)
        st.subheader("График температуры")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[datetime.now() - timedelta(minutes=i) for i in range(60, 0, -1)],
            y=[temp.get('bed', 0)] * 60,
            name="Стол",
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=[datetime.now() - timedelta(minutes=i) for i in range(60, 0, -1)],
            y=[temp.get('nozzle', 0)] * 60,
            name="Сопло",
            line=dict(color='red')
        ))
        fig.update_layout(title="Температура за последний час")
        st.plotly_chart(fig, use_container_width=True)
        
        # Детальный статус
        with st.expander("Детальный статус"):
            st.json(status)


def show_control():
    """Страница управления"""
    st.header("Управление принтером")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Температура")
        bed_temp = st.slider("Температура стола", 0, 120, 60)
        nozzle_temp = st.slider("Температура сопла", 0, 300, 200)
        
        if st.button("Установить температуру"):
            result = asyncio.run(hardware_tool.set_temperature(bed_temp, nozzle_temp))
            if result:
                st.success("Температура установлена!")
            else:
                st.error("Ошибка при установке температуры")
    
    with col2:
        st.subheader("Управление печатью")
        gcode_file = st.text_input("G-code файл")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("▶️ Начать печать"):
                if gcode_file:
                    result = asyncio.run(hardware_tool.start_print(gcode_file))
                    if result:
                        st.success("Печать начата!")
                    else:
                        st.error("Ошибка при запуске печати")
                else:
                    st.warning("Укажите G-code файл")
        
        with col_b:
            if st.button("⏸️ Пауза"):
                result = asyncio.run(hardware_tool.pause_print())
                if result:
                    st.success("Печать приостановлена")
        
        col_c, col_d = st.columns(2)
        with col_c:
            if st.button("▶️ Продолжить"):
                result = asyncio.run(hardware_tool.resume_print())
                if result:
                    st.success("Печать возобновлена")
        
        with col_d:
            if st.button("⏹️ Остановить"):
                result = asyncio.run(hardware_tool.stop_print())
                if result:
                    st.success("Печать остановлена")
        
        if st.button("🏠 Домой оси"):
            result = asyncio.run(hardware_tool.home_axes())
            if result:
                st.success("Оси отправлены в исходное положение")


def show_analysis():
    """Страница анализа"""
    st.header("Анализ G-code и изображений")
    
    tab1, tab2 = st.tabs(["G-code", "Изображения"])
    
    with tab1:
        st.subheader("Анализ G-code")
        gcode_text = st.text_area("Вставьте G-code", height=300)
        
        if st.button("Анализировать G-code"):
            if gcode_text:
                result = asyncio.run(orchestration_graph.process(
                    f"Проанализируй этот G-code:\n\n{gcode_text}",
                    context={"gcode_content": gcode_text}
                ))
                st.write(result.get("response", ""))
            else:
                st.warning("Введите G-code для анализа")
    
    with tab2:
        st.subheader("Анализ изображений")
        uploaded_file = st.file_uploader("Загрузите изображение", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            # Сохраняем файл
            import os
            os.makedirs("data/temp", exist_ok=True)
            file_path = f"data/temp/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.image(uploaded_file, caption="Загруженное изображение")
            
            if st.button("Анализировать изображение"):
                result = asyncio.run(orchestration_graph.process(
                    "Проанализируй это изображение печати",
                    context={"image_path": file_path}
                ))
                st.write(result.get("response", ""))


def show_knowledge_base():
    """Страница базы знаний"""
    st.header("База знаний")
    
    query = st.text_input("Поиск в базе знаний")
    
    if st.button("Поиск"):
        if query:
            from agents.rag_engine.tool import rag_engine_tool
            result = asyncio.run(rag_engine_tool.search(query, top_k=5))
            
            st.subheader("Результаты поиска")
            for i, res in enumerate(result.get("results", []), 1):
                with st.expander(f"Результат {i} (score: {res.get('score', 0):.2f})"):
                    st.write(res.get("text", ""))
                    st.json(res.get("metadata", {}))
        else:
            st.warning("Введите запрос для поиска")


def show_chat_history():
    """Страница истории диалогов"""
    st.header("История диалогов")
    
    user_id = st.session_state.get("user_id", 1)
    
    # Получаем сессии пользователя через API
    try:
        # Используем прямой запрос к БД через импорт (если API недоступен)
        try:
            response = requests.get(f"{API_BASE_URL}/sessions", params={"user_id": user_id}, timeout=2)
            if response.status_code == 200:
                sessions = response.json().get("sessions", [])
            else:
                sessions = []
        except requests.exceptions.RequestException:
            # Fallback: используем прямой доступ к БД
            from data.postgres.database import SessionLocal
            from data.postgres.models import Session as SessionModel
            db = SessionLocal()
            try:
                db_sessions = db.query(SessionModel).filter(SessionModel.user_id == user_id).all()
                sessions = [{"id": s.id, "started_at": str(s.started_at), "printer_model": s.printer_model} for s in db_sessions]
            finally:
                db.close()
    except Exception as e:
        sessions = []
        st.warning(f"Не удалось подключиться к API: {e}")
    
    if sessions:
        session_ids = [s["id"] for s in sessions]
        selected_session = st.selectbox("Выберите сессию", session_ids, format_func=lambda x: f"Сессия {x}")
        
        if selected_session:
            # Получаем историю выбранной сессии
            try:
                try:
                    history_response = requests.get(f"{API_BASE_URL}/sessions/{selected_session}/history", timeout=2)
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        messages = history_data.get("messages", [])
                    else:
                        messages = []
                except requests.exceptions.RequestException:
                    # Fallback: прямой доступ к БД
                    from data.postgres.database import SessionLocal
                    from data.postgres.models import Message as MessageModel
                    db = SessionLocal()
                    try:
                        db_messages = db.query(MessageModel).filter(
                            MessageModel.session_id == selected_session
                        ).order_by(MessageModel.created_at).all()
                        messages = [
                            {
                                "role": m.role,
                                "content": m.content,
                                "created_at": str(m.created_at)
                            }
                            for m in db_messages
                        ]
                    finally:
                        db.close()
                
                if messages:
                    st.subheader(f"История сессии {selected_session}")
                    st.info(f"Всего сообщений: {len(messages)}")
                    
                    # Отображаем сообщения
                    for msg in messages:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        created_at = msg.get("created_at", "")
                        
                        if role == "user":
                            with st.chat_message("user"):
                                st.write(content)
                                if created_at:
                                    st.caption(created_at)
                        elif role == "assistant":
                            with st.chat_message("assistant"):
                                st.markdown(content)
                                if created_at:
                                    st.caption(created_at)
                        elif role == "system":
                            st.error(f"Система: {content}")
                else:
                    st.info("В этой сессии пока нет сообщений")
            except Exception as e:
                st.error(f"Ошибка: {e}")
    else:
        st.info("Нет доступных сессий для этого пользователя")


def show_learning_progress():
    """Страница прогресса обучения"""
    st.header("Прогресс обучения")
    
    user_id = st.session_state.get("user_id", 1)
    
    try:
        try:
            response = requests.get(f"{API_BASE_URL}/learning/progress", params={"user_id": user_id}, timeout=2)
            if response.status_code == 200:
                progress = response.json()
            else:
                progress = {}
        except requests.exceptions.RequestException:
            # Fallback: прямой доступ к БД
            from agents.learning_mode.progress_tracker import ProgressTracker
            from data.postgres.database import SessionLocal
            db = SessionLocal()
            try:
                tracker = ProgressTracker(db)
                progress = tracker.get_user_progress(user_id)
                next_lesson = tracker.get_next_lesson(user_id)
                if next_lesson:
                    progress["next_lesson"] = next_lesson
            finally:
                db.close()
        
        if progress:
            # Общий прогресс
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Пройдено уроков", len(progress.get("completed_lessons", [])))
            with col2:
                st.metric("Всего уроков", progress.get("total_lessons", 0))
            with col3:
                st.metric("Прогресс", f"{progress.get('progress_percent', 0)}%")
            
            # Прогресс-бар
            progress_percent = progress.get("progress_percent", 0)
            st.progress(progress_percent / 100)
            
            # Следующий урок
            next_lesson = progress.get("next_lesson")
            if next_lesson:
                st.subheader("Следующий урок")
                if isinstance(next_lesson, dict):
                    st.info(f"**{next_lesson.get('title', next_lesson.get('id', ''))}**\n\n{next_lesson.get('description', '')}")
                else:
                    st.info(f"**{next_lesson.title}**\n\n{next_lesson.content[:200]}...")
                if st.button("Начать урок"):
                    st.success("Урок начат!")
            else:
                st.success("🎉 Все уроки пройдены!")
            
            # Список пройденных уроков
            if progress.get("completed_lessons"):
                st.subheader("Пройденные уроки")
                for lesson_id in progress.get("completed_lessons", []):
                    st.success(f"✅ {lesson_id}")
        else:
            st.info("Прогресс обучения пока не доступен")
    except Exception as e:
        st.error(f"Ошибка: {e}")
        st.info(f"Убедитесь, что API сервер запущен на порту {API_PORT}")


def show_metrics():
    """Страница метрик производительности"""
    st.header("Метрики производительности")
    
    try:
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=2)
            if response.status_code == 200:
                metrics_data = response.json()
                metrics = metrics_data.get("metrics", {})
            else:
                metrics = {}
        except requests.exceptions.RequestException:
            # Fallback: используем метрики напрямую
            from utils.metrics import metrics_collector
            metrics = metrics_collector.get_stats(limit=100)
        
        if metrics:
            # Основные метрики
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Всего запросов", metrics.get("total_requests", 0))
            
            with col2:
                avg_time = metrics.get("avg_execution_time_ms", 0)
                st.metric("Среднее время", f"{avg_time:.2f}ms")
            
            with col3:
                avg_llm = metrics.get("avg_llm_calls", 0)
                st.metric("Среднее LLM вызовов", f"{avg_llm:.2f}")
            
            with col4:
                avg_tokens = metrics.get("avg_tokens_per_request", 0)
                st.metric("Среднее токенов", f"{avg_tokens:.0f}")
            
            # Дополнительные метрики
            col5, col6 = st.columns(2)
            with col5:
                avg_rag = metrics.get("avg_rag_searches", 0)
                st.metric("Среднее RAG поисков", f"{avg_rag:.2f}")
            with col6:
                total_errors = metrics.get("total_errors", 0)
                st.metric("Всего ошибок", total_errors, delta=None if total_errors == 0 else f"-{total_errors}")
            
            # Графики
            st.subheader("Распределение времени выполнения")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=["Среднее время"],
                y=[avg_time],
                name="Среднее время (мс)",
                marker_color='lightblue'
            ))
            fig.update_layout(
                title="Среднее время выполнения запросов",
                yaxis_title="Время (мс)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Статистика по ошибкам
            if total_errors > 0:
                st.warning(f"⚠️ Всего ошибок: {total_errors}")
                st.info("Проверьте логи в `logs/errors.log` для деталей")
        else:
            st.info("Метрики пока не собраны. Выполните несколько запросов к API.")
    except Exception as e:
        st.error(f"Ошибка: {e}")
        st.info("Убедитесь, что API сервер запущен")


if __name__ == "__main__":
    main()

