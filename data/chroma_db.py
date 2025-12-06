"""ChromaDB для векторных embeddings"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings
import os


class ChromaDBManager:
    """Менеджер для работы с ChromaDB"""
    
    def __init__(self):
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="printer_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: list[str], metadatas: list[dict] = None, ids: list[str] = None):
        """Добавить документы в коллекцию"""
        self.collection.add(
            documents=documents,
            metadatas=metadatas or [{}] * len(documents),
            ids=ids or [f"doc_{i}" for i in range(len(documents))]
        )
    
    def query(self, query_texts: list[str], n_results: int = 5, filter: dict = None):
        """Поиск похожих документов"""
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=filter
        )
    
    def get_collection(self):
        """Получить коллекцию"""
        return self.collection


chroma_db = ChromaDBManager()

