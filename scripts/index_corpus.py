"""Script untuk indexing korpus Fatwa dan Fiqih dari file JSON ke Qdrant dan file BM25 disk."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from qdrant_client.models import PointStruct
from src.retrieval.dense_retriever import DenseRetriever
from src.retrieval.bm25_retriever import CorpusBM25Index
from src.state import Document


def load_corpus_from_dir(directory_path: str, default_corpus: str) -> List[Document]:
    """Membaca semua file JSON di folder korpus."""
    p = Path(directory_path)
    all_docs: List[Document] = []

    if not p.exists():
        return all_docs

    for json_file in p.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        item.setdefault("corpus", default_corpus)
                        all_docs.append(item)
                elif isinstance(data, dict):
                    data.setdefault("corpus", default_corpus)
                    all_docs.append(data)
            print(f"Berhasil memuat file: {json_file.name} (total akumulasi: {len(all_docs)} dokumen)")
        except Exception as e:
            print(f"Gagal memuat {json_file.name}: {e}")

    return all_docs


def index_data():
    print("=== Memulai Inisialisasi Hybrid Indexing (Dense Qdrant + BM25 Disk) ===")
    dense = DenseRetriever()
    dense.ensure_collection("fatwa")
    dense.ensure_collection("fiqih")

    corpora = [
        ("fatwa", "./data/fatwa"),
        ("fiqih", "./data/fiqih"),
    ]

    for corpus_name, dir_path in corpora:
        docs = load_corpus_from_dir(dir_path, corpus_name)
        if not docs:
            print(f"Peringatan: Tidak ada dokumen di {dir_path}")
            continue

        print(f"\n[1/2] Indexing {len(docs)} dokumen ke Qdrant '{corpus_name}'...")
        texts = [d["content"] for d in docs]
        vectors = dense.embed_texts(texts)

        points = []
        for i, (doc, vec) in enumerate(zip(docs, vectors)):
            points.append(
                PointStruct(
                    id=i + 1,
                    vector=vec,
                    payload={
                        "content": doc["content"],
                        "corpus": doc["corpus"],
                        "metadata": doc.get("metadata", {}),
                    },
                )
            )

        dense.client.upsert(collection_name=corpus_name, points=points)
        print(f"✓ Koleksi Qdrant '{corpus_name}' berhasil di-upsert!")

        print(f"[2/2] Membangun dan menyimpan index BM25 '{corpus_name}' ke disk...")
        bm25_index = CorpusBM25Index(corpus_name=corpus_name)
        bm25_index.build_index(docs)
        saved_path = bm25_index.save()
        print(f"✓ Index BM25 '{corpus_name}' disimpan ke: {saved_path}")

    print("\n=== Seluruh Indexing Korpus Fatwa & Fiqih Selesai ===")


if __name__ == "__main__":
    index_data()
