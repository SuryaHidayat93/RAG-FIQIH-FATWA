# RAG Fiqih & Fatwa Syariah

Sistem Tanya Jawab Hukum Islam dan Fatwa Kontemporer berbasis arsitektur **Corrective RAG (CRAG)**, **Parallel Hybrid Retrieval (Dense BGE-M3 + BM25 dengan RRF)**, dan **Self-RAG (Faithfulness Checker)**.

## Alur Kerja Pipeline

```
Query
  ↓
[1] Query Understanding (normalisasi teks Arab/Latin + rewrite + router)
    → fatwa | fiqih | keduanya | di_luar_cakupan
  ↓
[2] Parallel Retrieval
    Fatwa: dense (bge-m3) + BM25 → RRF
    Fiqih: dense (bge-m3) + BM25 → RRF
  ↓
[3] Rerank
    cross-encoder (bge-reranker-v2-m3) → top-k
  ↓
[4] Grader (CRAG)
    relevan | ambigu | tidak relevan (rewrite query 1x, jika gagal -> abstain)
  ↓
[5] Generator
    penjelasan mazhab, rujukan kitab/fatwa, paparan khilafiyah
  ↓
[6] Faithfulness Check
    evaluasi grounding jawaban terhadap rujukan (lolos / abstain)
  ↓
Jawaban + Sitasi Spesifik (Kitab, Bab, Hal, atau No. Fatwa)
```

## Setup & Instalasi

1. **Aktifkan Virtual Environment**:
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```

2. **Instal Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurasi Environment**:
   Salin `.env.example` menjadi `.env` lalu sesuaikan konfigurasi model Ollama dan Qdrant.

4. **Jalankan Indexing Data Contoh**:
   ```bash
   python scripts/index_corpus.py
   ```

5. **Jalankan API (FastAPI)**:
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

6. **Jalankan UI (Streamlit)**:
   ```bash
   streamlit run src/ui/app.py
   ```
