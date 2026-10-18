"""Script untuk indexing korpus Fatwa dan Fiqih dari file JSON ke Qdrant dan file BM25 disk."""
import json
import os
import sys
from pathlib import Path

# Pastikan root direktori proyek ada di sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Any, Dict, List
from qdrant_client.models import PointStruct
from src.retrieval.dense_retriever import DenseRetriever
from src.retrieval.bm25_retriever import CorpusBM25Index
from src.state import Document

sys.stdout.reconfigure(encoding="utf-8")


def load_corpus_from_dir(directory_path: str, default_corpus: str) -> List[Document]:
    """Membaca semua file JSON di folder korpus."""
    p = Path(directory_path)
    all_docs: List[Document] = []

    if not p.exists():
        return all_docs

    for json_file in sorted(p.glob("*.json")):
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
    import torch
    torch.set_num_threads(14)

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

        print(f"\n--- Memproses Korpus '{corpus_name}' ({len(docs)} dokumen) ---")

        # 1. BM25 Indexing terlebih dahulu (cepat & langsung tersimpan ke disk)
        print(f"[1/2] Membangun dan menyimpan index BM25 '{corpus_name}' ke disk...")
        bm25_index = CorpusBM25Index(corpus_name=corpus_name)
        bm25_index.build_index(docs)
        saved_path = bm25_index.save()
        print(f"✓ Index BM25 '{corpus_name}' disimpan ke: {saved_path}")

        # 2. Qdrant Dense Embedding
        collection_info = dense.client.get_collection(corpus_name)
        existing_points = collection_info.points_count or 0
        print(f"[2/2] Koleksi Qdrant '{corpus_name}' saat ini memiliki {existing_points} vektor (Target: {len(docs)}).")

        if existing_points >= len(docs):
            print(f"✓ Koleksi Qdrant '{corpus_name}' sudah terisi lengkap ({existing_points} vektor). Lewati dense embedding.")
            continue

        print(f"Menghitung embedding dense (BGE-M3) dalam batch (64)...")
        # Inisialisasi/reset koleksi jika data bertambah banyak agar ID selaras
        if existing_points > 0 and existing_points < len(docs):
            dense.client.delete_collection(corpus_name)
            dense.ensure_collection(corpus_name)

        chunk_size = 500
        total_docs = len(docs)

        for start_idx in range(0, total_docs, chunk_size):
            end_idx = min(start_idx + chunk_size, total_docs)
            batch_docs = docs[start_idx:end_idx]
            batch_texts = [d["content"] for d in batch_docs]

            print(f"  Embedding batch [{start_idx + 1} - {end_idx} / {total_docs}]...")
            vectors = dense.embed_texts(batch_texts, batch_size=64, show_progress_bar=False)

            points = []
            for offset, (doc, vec) in enumerate(zip(batch_docs, vectors)):
                pt_id = start_idx + offset + 1
                points.append(
                    PointStruct(
                        id=pt_id,
                        vector=vec,
                        payload={
                            "doc_id": doc.get("id"),
                            "content": doc["content"],
                            "corpus": doc["corpus"],
                            "metadata": doc.get("metadata", {}),
                        },
                    )
                )

            dense.client.upsert(collection_name=corpus_name, points=points)
            print(f"  ✓ {end_idx} dari {total_docs} vektor berhasil di-upsert ke Qdrant.")

        print(f"✓ Koleksi Qdrant '{corpus_name}' berhasil di-upsert penuh ({total_docs} vektor)!")

    print("\n=== Seluruh Indexing Korpus Fatwa & Fiqih Berhasil Selesai ===")


if __name__ == "__main__":
    index_data()
