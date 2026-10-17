import concurrent.futures
from typing import Dict, List
from src.state import Document, RAGState
from src.retrieval.dense_retriever import DenseRetriever
from src.retrieval.bm25_retriever import CorpusBM25Index
from src.retrieval.hybrid_retriever import HybridRetriever

# Inisialisasi retriever singleton
_dense_retriever: DenseRetriever | None = None
_fatwa_bm25: CorpusBM25Index = CorpusBM25Index("fatwa")
_fiqih_bm25: CorpusBM25Index = CorpusBM25Index("fiqih")


def get_dense_retriever() -> DenseRetriever:
    global _dense_retriever
    if _dense_retriever is None:
        _dense_retriever = DenseRetriever()
    return _dense_retriever


def retrieve_fatwa_corpus(query: str) -> List[Document]:
    retriever = HybridRetriever(get_dense_retriever(), _fatwa_bm25, "fatwa")
    return retriever.retrieve(query)


def retrieve_fiqih_corpus(query: str) -> List[Document]:
    retriever = HybridRetriever(get_dense_retriever(), _fiqih_bm25, "fiqih")
    return retriever.retrieve(query)


def parallel_retrieval_node(state: RAGState) -> Dict:
    """Node 2: Eksekusi retrieval paralel sesuai keputusan router."""
    route = state.get("route", "keduanya")
    query = state.get("rewritten_query") or state.get("query")

    if route == "di_luar_cakupan":
        return {"retrieved_documents": []}

    futures = {}
    docs: List[Document] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        if route in ["fatwa", "keduanya"]:
            futures[executor.submit(retrieve_fatwa_corpus, query)] = "fatwa"
        if route in ["fiqih", "keduanya"]:
            futures[executor.submit(retrieve_fiqih_corpus, query)] = "fiqih"

        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                docs.extend(res)
            except Exception as e:
                # Log error corpus tapi jangan hentikan eksekusi corpus lain
                print(f"Error retrieval {futures[future]}: {e}")

    return {"retrieved_documents": docs}
