import json
from typing import Dict, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from src.config import settings
from src.state import RAGState
from src.text_processing.arabic_normalizer import normalize_islamic_text


class QueryUnderstandingOutput(BaseModel):
    rewritten_query: str = Field(
        description="Query yang dioptimalkan untuk pencarian teks kitab fiqih dan fatwa, lengkap dengan istilah teknis syariah."
    )
    route: Literal["fatwa", "fiqih", "keduanya", "di_luar_cakupan"] = Field(
        description="Klasifikasi domain pertanyaan: 'fatwa' (lembaga resmi DSN-MUI, Tarjih, Bahtsul Masail, isu kontemporer), 'fiqih' (hukum klasik/mazhab), 'keduanya' (memerlukan rujukan kitab klasik sekaligus fatwa resmi), atau 'di_luar_cakupan' (pertanyaan non-keislaman/non-hukum syariah)."
    )
    reasoning: str = Field(description="Alasan singkat penentuan route dan rewrite.")


ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """Anda adalah spesialis Query Understanding untuk Sistem Tanya Jawab Syariah, Fiqih, dan Fatwa.
Tugas Anda:
1. Memahami maksud syariah dari pertanyaan pengguna.
2. Melakukan query rewrite: gunakan istilah baku fikih (bahasa Indonesia dan Arab transliterasi) agar ramah mesin pencari.
3. Menentukan router korpus rujukan:
   - 'fatwa': Isu kontemporer, regulasi muamalah modern (crypto, paylater, vaksin, ormas DSN-MUI/Tarjih/Bahtsul Masail).
   - 'fiqih': Hukum ibadah, munakahat, jinayat berbasis mazhab empat dan teks kitab turats klasik.
   - 'keduanya': Pertanyaan yang memiliki akar fiqih klasik sekaligus membutuhkan kepastian fatwa kontemporer Indonesia.
   - 'di_luar_cakupan': Pertanyaan di luar hukum Islam/syariah (misal sains umum, politik praktis non-syariah, programming).

Keluarkan HANYA JSON sesuai format skema.""",
    ),
    (
        "human",
        "Pertanyaan asli: {query}\nPertanyaan dinormalisasi: {normalized_query}",
    ),
])


def query_understanding_node(state: RAGState) -> Dict:
    """Node 1: Normalisasi teks + rewrite + routing domain."""
    query = state["query"]
    normalized = normalize_islamic_text(query)

    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.primary_model,
        format="json",
        temperature=0.0,
    )

    structured_llm = llm.with_structured_output(QueryUnderstandingOutput)
    chain = ROUTER_PROMPT | structured_llm

    try:
        result: QueryUnderstandingOutput = chain.invoke(
            {"query": query, "normalized_query": normalized}
        )
        return {
            "normalized_query": normalized,
            "rewritten_query": result.rewritten_query,
            "route": result.route,
            "retry_count": state.get("retry_count", 0),
        }
    except Exception:
        # Fallback deterministik jika LLM gagal format JSON
        return {
            "normalized_query": normalized,
            "rewritten_query": normalized,
            "route": "keduanya",
            "retry_count": state.get("retry_count", 0),
        }
