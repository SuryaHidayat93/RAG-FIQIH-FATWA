from typing import Any, Dict, List
from rank_bm25 import BM25Okapi
from src.text_processing.arabic_normalizer import tokenize_for_bm25
from src.state import Document


class CorpusBM25Index:
    def __init__(self, corpus_name: str):
        self.corpus_name = corpus_name
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: BM25Okapi | None = None

    def build_index(self, docs: List[Document]):
        """Build BM25 index dari list Document."""
        self.documents = docs
        self.tokenized_corpus = [
            tokenize_for_bm25(doc["content"]) for doc in docs
        ]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

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
