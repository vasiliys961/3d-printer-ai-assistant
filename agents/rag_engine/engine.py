"""RAG (Retrieval Augmented Generation) Engine.

Архитектура:
1. Documents -> Chunking (с Parent Document strategy)
2. Chunks -> Embeddings (local или via API)
3. Store -> ChromaDB (vector search)
4. Query -> Semantic + BM25 re-ranking
5. LLM -> Augmented generation
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    JSONLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pathlib import Path
import os

from agents.rag_engine.embedder import embedder
from agents.rag_engine.reranker import reranker
from config import settings
from utils.logger import logger
from utils.metrics import metrics_collector
from utils.cache import cache
import time


@dataclass
class RAGResult:
    """Результат поиска в KB"""
    question: str
    relevant_chunks: List[str]
    sources: List[Dict]  # {source: "materials.json", page: 5}
    relevance_scores: List[float]
    augmented_context: str
    total_results: int


class RAGEngine:
    """Основной RAG engine"""
    
    def __init__(self, db_path: str = None):
        """
        Инициализация RAG engine.
        
        Args:
            db_path: Путь к ChromaDB файлам
        """
        if db_path is None:
            db_path = settings.chroma_persist_dir
        
        os.makedirs(db_path, exist_ok=True)
        
        self.db_client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.db_client.get_or_create_collection(
            name="3d_printing_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Конфиг chunking
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Размер чанка
            chunk_overlap=200,  # Перекрытие между чанками
            separators=["\n\n", "\n", ". ", " "]
        )
        
        # Parent Document strategy: храним маппинг chunk -> parent
        self.chunk_to_parent = {}
        self.parent_documents = {}
    
    def ingest_knowledge_base(self, kb_path: str):
        """
        Загрузка документов из KB в ChromaDB.
        """
        kb_path_obj = Path(kb_path)
        
        if not kb_path_obj.exists():
            raise ValueError(f"Knowledge base path does not exist: {kb_path}")
        
        # Загружаем различные типы файлов
        documents = []
        
        # JSON файлы
        json_files = list(kb_path_obj.rglob("*.json"))
        if json_files:
            for json_file in json_files:
                try:
                    # Пробуем разные схемы для JSON
                    try:
                        # Если это массив документов
                        loader = JSONLoader(
                            str(json_file),
                            jq_schema=".[]"
                        )
                        docs = loader.load()
                    except:
                        # Если это объект с массивом documents
                        try:
                            loader = JSONLoader(
                                str(json_file),
                                jq_schema=".documents[]"
                            )
                            docs = loader.load()
                        except:
                            # Если это простой объект
                            loader = JSONLoader(
                                str(json_file),
                                jq_schema="."
                            )
                            docs = loader.load()
                    
                    # Обогащаем метаданные с информацией из JSON
                    for doc in docs:
                        # Если в метаданных есть content, используем его как page_content
                        if "content" in doc.metadata:
                            doc.page_content = doc.metadata["content"]
                        # Сохраняем source файл
                        doc.metadata["source"] = str(json_file.name)
                        # Сохраняем source_url если есть
                        if "source_url" in doc.metadata:
                            doc.metadata["source_url"] = doc.metadata["source_url"]
                        # Сохраняем другие важные поля
                        if "title" in doc.metadata:
                            doc.metadata["title"] = doc.metadata["title"]
                        if "category" in doc.metadata:
                            doc.metadata["category"] = doc.metadata["category"]
                    
                    documents.extend(docs)
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}", exc_info=True)
        
        # Текстовые файлы
        text_files = list(kb_path_obj.rglob("*.txt")) + list(kb_path_obj.rglob("*.md"))
        if text_files:
            for text_file in text_files:
                try:
                    loader = TextLoader(str(text_file), encoding='utf-8')
                    docs = loader.load()
                    documents.extend(docs)
                except Exception as e:
                    logger.error(f"Error loading {text_file}: {e}", exc_info=True)
        
        if not documents:
            logger.warning(f"No documents found in {kb_path}")
            return
        
        # Разбиваем на чанки с Parent Document strategy
        all_chunks = []
        chunk_metadatas = []
        chunk_ids = []
        
        for doc_idx, doc in enumerate(documents):
            # Сохраняем parent document
            parent_id = f"parent_{doc_idx}"
            self.parent_documents[parent_id] = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "unknown")
            }
            
            # Разбиваем на чанки
            chunks = self.splitter.split_documents([doc])
            
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"doc_{doc_idx}_chunk_{chunk_idx}"
                
                # Сохраняем маппинг chunk -> parent
                self.chunk_to_parent[chunk_id] = parent_id
                
                # Обогащаем метаданные
                chunk_metadata = chunk.metadata.copy()
                chunk_metadata.update({
                    "parent_id": parent_id,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks),
                    "source": doc.metadata.get("source", "unknown")
                })
                
                all_chunks.append(chunk.page_content)
                chunk_metadatas.append(chunk_metadata)
                chunk_ids.append(chunk_id)
        
        # Добавляем в ChromaDB батчами
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i+batch_size]
            batch_metadatas = chunk_metadatas[i:i+batch_size]
            batch_ids = chunk_ids[i:i+batch_size]
            
            # Создаем embeddings
            embeddings = embedder.embed(batch_chunks)
            
            self.collection.add(
                ids=batch_ids,
                documents=batch_chunks,
                embeddings=embeddings.tolist(),
                metadatas=batch_metadatas
            )
        
        logger.info(f"Ingested {len(all_chunks)} chunks from {len(documents)} documents")
        
        # Очищаем кэш RAG поиска при обновлении базы знаний
        cache.clear_pattern("rag_search:*")
        logger.info("RAG search cache cleared after knowledge base update")
    
    async def search(self, query: str, top_k: int = 5) -> RAGResult:
        """
        Поиск релевантных документов с семантическим поиском и BM25 re-ranking.
        Использует кэширование через Redis для ускорения повторных запросов.
        """
        start_time = time.time()
        
        # Проверяем кэш
        cache_key = cache._make_key("rag_search", f"{query}:{top_k}")
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"RAG search cache hit for query: {query[:50]}...")
            # Восстанавливаем RAGResult из кэша
            return RAGResult(
                question=cached_result["question"],
                relevant_chunks=cached_result["relevant_chunks"],
                sources=cached_result["sources"],
                relevance_scores=cached_result["relevance_scores"],
                augmented_context=cached_result["augmented_context"],
                total_results=cached_result["total_results"]
            )
        
        # 1. Семантический поиск через ChromaDB
        query_embedding = embedder.embed_query(query)
        
        # Получаем больше результатов для re-ranking
        n_results = top_k * 3
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
        
        if not results["documents"] or not results["documents"][0]:
            return RAGResult(
                question=query,
                relevant_chunks=[],
                sources=[],
                relevance_scores=[],
                augmented_context="",
                total_results=0
            )
        
        # Извлекаем результаты
        chunks = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        
        # Конвертируем distances в scores (меньше расстояние = выше score)
        semantic_scores = [1 - d for d in distances]
        
        # 2. BM25 re-ranking
        reranked = reranker.rerank(
            query,
            chunks,
            semantic_scores,
            top_k=top_k
        )
        
        # 3. Формируем результаты
        relevant_chunks = []
        relevance_scores = []
        sources = []
        
        for idx, score, chunk in reranked:
            relevant_chunks.append(chunk)
            relevance_scores.append(float(score))
            
            # Извлекаем source из метаданных
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            source_info = {
                "source": metadata.get("source", "unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
                "parent_id": metadata.get("parent_id", ""),
                "source_url": metadata.get("source_url", ""),
                "title": metadata.get("title", ""),
                "category": metadata.get("category", "")
            }
            
            # Если есть parent document, добавляем его информацию
            parent_id = metadata.get("parent_id")
            if parent_id and parent_id in self.parent_documents:
                parent = self.parent_documents[parent_id]
                source_info["parent_source"] = parent["source"]
                # Если source_url не найден в chunk, берем из parent
                if not source_info.get("source_url") and "source_url" in parent.get("metadata", {}):
                    source_info["source_url"] = parent["metadata"]["source_url"]
                if not source_info.get("title") and "title" in parent.get("metadata", {}):
                    source_info["title"] = parent["metadata"]["title"]
            
            sources.append(source_info)
        
        # 4. Формирование контекста
        context_parts = []
        for chunk, score, source in zip(relevant_chunks, relevance_scores, sources):
            if score > 0.3:  # Фильтр по релевантности
                context_parts.append(f"[Source: {source.get('source', 'unknown')}]\n{chunk}")
        
        augmented_context = "\n---\n".join(context_parts)
        
        execution_time = (time.time() - start_time) * 1000
        logger.debug(f"RAG search completed: {execution_time:.2f}ms, results: {len(relevant_chunks)}")
        
        # Создаем результат
        result = RAGResult(
            question=query,
            relevant_chunks=relevant_chunks,
            sources=sources,
            relevance_scores=relevance_scores,
            augmented_context=augmented_context,
            total_results=len(relevant_chunks)
        )
        
        # Кэшируем результат (TTL 1 час)
        cache.set(cache_key, {
            "question": result.question,
            "relevant_chunks": result.relevant_chunks,
            "sources": result.sources,
            "relevance_scores": result.relevance_scores,
            "augmented_context": result.augmented_context,
            "total_results": result.total_results
        }, ttl=3600)
        
        # Записываем метрики
        try:
            import contextvars
            request_id = getattr(contextvars, 'request_id', None)
            if request_id:
                metrics_collector.record_rag_search(request_id, len(relevant_chunks))
        except:
            pass
        
        return result
    
    def get_parent_document(self, chunk_id: str) -> Optional[Dict]:
        """Получить parent document для chunk"""
        parent_id = self.chunk_to_parent.get(chunk_id)
        if parent_id:
            return self.parent_documents.get(parent_id)
        return None
    
    def add_document(self, content: str, metadata: Dict = None):
        """Добавить один документ в базу знаний"""
        doc = Document(page_content=content, metadata=metadata or {})
        chunks = self.splitter.split_documents([doc])
        
        # Сохраняем parent
        parent_id = f"parent_{len(self.parent_documents)}"
        self.parent_documents[parent_id] = {
            "content": content,
            "metadata": metadata or {},
            "source": metadata.get("source", "manual") if metadata else "manual"
        }
        
        # Добавляем чанки
        chunk_ids = []
        chunk_contents = []
        chunk_metadatas = []
        
        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = f"doc_{len(self.parent_documents)-1}_chunk_{chunk_idx}"
            self.chunk_to_parent[chunk_id] = parent_id
            
            chunk_metadata = chunk.metadata.copy()
            chunk_metadata.update({
                "parent_id": parent_id,
                "chunk_index": chunk_idx,
                "total_chunks": len(chunks),
                "source": metadata.get("source", "manual") if metadata else "manual"
            })
            
            chunk_ids.append(chunk_id)
            chunk_contents.append(chunk.page_content)
            chunk_metadatas.append(chunk_metadata)
        
        # Создаем embeddings и добавляем
        embeddings = embedder.embed(chunk_contents)
        
        self.collection.add(
            ids=chunk_ids,
            documents=chunk_contents,
            embeddings=embeddings.tolist(),
            metadatas=chunk_metadatas
        )
        
        return len(chunks)


# Создаем глобальный экземпляр
rag_engine = RAGEngine()

