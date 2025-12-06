"""
Скрипт для загрузки базы знаний в RAG Engine
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
    
    # Загружаем документы
    rag_engine.ingest_knowledge_base(kb_path)
    
    print("✅ База знаний успешно загружена в ChromaDB!")
    print(f"📁 Путь к ChromaDB: ./data/chroma")


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_knowledge_base())

