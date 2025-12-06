"""Embeddings для RAG"""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np


class Embedder:
    """Генератор embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Создать embeddings для текстов"""
        return self.model.encode(texts, convert_to_numpy=True)
    
    def embed_query(self, query: str) -> np.ndarray:
        """Создать embedding для запроса"""
        return self.model.encode([query], convert_to_numpy=True)[0]


embedder = Embedder()

