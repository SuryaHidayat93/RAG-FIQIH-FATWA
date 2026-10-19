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
    import time

    t_start = time.time()
    route = state.get("route", "keduanya")
    query = state.get("rewritten_query") or state.get("query")
    retry_count = state.get("retry_count", 0)

    print(f"\n[2/6] PARALLEL HYBRID RETRIEVAL (BGE-M3 Dense + BM25 Sparse -> RRF)", flush=True)
    if retry_count > 0:
        print(f"  * Mode               : RETRY ke-{retry_count} (setelah CRAG query rewrite)", flush=True)
    print(f"  * Query Retrieval    : \"{query}\"", flush=True)
    print(f"  * Target Korpus      : {route.upper()}", flush=True)

    if route == "di_luar_cakupan":
        print(f"  * Catatan            : Korpus dilewati karena query di luar cakupan.", flush=True)
        return {"retrieved_documents": []}

    futures = {}
    docs: List[Document] = []
    corpus_stats = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        if route in ["fatwa", "keduanya"]:
            futures[executor.submit(retrieve_fatwa_corpus, query)] = "fatwa"
        if route in ["fiqih", "keduanya"]:
            futures[executor.submit(retrieve_fiqih_corpus, query)] = "fiqih"

        for future in concurrent.futures.as_completed(futures):
            c_name = futures[future]
            try:
                res = future.result()
                corpus_stats[c_name] = len(res)
                docs.extend(res)
            except Exception as e:
                corpus_stats[c_name] = 0
                print(f"  * Error retrieval [{c_name}]: {e}", flush=True)

    for c_name, count in corpus_stats.items():
        print(f"  * Hasil Korpus {c_name.capitalize():6s}: {count} dokumen (RRF Dense+BM25)", flush=True)

    elapsed = time.time() - t_start
    print(f"  * Total Dokumen RRF  : {len(docs)} dokumen dikirim ke reranker ({elapsed:.2f} detik)", flush=True)
    return {"retrieved_documents": docs}
