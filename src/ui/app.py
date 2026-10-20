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
    page_title="Asisten Fiqih & Fatwa Syariah",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Clean End-User Production UI)
st.markdown("""
<style>
    /* Styling card sitasi & rujukan */
    .citation-card {
        background-color: #1E293B;
        border-left: 4px solid #10B981;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
    }
    .badge-tag {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 8px;
    }
    .badge-fatwa {
        background-color: #0369A1;
        color: #E0F2FE;
    }
    .badge-fiqih {
        background-color: #047857;
        color: #ECFDF5;
    }
    .badge-keduanya {
        background-color: #6D28D9;
        color: #EDE9FE;
    }
    .badge-verified {
        background-color: #065F46;
        color: #D1FAE5;
    }
    .badge-warning {
        background-color: #991B1B;
        color: #FEE2E2;
    }
    /* Tombol cari */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        height: 46px;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar Ramah Pengguna (Client-Facing Information)
with st.sidebar:
    st.markdown("### 📖 Tentang Layanan")
    st.markdown("""
    Layanan cerdas penelusuran fatwa dan kajian hukum Islam yang merujuk langsung pada sumber primer keagamaan.
    """)

    st.markdown("---")
    st.markdown("### 📚 Sumber Rujukan Resmi")
    st.markdown("""
    - **Himpunan Fatwa Resmi Indonesia**:
      - Dewan Syariah Nasional (DSN-MUI)
      - Komisi Fatwa Majelis Ulama Indonesia (MUI)
      - Keputusan Ijtima Ulama Se-Indonesia
    - **Kitab Fiqih Turats (Mazhab Syafi'i)**:
      - *Matan Al-Ghayah wat Taqrib* (Al-Qadhi Abu Syuja')
      - *Fathul Qarib Al-Mujib* (Ibnu Qasim Al-Ghazi)
      - *Safinatun Najah* & *Kifayatul Akhyar*
    """)

    st.markdown("---")
    st.markdown("### ⚠️ Catatan Syar'i")
    st.caption(
        "Jawaban yang disajikan merupakan hasil penelusuran dokumen literatur keagamaan dan fatwa tertulis. "
        "Untuk fatwa kasus pribadi yang bersifat kasuistik dan kompleks, disarankan tetap berkonsultasi langsung "
        "dengan ulama, asatidz, atau lembaga fatwa resmi."
    )


# Main Header
st.title("⚖️ Asisten Fiqih & Fatwa Syariah")
st.markdown("Konsultasi dan penelusuran hukum Islam berbasis naskah fatwa resmi dan literatur fikih terpercaya.")

# Example Chips
st.markdown("##### 💡 Topik Populer:")
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
    "Ajukan pertanyaan hukum syariah, ibadah, muamalah, atau fatwa:",
    value=preset_query if preset_query else "",
    placeholder="Ketik pertanyaan di sini (contoh: Bagaimana hukum zakat fitrah dibayar dengan uang?)...",
)


def execute_pipeline(query_text: str):
    """Menjalankan query melalui API backend jika aktif, atau fallback ke embedded engine."""
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
                    "faithfulness_passed": data.get("faithfulness_passed", True),
                    "reranked_documents": data.get("reranked_documents", []),
                    "abstain": data.get("abstain", False),
                }
    except Exception:
        pass

    initial_state = {
        "query": query_text,
        "retry_count": 0,
        "retrieved_documents": [],
    }
    return app_graph.invoke(initial_state)


# Action
col_btn, _ = st.columns([1, 4])
with col_btn:
    run_clicked = st.button("Cari Jawaban Hukum", type="primary")

if (run_clicked or preset_query) and query.strip():
    with st.spinner("Mencari dalil dan naskah hukum terkait..."):
        try:
            result = execute_pipeline(query.strip())

            st.markdown("---")

            # Human-friendly Category & Verification Badges
            route_raw = result.get("route", "").lower()
            if route_raw == "fatwa":
                cat_label = "Fatwa Kontemporer (DSN-MUI)"
                cat_class = "badge-fatwa"
            elif route_raw == "fiqih":
                cat_label = "Fiqih Klasik (Mazhab Syafi'i)"
                cat_class = "badge-fiqih"
            elif route_raw == "keduanya":
                cat_label = "Kombinasi Fiqih & Fatwa"
                cat_class = "badge-keduanya"
            else:
                cat_label = "Di Luar Cakupan Syariah"
                cat_class = "badge-warning"

            is_faithful = result.get("faithfulness_passed", True)
            is_abstain = result.get("abstain", False)

            if is_abstain or not is_faithful:
                verif_label = "⚠️ Rujukan Belum Mencukupi (Ditangguhkan)"
                verif_class = "badge-warning"
            else:
                verif_label = "✓ Terverifikasi Sesuai Rujukan Teks"
                verif_class = "badge-verified"

            st.markdown(f"""
            <div>
                <span class="badge-tag {cat_class}">Domain: {cat_label}</span>
                <span class="badge-tag {verif_class}">{verif_label}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Jawaban Utama
            st.markdown("### 📝 Ketetapan Hukum & Penjelasan")
            if is_abstain:
                st.warning(result.get("generation", ""))
            else:
                st.markdown(result.get("generation", ""))

            # Bagian Rujukan & Sitasi
            citations = result.get("citations", [])
            if citations and not is_abstain:
                st.markdown("<br>### 📚 Rujukan Teks Terkait", unsafe_allow_html=True)
                for idx, c in enumerate(citations, 1):
                    details = []
                    if c.get("source"):
                        details.append(f"**Sumber**: {c['source']}")
                    if c.get("nomor_fatwa"):
                        details.append(f"**Nomor**: {c['nomor_fatwa']}")
                    if c.get("mazhab"):
                        details.append(f"**Mazhab**: {c['mazhab']}")
                    if c.get("bab"):
                        details.append(f"**Bab**: {c['bab']}")
                    if c.get("halaman"):
                        details.append(f"**Halaman**: {c['halaman']}")

                    details_str = " | ".join(details)
                    st.markdown(f"""
                    <div class="citation-card">
                        <b>[{idx}]</b> {details_str}
                    </div>
                    """, unsafe_allow_html=True)

            # Detail Kutipan Naskah Asli (Accordion Tersembunyi)
            reranked = result.get("reranked_documents", [])
            if reranked and not is_abstain:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📖 Lihat Kutipan Naskah Asli Dokumen Rujukan"):
                    for i, doc in enumerate(reranked, 1):
                        meta = doc.get("metadata", {})
                        title = meta.get("topik") or meta.get("fasal") or meta.get("bab") or doc.get("id")
                        st.markdown(f"**Kutipan {i}: {title}**")
                        st.text_area(f"Teks Dokumen {i}", doc.get("content", ""), height=150, key=f"raw_doc_{i}")

        except Exception as e:
            st.error(f"Terjadi kendala saat memproses pertanyaan: {e}")
