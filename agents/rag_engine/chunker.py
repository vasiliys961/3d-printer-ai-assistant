"""Chunking strategy для документов"""
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Разбиение документов на чанки"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def chunk_document(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Разбить документ на чанки"""
        chunks = self.splitter.split_text(text)
        result = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "chunk_index": i,
                "total_chunks": len(chunks),
                **(metadata or {})
            }
            result.append({
                "text": chunk,
                "metadata": chunk_metadata
            })
        
        return result
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Разбить несколько документов"""
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(
                doc.get("text", ""),
                doc.get("metadata", {})
            )
            all_chunks.extend(chunks)
        return all_chunks


chunker = DocumentChunker()

