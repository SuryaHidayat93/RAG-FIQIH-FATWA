from typing import Dict, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from src.config import settings
from src.state import RAGState


class GraderOutput(BaseModel):
    grade: Literal["relevan", "ambigu", "tidak_relevan"] = Field(
        description="'relevan' jika dokumen rujukan cukup untuk menjawab hukum fiqih/fatwa, 'ambigu' jika hanya sebagian aspek terjawab, 'tidak_relevan' jika dokumen tidak membahas hukum/topik yang ditanyakan."
    )
    explanation: str = Field(description="Alasan penilaian kesesuaian dokumen dengan pertanyaan.")


GRADER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """Anda adalah Penilai Relevansi Dokumen (CRAG Grader) untuk teks hukum Islam, Fiqih, dan Fatwa.
Tugas Anda: Menilai apakah kumpulan dokumen rujukan yang ditemukan relevan dan mencukupi untuk menjawab pertanyaan pengguna.
Kategori:
- 'relevan': Dokumen langsung memuat nash, fatwa, atau pembahasan bab fikih terkait masalah yang ditanyakan.
- 'ambigu': Dokumen membahas topik serupa tetapi belum tuntas atau hanya satu sudut pandang yang ada.
- 'tidak_relevan': Dokumen tidak memuat rujukan hukum yang dibutuhkan atau meleset dari topik pertanyaan.

Hasilkan HANYA output format JSON.""",
    ),
    (
        "human",
        "Pertanyaan: {query}\n\nDokumen Rujukan:\n{context}",
    ),
])


REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Anda bertugas merumuskan ulang (rewrite) query pencarian karena hasil sebelumnya tidak relevan. Buat query pencarian baru yang lebih fokus pada istilah teknis fikih Arab/Indonesia.",
    ),
    (
        "human",
        "Pertanyaan awal: {query}\nAlasan gagal: Dokumen tidak relevan.\nTulis query baru 1 kalimat:",
    ),
])


def grader_node(state: RAGState) -> Dict:
    """Node 4: Evaluasi relevansi dokumen hasil retrieval (CRAG)."""
    import time

    t_start = time.time()
    docs = state.get("reranked_documents", [])
    query = state.get("rewritten_query") or state.get("query")
    retry_count = state.get("retry_count", 0)

    print(f"\n[4/6] CRAG DOCUMENT GRADER (Relevance Verification)", flush=True)

    if not docs:
        print(f"  * Penilaian          : TIDAK_RELEVAN (Dokumen kosong)", flush=True)
        if retry_count < settings.max_crag_retries:
            print(f"  * Aksi               : Mengulang retrieval (Percobaan {retry_count + 1}/{settings.max_crag_retries})...", flush=True)
            return {"grade": "tidak_relevan", "retry_count": retry_count + 1}
        print(f"  * Aksi               : Batas retry tercapai -> ABSTAIN", flush=True)
        return {"grade": "tidak_relevan", "abstain": True}

    context_str = "\n\n".join(
        [f"[Doc {i+1} | {d.get('corpus')}]: {d.get('content')}" for i, d in enumerate(docs)]
    )

    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.primary_model,
        format="json",
        temperature=0.0,
    )
    structured_llm = llm.with_structured_output(GraderOutput)
    chain = GRADER_PROMPT | structured_llm

    explanation = ""
    try:
        result: GraderOutput = chain.invoke({"query": query, "context": context_str})
        grade = result.grade
        explanation = result.explanation
    except Exception as e:
        grade = "relevan"
        explanation = f"Fallback penilaian (error parser: {e})"

    elapsed = time.time() - t_start
    print(f"  * Hasil Evaluasi     : {grade.upper()} ({elapsed:.2f} detik)", flush=True)
    if explanation:
        print(f"  * Keterangan         : {explanation[:120]}...", flush=True)

    if grade == "tidak_relevan":
        if retry_count < settings.max_crag_retries:
            print(f"  * Aksi CRAG          : Dokumen belum relevan. Merumuskan ulang query (Retry {retry_count + 1})...", flush=True)
            rewrite_chain = REWRITE_PROMPT | llm
            res = rewrite_chain.invoke({"query": query})
            new_query = res.content.strip() if hasattr(res, "content") else query
            print(f"  * Query Baru (CRAG)  : \"{new_query}\"", flush=True)
            return {
                "grade": "tidak_relevan",
                "rewritten_query": new_query,
                "retry_count": retry_count + 1,
            }
        else:
            print(f"  * Aksi CRAG          : Batas retry ({settings.max_crag_retries}x) habis -> Rute ke ABSTAIN demi kehati-hatian", flush=True)
            return {"grade": "tidak_relevan", "abstain": True}

    print(f"  * Aksi CRAG          : Dokumen mencukupi -> Lanjut ke Generator Syariah", flush=True)
    return {"grade": grade, "abstain": False}
