# Log Perkembangan Proyek: RAG Fiqih & Fatwa

Dokumen ini mencatat tahapan arsitektur, implementasi teknis, dan pemrosesan data yang telah diselesaikan.

---

## 1. Desain Arsitektur Sistem
Pipeline dirancang dengan arsitektur **Corrective RAG (CRAG)** dan **Self-RAG (Faithfulness)**:
1. **Query Understanding & Router**: Normalisasi teks istilah syariah + klasifikasi rute (`fatwa`, `fiqih`, `keduanya`, `di_luar_cakupan`).
2. **Parallel Hybrid Retrieval**:
   - Korpus Fatwa: Dense (BGE-M3) + BM25 $\rightarrow$ Reciprocal Rank Fusion (RRF).
   - Korpus Fiqih: Dense (BGE-M3) + BM25 $\rightarrow$ Reciprocal Rank Fusion (RRF).
   - Dijalankan paralel hanya pada korpus terpilih.
3. **Cross-Encoder Reranker**: `bge-reranker-v2-m3` untuk menyaring ke top-k dokumen terbaik.
4. **CRAG Grader**: Evaluasi relevansi dokumen. Jika tidak relevan, lakukan query rewrite (maksimal 1x retry), lalu rute ke mode *abstain* bila tetap tidak relevan.
5. **Generator Syariah**: LLM (Llama 3.1 8B) dengan prompt terikat pada rujukan kitab, bab, pasal, nomor fatwa, mazhab, dan khilafiyah.
6. **Faithfulness Checker (Self-RAG)**: Pengujian keabsahan jawaban terhadap konteks dokumen rujukan guna mencegah halusinasi hukum syar'i.

---

## 2. Infrastruktur & Scaffolding Proyek
- **Lingkungan Kerja**: Git worktree terisolasi (`oke-lakukan-setup`), Python 3.13 (`.venv`).
- **Dependensi Utama**: `langgraph`, `langchain-ollama`, `qdrant-client`, `rank-bm25`, `sentence-transformers`, `torch`, `fastapi`, `uvicorn`, `streamlit`, `beautifulsoup4`, `pytest`.
- **StateGraph LangGraph**: [src/graph.py](src/graph.py) dengan TypedDict [src/state.py](src/state.py).
- **Interface Pengguna & API**:
  - FastAPI: [src/api/main.py](src/api/main.py) (`/ask`, `/health`).
  - Streamlit Dashboard: [src/ui/app.py](src/ui/app.py) dengan visualisasi status CRAG & sitasi dokumen.

---

## 3. Pemrosesan Teks Syariah & Persistensi
- **Normalisasi Teks Arab & Transliterasi**: [src/text_processing/arabic_normalizer.py](src/text_processing/arabic_normalizer.py)
  - Penghapusan tashkeel/harakat Arab.
  - Standarisasi varian huruf (alif, ya/alif maqsuroh, ta marbuthoh).
  - Standarisasi istilah fiqih serapan Latin (*sholat* $\rightarrow$ *salat*, *wudhu* $\rightarrow$ *wudu*, *madzhab* $\rightarrow$ *mazhab*).
  - Tokenizer khusus BM25.
- **Persistensi BM25 ke Disk**: [src/retrieval/bm25_retriever.py](src/retrieval/bm25_retriever.py)
  - Fitur `save()` dan `load()` otomatis dari disk (`.pkl`) di `data/bm25/`.

---

## 4. Router Cepat IndoBERT
- **Arsitektur Router**: Pengalihan dari LLM ke model klasifikasi kecil berbasis transformer (`IndoBERT`) untuk latency rendah ($<30$ ms) dan hemat resource.
- **Dataset Latih**: [data/router_dataset.json](data/router_dataset.json) berisi **335 data berlabel seimbang**:
  - `fatwa`: 93 contoh
  - `fiqih`: 83 contoh
  - `keduanya`: 81 contoh
  - `di_luar_cakupan`: 78 contoh
- **Modul & Skrip Latih**: [src/router/indobert_router.py](src/router/indobert_router.py) dan [scripts/train_router.py](scripts/train_router.py).

---

