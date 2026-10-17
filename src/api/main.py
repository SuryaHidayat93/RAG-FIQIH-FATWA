from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.graph import app_graph
from src.config import settings

app = FastAPI(
    title="RAG Fiqih & Fatwa API",
    description="API Tanya Jawab Syariah berbasis CRAG, Hybrid Search (Dense BGE-M3 + BM25), dan Self-RAG",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = None


class CitationResponse(BaseModel):
    corpus: Optional[str] = None
    source: Optional[str] = None
    bab: Optional[str] = None
    halaman: Optional[str] = None
    nomor_fatwa: Optional[str] = None
    mazhab: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    route: str
    rewritten_query: str
    answer: str
    citations: List[CitationResponse]
    faithfulness_passed: bool
    faithfulness_explanation: Optional[str] = None
    abstain: bool


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "rag-fiqih-fatwa"}


@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query tidak boleh kosong.")

    initial_state = {
        "query": request.query,
        "retry_count": 0,
        "retrieved_documents": [],
    }

    try:
        final_state = app_graph.invoke(initial_state)
        return QueryResponse(
            query=request.query,
            route=final_state.get("route", "keduanya"),
            rewritten_query=final_state.get("rewritten_query", request.query),
            answer=final_state.get("generation", ""),
            citations=final_state.get("citations", []),
            faithfulness_passed=final_state.get("faithfulness_passed", True),
            faithfulness_explanation=final_state.get("faithfulness_explanation"),
            abstain=final_state.get("abstain", False),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses query: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host=settings.api_host, port=settings.api_port, reload=True)
