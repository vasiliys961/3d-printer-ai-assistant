"""Тесты базы знаний"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.rag_engine.engine import RAGEngine


async def test_knowledge_base():
    """Тест загрузки и поиска в базе знаний"""
    print("🧪 Тестирование базы знаний...")
    
    # Инициализация
    rag_engine = RAGEngine(db_path="./data/chroma_test")
    
    # Загрузка
    print("📚 Загрузка базы знаний...")
    rag_engine.ingest_knowledge_base("./data/knowledge_base")
    
    # Поиск
    print("🔍 Тестирование поиска...")
    results = await rag_engine.search("PLA температура", top_k=3)
    
    print(f"✅ Найдено результатов: {results.total_results}")
    print(f"📄 Релевантные чанки: {len(results.relevant_chunks)}")
    
    if results.relevant_chunks:
        print("\nПервый результат:")
        print(results.relevant_chunks[0][:200] + "...")
    
    print("✅ Тест базы знаний пройден!")


if __name__ == "__main__":
    asyncio.run(test_knowledge_base())

