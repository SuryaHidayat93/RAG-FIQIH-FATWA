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
    query = state.get("rewritten_query") or state.get("query")
    docs: List[Document] = state.get("retrieved_documents", [])

    if not docs:
        return {"reranked_documents": []}

    reranker = get_reranker()
    top_docs = reranker.rerank(query=query, documents=docs)

    return {"reranked_documents": top_docs}
