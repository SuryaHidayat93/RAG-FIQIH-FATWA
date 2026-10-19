from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from src.config import settings
from src.state import RAGState
from src.text_processing.arabic_normalizer import normalize_islamic_text
from src.router.indobert_router import IndoBERTRouter

_indobert_router: Optional[IndoBERTRouter] = None


def get_indobert_router() -> IndoBERTRouter:
    global _indobert_router
    if _indobert_router is None:
        _indobert_router = IndoBERTRouter()
    return _indobert_router


class QueryUnderstandingOutput(BaseModel):
    rewritten_query: str = Field(
        description="Query yang dioptimalkan untuk pencarian teks kitab fiqih dan fatwa, lengkap dengan istilah teknis syariah."
    )
    route: Literal["fatwa", "fiqih", "keduanya", "di_luar_cakupan"] = Field(
        description="Klasifikasi domain pertanyaan: 'fatwa' (lembaga resmi DSN-MUI, Tarjih, Bahtsul Masail, isu kontemporer), 'fiqih' (hukum klasik/mazhab), 'keduanya' (memerlukan rujukan kitab klasik sekaligus fatwa resmi), atau 'di_luar_cakupan' (pertanyaan non-keislaman/non-hukum syariah)."
    )
    reasoning: str = Field(description="Alasan singkat penentuan route dan rewrite.")


REWRITE_ONLY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Anda bertugas melakukan query rewrite untuk pencarian teks fikih dan fatwa. Tulis ulang pertanyaan agar menggunakan istilah baku fikih Arab/Indonesia untuk mesin pencari. Tulis HANYA satu kalimat hasil rewrite.",
    ),
    (
        "human",
        "Pertanyaan: {query}",
    ),
])

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
    """Node 1: Normalisasi teks + rewrite + routing domain via IndoBERT atau LLM."""
    import time

    t_start = time.time()
    query = state["query"]
    normalized = normalize_islamic_text(query)
    retry_count = state.get("retry_count", 0)

    print("\n" + "=" * 80, flush=True)
    print(f"[RAG PIPELINE] MEMULAI PEMROSESAN PERTANYAAN", flush=True)
    print(f"Pertanyaan Asli  : \"{query}\"", flush=True)
    print("=" * 80, flush=True)
    print(f"\n[1/6] QUERY UNDERSTANDING & ROUTING", flush=True)
    print(f"  * Normalisasi Teks   : \"{normalized}\"", flush=True)

    # Mode 1: IndoBERT Router
    if settings.router_model_type == "indobert":
        router = get_indobert_router()
        route, confidence = router.predict(normalized)
        print(f"  * Router Model       : IndoBERT (Confidence: {confidence:.2%})", flush=True)
        print(f"  * Keputusan Rute     : {route.upper()}", flush=True)

        # Jika di luar cakupan, lewati query rewrite hemat LLM call
        if route == "di_luar_cakupan":
            elapsed = time.time() - t_start
            print(f"  * Catatan            : Pertanyaan teridentifikasi di luar lingkup syariah ({elapsed:.2f}s)", flush=True)
            return {
                "normalized_query": normalized,
                "rewritten_query": normalized,
                "route": "di_luar_cakupan",
                "retry_count": retry_count,
            }

        # Lakukan query rewrite ringan via LLM
        try:
            llm = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.primary_model,
                temperature=0.0,
            )
            rewrite_res = (REWRITE_ONLY_PROMPT | llm).invoke({"query": normalized})
            rewritten = rewrite_res.content.strip() if hasattr(rewrite_res, "content") else normalized
        except Exception as e:
            print(f"  * Warning Rewrite    : Gagal rewrite ({e}), menggunakan query normalisasi", flush=True)
            rewritten = normalized

        elapsed = time.time() - t_start
        print(f"  * Query Rewrite      : \"{rewritten}\"", flush=True)
        print(f"  * Selesai Tahap 1    : {elapsed:.2f} detik", flush=True)

        return {
            "normalized_query": normalized,
            "rewritten_query": rewritten,
            "route": route,
            "retry_count": retry_count,
        }

    # Mode 2: LLM Router Fallback
    print(f"  * Router Model       : LLM ({settings.primary_model})", flush=True)
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
        elapsed = time.time() - t_start
        print(f"  * Keputusan Rute     : {result.route.upper()}", flush=True)
        print(f"  * Query Rewrite      : \"{result.rewritten_query}\"", flush=True)
        print(f"  * Reasoning          : {result.reasoning}", flush=True)
        print(f"  * Selesai Tahap 1    : {elapsed:.2f} detik", flush=True)
        return {
            "normalized_query": normalized,
            "rewritten_query": result.rewritten_query,
            "route": result.route,
            "retry_count": retry_count,
        }
    except Exception as e:
        elapsed = time.time() - t_start
        print(f"  * Fallback Router    : Gagal ({e}), default ke 'keduanya' ({elapsed:.2f}s)", flush=True)
        return {
            "normalized_query": normalized,
            "rewritten_query": normalized,
            "route": "keduanya",
            "retry_count": retry_count,
        }
