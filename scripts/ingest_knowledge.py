"""
Скрипт для загрузки базы знаний в RAG Engine
Поддерживает новую структуру с категориями и метаданными
"""
import sys
import os
import json
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.rag_engine.engine import RAGEngine


async def ingest_knowledge_base():
    """Загрузить базу знаний в ChromaDB"""
    # Инициализируем RAG Engine
    rag_engine = RAGEngine(db_path="./data/chroma")
    
    # Путь к базе знаний
    kb_path = "./data/knowledge_base"
    
    print(f"📚 Загрузка базы знаний из {kb_path}...")
    print(f"📂 Структура: materials/, troubleshooting/, printer_profiles/, gcode_commands/, calibration/, slicer_settings/")
    
    # Загружаем документы
    rag_engine.ingest_knowledge_base(kb_path)
    
    # Подсчитываем количество документов
    kb_path_obj = Path(kb_path)
    json_files = list(kb_path_obj.rglob("*.json"))
    total_docs = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    total_docs += len(data)
                else:
                    total_docs += 1
        except:
            pass
    
    print(f"✅ База знаний успешно загружена в ChromaDB!")
    print(f"📊 Загружено документов: {total_docs}")
    print(f"📁 Путь к ChromaDB: ./data/chroma")
    print(f"💡 Для использования выполните поиск через RAG Engine")


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_knowledge_base())

