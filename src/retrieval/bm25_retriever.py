import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi
from src.text_processing.arabic_normalizer import tokenize_for_bm25
from src.state import Document


class CorpusBM25Index:
    def __init__(self, corpus_name: str, storage_dir: str = "./data/bm25"):
        self.corpus_name = corpus_name
        self.storage_dir = Path(storage_dir)
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: BM25Okapi | None = None

        # Auto-load jika file index ada di disk
        self.load()

    def build_index(self, docs: List[Document]):
        """Build BM25 index dari list Document."""
        self.documents = docs
        self.tokenized_corpus = [
            tokenize_for_bm25(doc["content"]) for doc in docs
        ]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def save(self, storage_dir: Optional[str] = None) -> str:
        """Simpan index BM25 dan data dokumen ke disk (.pkl)."""
        target_dir = Path(storage_dir) if storage_dir else self.storage_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{self.corpus_name}_bm25.pkl"

        data = {
            "corpus_name": self.corpus_name,
            "documents": self.documents,
            "tokenized_corpus": self.tokenized_corpus,
            "bm25": self.bm25,
        }

        with open(file_path, "wb") as f:
            pickle.dump(data, f)

        return str(file_path)

    def load(self, storage_dir: Optional[str] = None) -> bool:
        """Muat index BM25 dari disk jika tersedia."""
        target_dir = Path(storage_dir) if storage_dir else self.storage_dir
        file_path = target_dir / f"{self.corpus_name}_bm25.pkl"

        if not file_path.exists():
            return False

        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            self.documents = data.get("documents", [])
            self.tokenized_corpus = data.get("tokenized_corpus", [])
            self.bm25 = data.get("bm25")
            return True
        except Exception as e:
            print(f"Gagal memuat index BM25 {self.corpus_name} dari disk: {e}")
            return False

    def search(self, query: str, top_k: int = 15) -> List[Document]:
        """Search BM25 dan kembalikan top-k docs dengan skor."""
        if not self.bm25 or not self.documents:
            return []

        tokenized_query = tokenize_for_bm25(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Urutkan berdasarkan skor tertinggi
        scored_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results: List[Document] = []
        for idx in scored_indices:
            doc = self.documents[idx].copy()
            doc["score"] = float(scores[idx])
            results.append(doc)
        return results