## 5. Pengumpulan, Audit, & Pembersihan Data Fiqih
- **Sumber Korpus**: Clone repositori `kode-27-id/fathul.qarib` (Kitab *Fathul Qarib Al-Mujib*, 18 bab lengkap karya Syamsuddin Ibnu Qasim Al-Ghazi & Matan Abu Syuja').
- **Audit Masalah Data Mentah**:
  - Ditemukan kebocoran spasi antar karakter (`M u q o d d i m a h`).
  - Tag HTML rusak (`b>`, `i>`, `,br>`, `&nbsp;`, garis footnote `------`).
  - Teks matan Arab dan terjemahan Indonesia terpisah blok paragraf.
  - Distribusi ukuran tidak berimbang (ada bab berukuran 120.000 karakter yang melampaui window embedding).
- **Pembersihan & Chunking Adaptif**: [scripts/clean_and_parse_fathul_qarib.py](scripts/clean_and_parse_fathul_qarib.py)
  - Menghilangkan seluruh artefak tag rusak dan navigasi.
  - Memasangkan matan Arab asli dengan terjemahan Indonesia per pasal.
  - Chunking adaptif (target 600–1.500 karakter, rata-rata 1.162 karakter) agar fit dalam window model `BAAI/bge-m3` tanpa terpotong.
- **Hasil Korpus Fiqih Bersih**: [data/fiqih/fathul_qarib_full.json](data/fiqih/fathul_qarib_full.json) berisi **543 dokumen pasal lengkap**:
  - Bab 01 (Muqaddimah): 1 chunk
  - Bab 02 (Thaharah / Bersuci): 56 chunk
  - Bab 03 (Shalat Fardhu & Sunnah): 120 chunk
  - Bab 04 (Shalat Berjamaah & Khusus): 12 chunk
  - Bab 05 (Zakat Mal & Fitrah): 24 chunk
  - Bab 06 (Puasa & I'tikaf): 20 chunk
  - Bab 07 (Haji & Umrah): 26 chunk
  - Bab 08 (Muamalah, Jual Beli, & Waris): 91 chunk
  - Bab 09 (Munakahat / Pernikahan): 77 chunk
  - Bab 10 (Talak, Rujuk, Iddah, & Hadhanah): 13 chunk
  - Bab 11 (Jinayat / Pidana & Qisas): 7 chunk
  - Bab 12 (Hudud / Zina, Qadzaf, Pencurian): 11 chunk
  - Bab 13 (Jihad): 22 chunk
  - Bab 14 (Sembelihan, Qurban, Aqiqah): 6 chunk
  - Bab 15 (Perlombaan & Memanah): 2 chunk
  - Bab 16 (Sumpah & Nazar): 2 chunk
  - Bab 17 (Peradilan / Qadha & Saksi): 42 chunk
  - Bab 18 (Pembebasan Budak): 11 chunk

## 6. Pembersihan & Ekstraksi Korpus Fatwa PDF
- **Sumber Data**: 572 berkas PDF Fatwa MUI dan DSN-MUI (fintech, e-money, perbankan, pasar modal, sosial, medis, pangan halal).
- **Pembersihan Mendalam ([scripts/ingest_fatwa_pdf.py](scripts/ingest_fatwa_pdf.py))**:
  - **Margin Filtering (Bounding Box PyMuPDF)**: Membuang running header atas ($y < 55$) dan running footer bawah ($y > \text{height} - 55$).
  - **Hyphenation Repair**: Menyambung pemotongan kata di akhir baris (`penda-\npat` $\rightarrow$ `pendapat`).
  - **Pembersihan Nomor Halaman**: Mengeliminasi 1.718 nomor halaman terisolasi di baris mandiri.
  - **Pembersihan Footer Kontak/Kantor**: Membuang teks alamat kantor, nomor telepon, fax, dan website sekretariat.
  - **Filter Noise Daftar Absensi/Peserta**: Mengidentifikasi dan membuang 95 chunk yang murni berisi daftar nama peserta/gelar tanpa substansi hukum fatwa.
  - **Perbaikan Karakter**: Memperbaiki tanda petik dan tanda tanya pada kata serapan istilah syariah (*Ijtima'*, *Syar'i*, *Kaidah*).
- **Hasil Korpus Fatwa Bersih**: [data/fatwa/fatwa_pdf_corpus.json](data/fatwa/fatwa_pdf_corpus.json) berisi **10.983 dokumen pasal/chunk fatwa bersih**.
- **Persistensi BM25 Fatwa**: Selesai dibangun dan tersimpan di [data/bm25/fatwa_bm25.pkl](data/bm25/fatwa_bm25.pkl) (terverifikasi presisi tinggi).

## 7. Verifikasi & Pengujian
- Unit test terdaftar di [tests/test_pipeline.py](tests/test_pipeline.py):
  - Normalisasi teks Arab & Latin.
  - Tokenisasi BM25.
  - Penggabungan skor Reciprocal Rank Fusion (RRF).
  - Persistensi save/load BM25 ke disk.
  - Fallback & prediksi router IndoBERT.
  - Kompilasi StateGraph LangGraph.
- Status pengujian: **6/6 passed (100%)**.

## 8. Status & Langkah Berikutnya
- [x] Desain arsitektur CRAG + Self-RAG
- [x] StateGraph LangGraph & nodes pipeline
- [x] Normalizer istilah syariah & Arab
- [x] Persistensi index BM25
- [x] Scaffolding IndoBERT Router + 335 dataset latih
- [x] Ekstraksi & pembersihan 543 dokumen Fathul Qarib
- [x] Ekstraksi, pembersihan mendalam, & BM25 indexing 10.987 dokumen Fatwa PDF
- [x] Penyelesaian dense embedding Qdrant untuk korpus fatwa via GPU RTX 4050 (10.987 vektor)
- [ ] Pengujian retrieval end-to-end dengan query fikih & fatwa riil (FastAPI & Streamlit)
