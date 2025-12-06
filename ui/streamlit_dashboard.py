"""Streamlit Web Dashboard для мониторинга"""
import streamlit as st
import asyncio
from orchestration.graph import orchestration_graph
from agents.hardware.tool import hardware_tool
import plotly.graph_objects as go
from datetime import datetime, timedelta


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
            ["Мониторинг", "Управление", "Анализ", "База знаний"]
        )
    
    if page == "Мониторинг":
        show_monitoring()
    elif page == "Управление":
        show_control()
    elif page == "Анализ":
        show_analysis()
    elif page == "База знаний":
        show_knowledge_base()


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


if __name__ == "__main__":
    main()

