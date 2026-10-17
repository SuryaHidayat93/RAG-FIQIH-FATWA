from collections import defaultdict
from typing import Dict, List, Literal, Optional
from src.config import settings
from src.state import Document
from src.retrieval.bm25_retriever import CorpusBM25Index
from src.retrieval.dense_retriever import DenseRetriever


def reciprocal_rank_fusion(
    ranked_lists: List[List[Document]],
    k: int = 60,
    top_n: int = 15,
) -> List[Document]:
    """Menggabungkan beberapa daftar dokumen terurut menggunakan RRF."""
    rrf_scores: Dict[str, float] = defaultdict(float)
    doc_lookup: Dict[str, Document] = {}

    for doc_list in ranked_lists:
        for rank, doc in enumerate(doc_list, start=1):
            doc_id = doc.get("id") or doc.get("content")
            rrf_scores[doc_id] += 1.0 / (k + rank)
            if doc_id not in doc_lookup:
                doc_lookup[doc_id] = doc

    sorted_ids = sorted(rrf_scores.keys(), key=lambda did: rrf_scores[did], reverse=True)[:top_n]

    results: List[Document] = []
    for did in sorted_ids:
        doc = doc_lookup[did].copy()
        doc["score"] = rrf_scores[did]
        results.append(doc)

    return results


class HybridRetriever:
    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_index: CorpusBM25Index,
        corpus_name: Literal["fatwa", "fiqih"],
    ):
        self.dense_retriever = dense_retriever
        self.bm25_index = bm25_index
        self.corpus_name = corpus_name

    def retrieve(
        self,
        query: str,
        dense_top_k: Optional[int] = None,
        bm25_top_k: Optional[int] = None,
        top_n: Optional[int] = None,
    ) -> List[Document]:
        """Eksekusi dense + BM25 lalu gabungkan via RRF."""
        d_top = dense_top_k or settings.dense_top_k
        b_top = bm25_top_k or settings.bm25_top_k
        final_top = top_n or settings.dense_top_k

        dense_docs = self.dense_retriever.search(
            collection_name=self.corpus_name,
            query=query,
            corpus=self.corpus_name,
            top_k=d_top,
        )
        bm25_docs = self.bm25_index.search(query=query, top_k=b_top)

        return reciprocal_rank_fusion([dense_docs, bm25_docs], k=settings.rrf_k, top_n=final_top)
