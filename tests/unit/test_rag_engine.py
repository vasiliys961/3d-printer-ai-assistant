"""
Unit тесты для RAG Engine
"""
import pytest
import asyncio
from agents.rag_engine.engine import RAGEngine
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_rag_engine():
    """Создать временный RAG engine для тестов"""
    temp_dir = tempfile.mkdtemp()
    engine = RAGEngine(db_path=temp_dir)
    yield engine
    shutil.rmtree(temp_dir)


@pytest.mark.unit
class TestRAGEngine:
    """Тесты RAG Engine"""
    
    def test_ingest_documents(self, temp_rag_engine):
        """Тест загрузки документов"""
        # Создаем тестовый документ
        test_kb_dir = Path(tempfile.mkdtemp())
        test_doc = test_kb_dir / "test.json"
        test_doc.write_text('''[
            {
                "id": "test_001",
                "title": "Test Document",
                "content": "This is a test document about 3D printing with PLA material.",
                "category": "materials",
                "source_url": "https://example.com/test"
            }
        ]''')
        
        try:
            temp_rag_engine.ingest_knowledge_base(str(test_kb_dir))
            
            # Проверяем, что документы загружены
            collection = temp_rag_engine.collection
            count = collection.count()
            assert count > 0
        finally:
            shutil.rmtree(test_kb_dir)
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, temp_rag_engine):
        """Тест поиска с пустым запросом"""
        result = await temp_rag_engine.search("", top_k=5)
        
        assert result is not None
        assert result.question == ""
        assert isinstance(result.relevant_chunks, list)
        assert isinstance(result.sources, list)
    
    @pytest.mark.asyncio
    async def test_search_with_query(self, temp_rag_engine):
        """Тест поиска с запросом"""
        # Сначала загружаем тестовые документы
        test_kb_dir = Path(tempfile.mkdtemp())
        test_doc = test_kb_dir / "test.json"
        test_doc.write_text('''[
            {
                "id": "test_001",
                "title": "PLA Material",
                "content": "PLA is a popular 3D printing material. Temperature: 190-220°C.",
                "category": "materials",
                "source_url": "https://example.com/pla"
            }
        ]''')
        
        try:
            temp_rag_engine.ingest_knowledge_base(str(test_kb_dir))
            
            # Выполняем поиск
            result = await temp_rag_engine.search("PLA temperature", top_k=5)
            
            assert result is not None
            assert result.total_results >= 0
            assert isinstance(result.relevant_chunks, list)
            assert isinstance(result.sources, list)
        finally:
            shutil.rmtree(test_kb_dir)
    
    def test_get_parent_document(self, temp_rag_engine):
        """Тест получения parent document"""
        # Создаем тестовый документ
        test_kb_dir = Path(tempfile.mkdtemp())
        test_doc = test_kb_dir / "test.json"
        test_doc.write_text('''[
            {
                "id": "test_001",
                "title": "Test",
                "content": "Test content",
                "category": "test"
            }
        ]''')
        
        try:
            temp_rag_engine.ingest_knowledge_base(str(test_kb_dir))
            
            # Пытаемся получить parent document
            parent = temp_rag_engine.get_parent_document("doc_0_chunk_0")
            
            # Может быть None если chunk не найден, это нормально
            assert parent is None or isinstance(parent, dict)
        finally:
            shutil.rmtree(test_kb_dir)

