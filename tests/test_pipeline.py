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


def test_langgraph_compilation():
    # Pastikan graph berhasil dikompilasi dan memiliki nodes yang sesuai
    assert app_graph is not None
    assert "query_understanding" in app_graph.nodes
    assert "parallel_retrieval" in app_graph.nodes
    assert "reranker" in app_graph.nodes
    assert "grader" in app_graph.nodes
    assert "generator" in app_graph.nodes
    assert "faithfulness_checker" in app_graph.nodes
