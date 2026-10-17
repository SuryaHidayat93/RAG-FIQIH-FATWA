from pathlib import Path
import pytest
from src.text_processing.arabic_normalizer import (
    normalize_islamic_text,
    remove_arabic_diacritics,
    normalize_arabic_letters,
    normalize_transliteration,
    tokenize_for_bm25,
)
from src.retrieval.hybrid_retriever import reciprocal_rank_fusion
from src.state import Document
from src.graph import app_graph


def test_arabic_normalizer():
    # Test penghapusan harakat
    arabic_with_tashkeel = "الصَّلَاةُ"
    assert remove_arabic_diacritics(arabic_with_tashkeel) == "الصلاة"

    # Test alif / ya normalisasi
    raw_arabic = "فَتْوَى إِسْلَامِيَّة"
    cleaned = normalize_islamic_text(raw_arabic)
    assert "فتوي" in cleaned or "اسلاميه" in cleaned

    # Test transliterasi fiqih Latin
    latin_query = "bagaimana sholat dan wudhu orang yang hadast?"
    normalized = normalize_transliteration(latin_query)
    assert "salat" in normalized
    assert "wudu" in normalized
    assert "hadas" in normalized


def test_tokenize_for_bm25():
    text = "Hukum Sholat dengan Wudhu yang batal"
    tokens = tokenize_for_bm25(text)
    assert "salat" in tokens
    assert "wudu" in tokens


def test_reciprocal_rank_fusion():
    doc1: Document = {"id": "1", "content": "teks 1", "corpus": "fatwa", "score": 0.9}
    doc2: Document = {"id": "2", "content": "teks 2", "corpus": "fatwa", "score": 0.8}
    doc3: Document = {"id": "3", "content": "teks 3", "corpus": "fatwa", "score": 0.7}

    list_a = [doc1, doc2]
    list_b = [doc2, doc3]

    fused = reciprocal_rank_fusion([list_a, list_b], k=60, top_n=3)
    assert len(fused) == 3
    # doc2 muncul di kedua daftar pada rank tinggi sehingga harus dapat skor tertinggi
    assert fused[0]["id"] == "2"


def test_bm25_save_and_load(tmp_path):
    from src.retrieval.bm25_retriever import CorpusBM25Index

    idx = CorpusBM25Index("test_corpus", storage_dir=str(tmp_path))
    docs = [
        {"id": "1", "content": "tata cara wudhu membasuh muka dan tangan", "corpus": "fiqih"},
        {"id": "2", "content": "tata cara shalat menghadap kiblat dan takbir", "corpus": "fiqih"},
        {"id": "3", "content": "ketentuan zakat fitrah dan mal", "corpus": "fiqih"},
        {"id": "4", "content": "hukum puasa ramadhan dan syarat wajib", "corpus": "fiqih"},
    ]
    idx.build_index(docs)
    saved_file = idx.save(str(tmp_path))
    assert Path(saved_file).exists()

    # Load ke instance baru
    idx2 = CorpusBM25Index("test_corpus", storage_dir=str(tmp_path))
    assert len(idx2.documents) == 4
    res = idx2.search("shalat kiblat", top_k=1)
    assert len(res) == 1
    assert res[0]["id"] == "2"


def test_langgraph_compilation():
    # Pastikan graph berhasil dikompilasi dan memiliki nodes yang sesuai
    assert app_graph is not None
    assert "query_understanding" in app_graph.nodes
    assert "parallel_retrieval" in app_graph.nodes
    assert "reranker" in app_graph.nodes
    assert "grader" in app_graph.nodes
    assert "generator" in app_graph.nodes
    assert "faithfulness_checker" in app_graph.nodes
