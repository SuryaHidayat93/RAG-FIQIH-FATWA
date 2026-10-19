from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from src.config import settings
from src.state import Document, RAGState


GENERATOR_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """Anda adalah Asisten Pakar Fiqih dan Fatwa Syariah.
Tugas Anda menjawab pertanyaan hukum Islam dengan KETAT HANYA bersandarkan pada dokumen rujukan yang disediakan.

Pedoman Penulisan:
1. Rujukan & Sitasi: Salin NAMA SUMBER, NOMOR FATWA, atau NAMA KITAB PERSIS sebagaimana tercantum di bagian header dokumen rujukan. JANGAN mengarang atau memetakan nama sumber yang tidak tertulis.
2. Mazhab Fikih: Sebutkan mazhab yang tertera di dokumen (misal: Syafi'i, Kompilasi Hukum Islam Kontemporer, dll).
3. Dalil & Argumen: Kutip ayat Al-Qur'an, hadits, atau kaidah fiqih HANYA jika teks atau potongannya ada dalam dokumen rujukan.
4. JANGAN membuat analogi liar atau memasukkan pengetahuan di luar teks dokumen.
5. Jika dokumen membahas masalah terkait, jelaskan secara lugas dan faktual.""",
    ),
    (
        "human",
        """Pertanyaan:
{query}

Dokumen Rujukan:
{context}

Berikan jawaban terstruktur dan faktual berdasarkan dokumen rujukan di atas:""",
    ),
])


def format_context(documents: List[Document]) -> str:
    parts = []
    for i, doc in enumerate(documents, start=1):
        meta = doc.get("metadata", {})
        meta_info = ", ".join(f"{k}: {v}" for k, v in meta.items() if v)
        header = f"[Dokumen {i} | Korpus: {doc.get('corpus').upper()} | {meta_info}]"
        parts.append(f"{header}\n{doc.get('content')}")
    return "\n\n".join(parts)


def extract_citations(documents: List[Document]) -> List[Dict[str, Any]]:
    citations = []
    for doc in documents:
        meta = doc.get("metadata", {})
        citations.append({
            "corpus": doc.get("corpus"),
            "source": meta.get("kitab") or meta.get("lembaga") or "Tidak diketahui",
            "bab": meta.get("bab"),
            "halaman": meta.get("halaman"),
            "nomor_fatwa": meta.get("nomor_fatwa"),
            "mazhab": meta.get("mazhab"),
        })
    return citations


def generator_node(state: RAGState) -> Dict:
    """Node 5: Generator jawaban syariah dengan kewajiban sitasi, mazhab, dan khilafiyah."""
    import time

    t_start = time.time()
    print(f"\n[5/6] SYARIAH GENERATOR (Ollama {settings.primary_model})", flush=True)

    if state.get("abstain", False):
        print(f"  * Status             : ABSTAIN (Sistem menolak spekulasi tanpa rujukan valid)", flush=True)
        return {
            "generation": "Maaf, sistem tidak menemukan rujukan teks fatwa atau kitab fiqih yang cukup dan terverifikasi untuk menjawab pertanyaan ini secara bertanggung jawab. Disarankan berkonsultasi langsung kepada ulama/mufti yang kompeten.",
            "citations": [],
            "faithfulness_passed": True,
        }

    docs = state.get("reranked_documents", [])
    query = state.get("query")
    print(f"  * Konteks Masukan    : {len(docs)} dokumen rujukan terverifikasi", flush=True)
    print(f"  * Memulai Inferensi  : Menyusun jawaban syariah (mazhab, dalil, khilafiyah, sitasi)...", flush=True)

    context_str = format_context(docs)

    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.primary_model,
        temperature=0.1,
    )

    chain = GENERATOR_PROMPT | llm
    response = chain.invoke({"query": query, "context": context_str})

    answer = response.content if hasattr(response, "content") else str(response)
    citations = extract_citations(docs)

    elapsed = time.time() - t_start
    print(f"  * Selesai Generasi   : {len(answer)} karakter ({elapsed:.2f} detik)", flush=True)
    print(f"  * Daftar Sitasi Rujukan ({len(citations)} sumber):", flush=True)
    for c_idx, c in enumerate(citations[:3], start=1):
        src = c.get("source", "")
        no_fatwa = f" No: {c['nomor_fatwa']}" if c.get("nomor_fatwa") else ""
        mzh = f" Mazhab: {c['mazhab']}" if c.get("mazhab") else ""
        print(f"    {c_idx}. [{c.get('corpus', '').upper()}] {src}{no_fatwa}{mzh}", flush=True)

    return {
        "generation": answer,
        "raw_generation": answer,
        "citations": citations,
    }
