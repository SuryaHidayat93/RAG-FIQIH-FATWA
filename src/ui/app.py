import sys
from pathlib import Path

# Tambahkan root folder proyek ke sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from src.graph import app_graph
from src.config import settings

st.set_page_config(
    page_title="Tanya Fiqih & Fatwa AI",
    page_icon="📖",
    layout="wide",
)

st.title("📖 Asisten Cerdas Fiqih & Fatwa Kontemporer")
st.markdown("Sistem QA Syariah dengan **CRAG**, **Hybrid Retrieval (Dense BGE-M3 + BM25)**, dan **Self-RAG**")

with st.sidebar:
    st.header("⚙️ Pengaturan LLM & Retrieval")
    selected_model = st.selectbox(
        "Pilih Model Ollama",
        [settings.primary_model, settings.comparison_model],
        index=0,
    )
    st.info(f"Embedding: {settings.embedding_model_name}\nReranker: {settings.reranker_model_name}")
    st.markdown("---")
    st.markdown("### Korpus Tersedia")
    st.markdown("- **Fatwa**: DSN-MUI, Tarjih Muhammadiyah, Bahtsul Masail NU")
    st.markdown("- **Fiqih**: Kitab Turats Mazhab Syafi'i, Hanafi, Maliki, Hanbali")

query = st.text_input(
    "Masukkan pertanyaan hukum Islam / fiqih / fatwa:",
    placeholder="Contoh: Bagaimana hukum paylater dalam transaksi online menurut fatwa DSN MUI?",
)

import requests

def run_query(query_text: str):
    api_url = f"http://127.0.0.1:{settings.api_port}"
    try:
        h = requests.get(f"{api_url}/health", timeout=1.0)
        if h.status_code == 200:
            print(f">>> [STREAMLIT] Meneruskan query ke FastAPI Server ({api_url})...", flush=True)
            res = requests.post(f"{api_url}/ask", json={"query": query_text}, timeout=300)
            if res.status_code == 200:
                data = res.json()
                return {
                    "generation": data.get("answer", ""),
                    "citations": data.get("citations", []),
                    "route": data.get("route", ""),
                    "rewritten_query": data.get("rewritten_query", query_text),
                    "grade": "relevan" if not data.get("abstain") else "tidak_relevan",
                    "faithfulness_passed": data.get("faithfulness_passed", True),
                    "faithfulness_explanation": data.get("faithfulness_explanation"),
                    "reranked_documents": data.get("reranked_documents", []),
                    "mode": "FastAPI Server",
                }
    except Exception:
        pass

    initial_state = {
        "query": query_text,
        "retry_count": 0,
        "retrieved_documents": [],
    }
    res = app_graph.invoke(initial_state)
    res["mode"] = "Embedded Graph"
    return res

if st.button("Cari Jawaban Hukum", type="primary") and query:
    with st.spinner("Memproses pertanyaan melalui pipeline LangGraph..."):
        try:
            result = run_query(query)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📝 Jawaban Syariah")
                st.markdown(result.get("generation", ""))

                citations = result.get("citations", [])
                if citations:
                    st.markdown("### 📚 Rujukan & Sitasi")
                    for c in citations:
                        ref_parts = []
                        if c.get("source"):
                            ref_parts.append(f"**Sumber**: {c['source']}")
                        if c.get("nomor_fatwa"):
                            ref_parts.append(f"**No. Fatwa**: {c['nomor_fatwa']}")
                        if c.get("mazhab"):
                            ref_parts.append(f"**Mazhab**: {c['mazhab']}")
                        if c.get("bab"):
                            ref_parts.append(f"**Bab**: {c['bab']}")
                        if c.get("halaman"):
                            ref_parts.append(f"**Hal**: {c['halaman']}")
                        st.markdown(f"- {', '.join(ref_parts)}")

            with col2:
                st.subheader("🔍 Status Pipeline (CRAG & Self-RAG)")
                st.write(f"**Router:** `{result.get('route')}`")
                st.write(f"**Query Rewrite:** `{result.get('rewritten_query')}`")
                st.write(f"**Grader CRAG:** `{result.get('grade')}`")
                st.write(f"**Faithfulness Passed:** `{result.get('faithfulness_passed')}`")
                if result.get("faithfulness_explanation"):
                    st.caption(f"Catatan verifikasi: {result.get('faithfulness_explanation')}")

                reranked = result.get("reranked_documents", [])
                if reranked:
                    with st.expander(f"Lihat {len(reranked)} Dokumen Reranked"):
                        for i, doc in enumerate(reranked, 1):
                            st.markdown(f"**Doc {i} ({doc.get('corpus').upper()} | Skor: {doc.get('score'):.4f})**")
                            st.text(doc.get("content")[:300] + "...")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses pertanyaan: {e}")
