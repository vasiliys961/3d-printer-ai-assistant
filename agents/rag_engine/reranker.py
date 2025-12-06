"""Re-ranker (BM25 + semantic)"""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple
import numpy as np
from agents.rag_engine.embedder import embedder


class Reranker:
    """Re-ranker для улучшения результатов поиска"""
    
    def __init__(self):
        self.bm25 = None
    
    def build_bm25_index(self, documents: List[str]):
        """Построить BM25 индекс"""
        tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        semantic_scores: List[float],
        top_k: int = 5
    ) -> List[Tuple[int, float, str]]:
        """Re-ranking с использованием BM25 и семантических оценок"""
        if not documents:
            return []
        
        # Пересоздаем BM25 индекс для текущих документов
        self.build_bm25_index(documents)
        
        # BM25 scores
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Нормализация scores
        if len(bm25_scores) > 0:
            bm25_min = bm25_scores.min()
            bm25_max = bm25_scores.max()
            if bm25_max > bm25_min:
                bm25_scores = (bm25_scores - bm25_min) / (bm25_max - bm25_min)
            else:
                bm25_scores = np.ones_like(bm25_scores)
        else:
            bm25_scores = np.array([])
        
        semantic_scores = np.array(semantic_scores)
        if len(semantic_scores) > 0:
            sem_min = semantic_scores.min()
            sem_max = semantic_scores.max()
            if sem_max > sem_min:
                semantic_scores = (semantic_scores - sem_min) / (sem_max - sem_min)
            else:
                semantic_scores = np.ones_like(semantic_scores)
        else:
            semantic_scores = np.array([])
        
        # Комбинированные scores (50% BM25, 50% semantic)
        if len(bm25_scores) > 0 and len(semantic_scores) > 0:
            combined_scores = 0.5 * bm25_scores + 0.5 * semantic_scores
        elif len(semantic_scores) > 0:
            combined_scores = semantic_scores
        elif len(bm25_scores) > 0:
            combined_scores = bm25_scores
        else:
            combined_scores = np.array([1.0] * len(documents))
        
        # Сортировка
        ranked_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        results = [
            (int(idx), float(combined_scores[idx]), documents[idx])
            for idx in ranked_indices
        ]
        
        return results


reranker = Reranker()

