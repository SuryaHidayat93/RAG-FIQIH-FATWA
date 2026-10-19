from typing import Literal
from langgraph.graph import StateGraph, START, END
from src.state import RAGState
from src.nodes.query_understanding import query_understanding_node
from src.nodes.retrieval_node import parallel_retrieval_node
from src.nodes.reranker_node import reranker_node
from src.nodes.grader_node import grader_node
from src.nodes.generator_node import generator_node
from src.nodes.faithfulness_node import faithfulness_node


def out_of_scope_node(state: RAGState) -> dict:
    """Menangani pertanyaan di luar domain syariah dan hukum Islam."""
    print(f"\n[OUT OF SCOPE NODE]", flush=True)
    print(f"  * Status             : Menghentikan pipeline (Pertanyaan non-syariah)", flush=True)
    print("=" * 80, flush=True)
    print(f"[RAG PIPELINE] SELESAI (OUT OF SCOPE)", flush=True)
    print("=" * 80 + "\n", flush=True)
    return {
        "generation": "Pertanyaan ini berada di luar cakupan fiqih dan fatwa hukum Islam. Sistem ini dikhususkan untuk pencarian hukum syariah, perbandingan mazhab, dan fatwa keagamaan.",
        "citations": [],
        "abstain": True,
        "faithfulness_passed": True,
    }


def route_after_query_understanding(state: RAGState) -> Literal["out_of_scope", "parallel_retrieval"]:
    if state.get("route") == "di_luar_cakupan":
        return "out_of_scope"
    return "parallel_retrieval"


def route_after_grader(state: RAGState) -> Literal["parallel_retrieval", "generator"]:
    grade = state.get("grade")
    abstain = state.get("abstain", False)

    # Jika tidak relevan dan belum abstain (masih ada kuota retry), ulangi retrieval
    if grade == "tidak_relevan" and not abstain:
        return "parallel_retrieval"
    return "generator"


def build_rag_graph():
    """Merakit state graph LangGraph untuk pipeline Fiqih & Fatwa."""
    workflow = StateGraph(RAGState)

    # Tambah nodes
    workflow.add_node("query_understanding", query_understanding_node)
    workflow.add_node("out_of_scope", out_of_scope_node)
    workflow.add_node("parallel_retrieval", parallel_retrieval_node)
    workflow.add_node("reranker", reranker_node)
    workflow.add_node("grader", grader_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("faithfulness_checker", faithfulness_node)

    # Hubungkan edges
    workflow.add_edge(START, "query_understanding")

    workflow.add_conditional_edges(
        "query_understanding",
        route_after_query_understanding,
        {
            "out_of_scope": "out_of_scope",
            "parallel_retrieval": "parallel_retrieval",
        },
    )

    workflow.add_edge("out_of_scope", END)
    workflow.add_edge("parallel_retrieval", "reranker")
    workflow.add_edge("reranker", "grader")

    workflow.add_conditional_edges(
        "grader",
        route_after_grader,
        {
            "parallel_retrieval": "parallel_retrieval",
            "generator": "generator",
        },
    )

    workflow.add_edge("generator", "faithfulness_checker")
    workflow.add_edge("faithfulness_checker", END)

    return workflow.compile()


app_graph = build_rag_graph()
