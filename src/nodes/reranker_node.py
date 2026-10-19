from typing import Dict, List, Optional
from src.state import Document, RAGState
from src.retrieval.reranker import CrossEncoderReranker

_reranker: Optional[CrossEncoderReranker] = None


def get_reranker() -> CrossEncoderReranker:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker()
    return _reranker


def reranker_node(state: RAGState) -> Dict:
    """Node 3: Cross-encoder reranking untuk menghasilkan top-k dokumen paling relevan."""
    import time

    t_start = time.time()
    query = state.get("rewritten_query") or state.get("query")
    docs: List[Document] = state.get("retrieved_documents", [])

    print(f"\n[3/6] CROSS-ENCODER RERANKER (BAAI/bge-reranker-v2-m3)", flush=True)
    print(f"  * Dokumen Masuk      : {len(docs)} kandidat dokumen", flush=True)

    if not docs:
        print(f"  * Warning            : Tidak ada dokumen untuk di-rerank.", flush=True)
        return {"reranked_documents": []}

    reranker = get_reranker()
    top_docs = reranker.rerank(query=query, documents=docs)

    elapsed = time.time() - t_start
    print(f"  * Dokumen Terpilih   : {len(top_docs)} dokumen terbaik (Top-K) ({elapsed:.2f} detik)", flush=True)
    print(f"  * Peringkat Dokumen Teratas:", flush=True)
    for idx, d in enumerate(top_docs[:3], start=1):
        meta = d.get("metadata", {})
        title = meta.get("topik") or meta.get("fasal") or meta.get("bab") or d.get("id")
        corpus = d.get("corpus", "").upper()
        score = d.get("score", 0.0)
        print(f"    {idx}. [{corpus}] (Skor: {score:.4f}) {str(title)[:65]}", flush=True)

    return {"reranked_documents": top_docs}
