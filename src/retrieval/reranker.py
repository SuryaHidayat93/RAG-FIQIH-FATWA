from typing import List, Optional
from sentence_transformers import CrossEncoder
from src.config import settings
from src.state import Document


class CrossEncoderReranker:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.reranker_model_name
        self._model: Optional[CrossEncoder] = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None,
    ) -> List[Document]:
        """Rerank dokumen menggunakan cross-encoder bge-reranker."""
        if not documents:
            return []

        limit = top_k or settings.rerank_top_k
        pairs = [[query, doc["content"]] for doc in documents]
        scores = self.model.predict(pairs)

        scored_docs = []
        for doc, score in zip(documents, scores):
            d = doc.copy()
            d["score"] = float(score)
            scored_docs.append(d)

        scored_docs.sort(key=lambda d: d["score"], reverse=True)
        return scored_docs[:limit]
