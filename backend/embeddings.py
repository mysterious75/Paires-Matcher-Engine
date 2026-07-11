"""
Paires Matcher - Real Embedding System
Uses sentence-transformers for semantic similarity
"""
from typing import List, Dict, Any
import numpy as np

# Lazy load to avoid slow startup
_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


class EmbeddingEngine:
    """Real embedding-based similarity scoring"""
    
    def __init__(self):
        self.cache = {}
    
    def embed_text(self, text: str) -> np.ndarray:
        """Convert text to embedding vector"""
        if text in self.cache:
            return self.cache[text]
        model = _get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        self.cache[text] = embedding
        return embedding
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def score_match(self, founder_text: str, investor_text: str) -> float:
        """Compute semantic similarity score between founder and investor"""
        emb1 = self.embed_text(founder_text)
        emb2 = self.embed_text(investor_text)
        return self.cosine_similarity(emb1, emb2)
    
    def batch_embed(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts at once"""
        model = _get_model()
        return model.encode(texts, convert_to_numpy=True)
    
    def batch_similarity(self, query_embedding: np.ndarray, corpus_embeddings: np.ndarray) -> np.ndarray:
        """Compute similarity between query and all corpus embeddings"""
        norms = np.linalg.norm(corpus_embeddings, axis=1)
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return np.zeros(len(corpus_embeddings))
        similarities = np.dot(corpus_embeddings, query_embedding) / (norms * query_norm)
        return similarities
