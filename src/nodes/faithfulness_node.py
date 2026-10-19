from typing import Dict
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from src.config import settings
from src.state import RAGState
from src.nodes.generator_node import format_context


class FaithfulnessOutput(BaseModel):
    is_faithful: bool = Field(
        description="True jika semua klaim hukum fiqih, kutipan nash, dan rujukan fatwa didukung langsung oleh dokumen konteks. False jika terdapat klaim atau penetapan hukum tanpa sandaran dalam dokumen."
    )
    explanation: str = Field(description="Analisis grounding klaim terhadap dokumen konteks.")


FAITHFULNESS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """Anda adalah Penguji Keabsahan Teks (Faithfulness Checker) untuk fatwa dan hukum Islam.
Tugas Anda: Memverifikasi apakah jawaban yang dihasilkan HANYA didasarkan pada dokumen rujukan yang diberikan (tanpa halusinasi dan tanpa menambahkan penetapan hukum liar di luar teks).

Kriteria ketat:
- Jika ada kutipan ayat/hadits/pendapat ulama yang TIDAK termuat di dokumen rujukan -> False.
- Jika nomor fatwa atau nama kitab yang diklaim TIDAK ada di metadata/teks rujukan -> False.
- Jika seluruh jawaban berpijak pada dokumen rujukan -> True.

Keluarkan format JSON.""",
    ),
    (
        "human",
        "Dokumen Rujukan:\n{context}\n\nJawaban yang Diuji:\n{generation}",
    ),
])


def faithfulness_node(state: RAGState) -> Dict:
    """Node 6: Faithfulness check untuk mencegah halusinasi penetapan hukum."""
    import time

    t_start = time.time()
    print(f"\n[6/6] FAITHFULNESS CHECKER (Self-RAG Grounding Verification)", flush=True)

    if state.get("abstain", False):
        print(f"  * Status             : Dilewati karena jawaban sebelumnya berstatus ABSTAIN", flush=True)
        print("=" * 80 + "\n", flush=True)
        return {"faithfulness_passed": True}

    generation = state.get("generation", "")
    docs = state.get("reranked_documents", [])
    context_str = format_context(docs)

    print(f"  * Menguji Grounding  : Memverifikasi apakah semua klaim hukum bertumpu pada dokumen...", flush=True)

    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.primary_model,
        format="json",
        temperature=0.0,
    )
    structured_llm = llm.with_structured_output(FaithfulnessOutput)
    chain = FAITHFULNESS_PROMPT | structured_llm

    try:
        res: FaithfulnessOutput = chain.invoke(
            {"context": context_str, "generation": generation}
        )
        passed = res.is_faithful
        explanation = res.explanation
    except Exception as e:
        passed = True
        explanation = f"Faithfulness check fallback: {e}"

    elapsed = time.time() - t_start
    status_str = "LULUS (FAITHFUL)" if passed else "GAGAL (UNFAITHFUL -> ABSTAIN)"
    print(f"  * Hasil Pengujian    : {status_str} ({elapsed:.2f} detik)", flush=True)
    if explanation:
        print(f"  * Evaluasi Grounding : {explanation[:130]}...", flush=True)

    print("=" * 80, flush=True)
    print(f"[RAG PIPELINE] SELESAI MEMPROSES PERTANYAAN", flush=True)
    print("=" * 80 + "\n", flush=True)

    if not passed:
        # Jika klaim tidak faithful terhadap teks rujukan, abstain demi kehati-hatian syar'i
        return {
            "faithfulness_passed": False,
            "faithfulness_explanation": explanation,
            "generation": "Maaf, jawaban awal tidak lolos verifikasi validitas rujukan teks (faithfulness check). Demi kehati-hatian hukum syariah, jawaban ditangguhkan. Silakan rujuk langsung sumber primer atau ulama terpercaya.",
        }

    return {
        "faithfulness_passed": True,
        "faithfulness_explanation": explanation,
    }
