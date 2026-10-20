import sys
from pathlib import Path
import time
import requests

# Tambahkan root folder proyek ke sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from src.config import settings
from src.graph import app_graph

# Page Configuration
st.set_page_config(
    page_title="RAG Fiqih & Fatwa — AI Jurisprudence QA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Modern Production CSS)
st.markdown("""
<style>
    /* Metric & Card styling */
    .stMetric {
        background-color: #1E293B;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    .citation-card {
        background-color: #0F172A;
        border-left: 4px solid #38BDF8;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 0 6px 6px 0;
    }
    /* Input & Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        height: 44px;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar System Telemetry & Configuration
with st.sidebar:
    st.markdown("### ⚙️ System Telemetry")
    
    # Check services
    ollama_ok = False
    try:
        r = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=0.8)
        ollama_ok = (r.status_code == 200)
    except Exception:
        pass

    router_ok = False
    try:
        r2 = requests.get(f"{settings.ninerouter_base_url}/models", timeout=0.8)
        router_ok = (r2.status_code == 200)
    except Exception:
        pass

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.caption("Ollama (Llama 3.1)")
        st.markdown("🟢 **Active**" if ollama_ok else "🔴 **Offline**")
    with col_s2:
        st.caption("9Router (Gemini)")
        st.markdown("🟢 **Active**" if router_ok else "🟡 **Fallback**")

    st.markdown("---")
    st.markdown("### 📚 Korpus Terindeks")
    st.markdown("""
    - **10.987 Dokumen Fatwa**  
      *(DSN-MUI, MUI Pusat, Ijtima Ulama)*
    - **583 Pasal Fiqih Syafi'i**  
      *(Kitab Fathul Qarib Al-Mujib & Matan Taqrib)*
    """)

    st.markdown("---")
    st.markdown("### 🔬 Arsitektur Pipeline")
    st.caption("• **Router**: IndoBERT Fine-Tuned (<30ms)")
    st.caption("• **Retrieval**: BGE-M3 (GPU) + BM25 (RRF)")
    st.caption("• **Reranker**: BAAI/bge-reranker-v2-m3")
    st.caption("• **Decision**: CRAG Relevance Grader")
    st.caption("• **Generator**: Llama 3.1 8B (RTX 4050)")
    st.caption("• **Auditor**: Gemini 3.8 Flash (Self-RAG)")


# Main Header
st.title("⚖️ Asisten Fiqih & Fatwa Syariah AI")
st.markdown(
    "Sistem Tanya-Jawab Hukum Islam berbasis **Corrective RAG (CRAG)**, "
    "**Hybrid Retrieval (BGE-M3 + BM25)**, dan **Self-RAG Anti-Hallucination Guard**."
)

# Example Chips
st.markdown("##### 💡 Contoh Pertanyaan Cepat:")
sample_col1, sample_col2, sample_col3, sample_col4 = st.columns(4)

preset_query = ""
if sample_col1.button("💳 Hukum Paylater", key="btn_paylater"):
    preset_query = "Bagaimana fatwa hukum paylater dalam transaksi online menurut DSN MUI?"
if sample_col2.button("🏦 Bunga Bank", key="btn_bunga"):
    preset_query = "Apa hukum bunga bank menurut fatwa MUI?"
if sample_col3.button("🧼 Sentuh Kulit Istri", key="btn_istri"):
    preset_query = "Apakah menyentuh kulit istri membatalkan wudhu menurut madzhab Syafi'i?"
if sample_col4.button("🪙 Zakat Emas", key="btn_zakat"):
    preset_query = "Berapa nisab zakat emas dan perak serta kadar zakat yang wajib dikeluarkan?"

# Query Input
query = st.text_input(
    "Masukkan pertanyaan hukum syariah, fatwa, atau fiqih:",
    value=preset_query if preset_query else "",
    placeholder="Contoh: Bagaimana fatwa hukum uang elektronik syariah menurut DSN MUI?",
)


def execute_pipeline(query_text: str):
    """Menjalankan query melalui API jika aktif, atau fallback ke embedded LangGraph."""
    api_url = f"http://127.0.0.1:{settings.api_port}"
    try:
        h = requests.get(f"{api_url}/health", timeout=0.8)
        if h.status_code == 200:
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
                    "abstain": data.get("abstain", False),
                    "mode": "FastAPI Daemon Server",
                }
    except Exception:
        pass

    initial_state = {
        "query": query_text,
        "retry_count": 0,
        "retrieved_documents": [],
    }
    t0 = time.time()
    res = app_graph.invoke(initial_state)
    res["execution_time"] = time.time() - t0
    res["mode"] = "Embedded LangGraph Engine"
    return res


# Trigger Run
col_btn, col_info = st.columns([1, 4])
with col_btn:
    run_clicked = st.button("🔍 Analisis Hukum", type="primary")

if (run_clicked or preset_query) and query.strip():
    with st.spinner("Memproses pertanyaan melalui 6 tahap verifikasi syariah..."):
        t_start = time.time()
        try:
            result = execute_pipeline(query.strip())
            total_time = result.get("execution_time", time.time() - t_start)

            st.markdown("---")
            
            # KPI Dashboard Row
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            with m_col1:
                r_val = result.get("route", "UNKNOWN").upper()
                st.metric(label="Rute Korpus", value=r_val)
            
            with m_col2:
                g_val = result.get("grade", "RELEVAN").upper()
                st.metric(label="Status Relevansi CRAG", value=g_val)

            with m_col3:
                is_faithful = result.get("faithfulness_passed", True)
                st.metric(label="Self-RAG Verification", value="LULUS (FAITHFUL)" if is_faithful else "ABSTAIN (GUARDED)")

            with m_col4:
                st.metric(label="Total Latensi", value=f"{total_time:.1f} detik")

            st.markdown("<br>", unsafe_allow_html=True)

            # Tabbed View
            tab_ans, tab_docs, tab_audit = st.tabs([
                "📖 Jawaban Syariah & Sitasi",
                "📑 Dokumen Rujukan Reranked",
                "🔍 Log Telemetri Pipeline"
            ])

            with tab_ans:
                st.markdown("### Ketetapan Hukum & Penjelasan")
                
                if result.get("abstain", False):
                    st.warning(result.get("generation", ""))
                else:
                    st.markdown(result.get("generation", ""))

                citations = result.get("citations", [])
                if citations:
                    st.markdown("<br><h5>📚 Sumber Rujukan & Metadata:</h5>", unsafe_allow_html=True)
                    for c_idx, c in enumerate(citations, 1):
                        meta_items = []
                        if c.get("source"):
                            meta_items.append(f"**Sumber**: {c['source']}")
                        if c.get("nomor_fatwa"):
                            meta_items.append(f"**No**: {c['nomor_fatwa']}")
                        if c.get("mazhab"):
                            meta_items.append(f"**Mazhab**: {c['mazhab']}")
                        if c.get("bab"):
                            meta_items.append(f"**Bab**: {c['bab']}")
                        if c.get("halaman"):
                            meta_items.append(f"**Hal**: {c['halaman']}")

                        meta_str = " | ".join(meta_items)
                        st.markdown(f"""
                        <div class="citation-card">
                            <b>[{c_idx}] [{c.get('corpus', '').upper()}]</b> {meta_str}
                        </div>
                        """, unsafe_allow_html=True)

            with tab_docs:
                reranked = result.get("reranked_documents", [])
                st.markdown(f"### Top-{len(reranked)} Dokumen Terpilih (Hasil Cross-Encoder Rerank)")
                if reranked:
                    for i, doc in enumerate(reranked, 1):
                        score = doc.get("score", 0.0)
                        corpus = doc.get("corpus", "").upper()
                        meta = doc.get("metadata", {})
                        title = meta.get("topik") or meta.get("fasal") or meta.get("bab") or doc.get("id")
                        
                        with st.expander(f"Dokumen {i} [{corpus}] (Skor Relevansi: {score:.4f}) — {title}"):
                            st.caption(f"Metadata: {meta}")
                            st.text_area("Isi Teks Rujukan:", doc.get("content", ""), height=180, key=f"doc_txt_{i}")
                else:
                    st.info("Dokumen konteks dikelola oleh background daemon.")

            with tab_audit:
                st.markdown("### Rincian Pemeriksaan Anti-Halusinasi & Audit")
                st.write(f"**Engine Mode:** `{result.get('mode', 'Embedded')}`")
                st.write(f"**Query Asli:** `{query}`")
                st.write(f"**Query Rewrite (Optimasi Mesin Pencari):** `{result.get('rewritten_query')}`")
                st.write(f"**Evaluasi CRAG Grader:** `{result.get('grade')}`")
                st.write(f"**Status Faithfulness:** `{result.get('faithfulness_passed')}`")
                
                if result.get("faithfulness_explanation"):
                    st.info(f"**Catatan Evaluator Independen (Gemini 3.8 Flash):**\n\n{result.get('faithfulness_explanation')}")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses pertanyaan: {e}")
