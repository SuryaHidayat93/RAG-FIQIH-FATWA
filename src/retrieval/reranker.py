from typing import List, Optional
import torch
from sentence_transformers import CrossEncoder
from src.config import settings
from src.state import Document


class CrossEncoderReranker:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.reranker_model_name
        self._model: Optional[CrossEncoder] = None
        self._load_attempted = False

    @property
    def model(self) -> Optional[CrossEncoder]:
        if self._model is None and not self._load_attempted:
            self._load_attempted = True
            device = "cuda" if torch.cuda.is_available() else "cpu"
            try:
                # Muat dari cache lokal agar tidak memblokir request pengguna
                self._model = CrossEncoder(self.model_name, device=device, local_files_only=True)
            except Exception:
                # Model belum terunduh penuh di cache lokal
                self._model = None
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None,
    ) -> List[Document]:
        """Rerank dokumen menggunakan cross-encoder bge-reranker dengan fallback RRF jika model belum siap."""
        if not documents:
            return []

        limit = top_k or settings.rerank_top_k

        if self.model is None:
            print("  * Catatan Reranker   : Model Cross-Encoder belum di-cache lokal. Menggunakan pemeringkatan RRF Hybrid (Dense + BM25).", flush=True)
            return documents[:limit]

        try:
            pairs = [[query, doc["content"]] for doc in documents]
            scores = self.model.predict(pairs)

            scored_docs = []
            for doc, score in zip(documents, scores):
                d = doc.copy()
                d["score"] = float(score)
                scored_docs.append(d)

            scored_docs.sort(key=lambda d: d["score"], reverse=True)
            return scored_docs[:limit]
        except Exception as e:
            print(f"  * Warning Reranker: {e}. Menggunakan peringkat RRF awal.", flush=True)
            return documents[:limit]
