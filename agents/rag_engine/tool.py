"""RAG Engine Tool для LangGraph"""
from typing import List, Dict, Any
from agents.rag_engine.engine import rag_engine, RAGResult


class RAGEngineTool:
    """Инструмент для поиска по базе знаний"""
    
    async def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Поиск по базе знаний с семантическим поиском и BM25 re-ranking"""
        result: RAGResult = await rag_engine.search(query, top_k)
        
        return {
            "question": result.question,
            "results": [
                {
                    "text": chunk,
                    "score": float(score),
                    "source": source
                }
                for chunk, score, source in zip(
                    result.relevant_chunks,
                    result.relevance_scores,
                    result.sources
                )
            ],
            "count": result.total_results,
            "augmented_context": result.augmented_context,
            "query": query
        }
    
    def add_knowledge(self, text: str, metadata: Dict = None):
        """Добавить знания в базу"""
        chunk_count = rag_engine.add_document(text, metadata)
        return {
            "success": True,
            "chunks_created": chunk_count,
            "message": f"Добавлено {chunk_count} чанков в базу знаний"
        }
    
    def ingest_knowledge_base(self, kb_path: str):
        """Загрузить документы из директории в базу знаний"""
        try:
            rag_engine.ingest_knowledge_base(kb_path)
            return {
                "success": True,
                "message": f"База знаний загружена из {kb_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_description(self) -> str:
        """Описание инструмента для LLM"""
        return """RAG Engine Tool для поиска по базе знаний:
        - search: Поиск релевантной информации по запросу (семантический поиск + BM25 re-ranking)
        - add_knowledge: Добавить новую информацию в базу знаний
        - ingest_knowledge_base: Загрузить документы из директории в базу знаний
        """


rag_engine_tool = RAGEngineTool()
