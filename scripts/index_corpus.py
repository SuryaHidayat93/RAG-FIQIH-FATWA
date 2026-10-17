"""Script untuk indexing korpus Fatwa dan Fiqih ke Qdrant dan file BM25."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from qdrant_client.models import PointStruct
from src.retrieval.dense_retriever import DenseRetriever
from src.retrieval.bm25_retriever import CorpusBM25Index
from src.state import Document


SAMPLE_FATWA_DATA = [
    {
        "id": "fatwa-dsn-116",
        "content": "Fatwa DSN-MUI No. 116/DSN-MUI/IX/2017 tentang Uang Elektronik Syariah. Ketentuan umum: Uang elektronik syariah wajib terbebas dari riba, gharar, maysir, tadlis, risywah, dan isyraf. Akad penerbitan uang elektronik antara penerbit dan pemegang adalah wadi'ah atau qardh. Apabila terdapat biaya fasilitas, akad yang digunakan adalah ijarah.",
        "corpus": "fatwa",
        "metadata": {
            "lembaga": "DSN-MUI",
            "nomor_fatwa": "116/DSN-MUI/IX/2017",
            "tahun": 2017,
            "topik": "Uang Elektronik Syariah",
            "mazhab": "Kompilasi Hukum Ekonomi Syariah",
        },
    },
    {
        "id": "fatwa-dsn-140",
        "content": "Fatwa DSN-MUI No. 140/DSN-MUI/VIII/2021 tentang Penyelenggaraan Pembiayaan Berbasis Teknologi Informasi Berdasarkan Prinsip Syariah (Peer-to-Peer Financing). Layanan pinjam meminjam online (fintech) boleh dilakukan menggunakan akad al-bai', ijarah, mudharabah, musyarakah, wakalah bi al-ujrah, dan qardh, serta dilarang mengenakan bunga pinjaman ribawi.",
        "corpus": "fatwa",
        "metadata": {
            "lembaga": "DSN-MUI",
            "nomor_fatwa": "140/DSN-MUI/VIII/2021",
            "tahun": 2021,
            "topik": "Fintech P2P Lending & Paylater",
            "mazhab": "Kompilasi Hukum Ekonomi Syariah",
        },
    },
]

SAMPLE_FIQIH_DATA = [
    {
        "id": "fiqih-fathul-qarib-wudu",
        "content": "Fathul Qarib Al-Mujib fi Syarh Alfazh At-Taqrib karya Ibnu Qasim Al-Ghazi. Faslun fi Furu'il Wudhu'. Fardhu wudhu ada enam perkara: (1) Niat saat membasuh wajah, (2) Membasuh seluruh muka, (3) Membasuh kedua tangan sampai siku, (4) Mengusap sebagian kepala, (5) Membasuh kedua kaki sampai mata kaki, (6) Tertib sesuai urutan.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Fathul Qarib Al-Mujib",
            "pengarang": "Ibnu Qasim Al-Ghazi",
            "bab": "Thaharah / Fardhu Wudhu",
            "halaman": "12-14",
            "mazhab": "Syafi'i",
        },
    },
    {
        "id": "fiqih-bidayatul-mujtahid-salat",
        "content": "Bidayatul Mujtahid wa Nihayatul Muqtashid karya Ibnu Rusyd Al-Qurthubi. Kitab As-Shalah, Mas'alah Raf'ul Yadain (Mengangkat kedua tangan dalam salat). Ulama berbeda pendapat mengenai mengangkat tangan selain takbiratul ihram. Imam Syafi'i dan Ahmad berpendapat sunnah mengangkat tangan ketika ruku' dan bangkit dari ruku'. Sedangkan Imam Abu Hanifah dan sebagian riwayat Imam Malik berpendapat tidak disunnahkan selain takbiratul ihram.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Bidayatul Mujtahid",
            "pengarang": "Ibnu Rusyd",
            "bab": "Shalat / Khilafiyah Raf'ul Yadain",
            "halaman": "150-153",
            "mazhab": "Perbandingan Mazhab (Syafi'i, Hanafi, Maliki, Hanbali)",
        },
    },
]


def index_data():
    print("Memulai inisialisasi Qdrant dan indexing korpus...")
    dense = DenseRetriever()
    dense.ensure_collection("fatwa")
    dense.ensure_collection("fiqih")

    for corpus_name, dataset in [("fatwa", SAMPLE_FATWA_DATA), ("fiqih", SAMPLE_FIQIH_DATA)]:
        print(f"Indexing {len(dataset)} dokumen ke koleksi '{corpus_name}'...")
        texts = [d["content"] for d in dataset]
        vectors = dense.embed_texts(texts)

        points = []
        for i, (doc, vec) in enumerate(zip(dataset, vectors)):
            points.append(
                PointStruct(
                    id=i + 1,
                    vector=vec,
                    payload={
                        "content": doc["content"],
                        "corpus": doc["corpus"],
                        "metadata": doc["metadata"],
                    },
                )
            )

        dense.client.upsert(collection_name=corpus_name, points=points)
        print(f"Koleksi Qdrant '{corpus_name}' selesai diindeks!")

        # Indexing & persistensi BM25 ke disk
        bm25_index = CorpusBM25Index(corpus_name=corpus_name)
        bm25_index.build_index(dataset)
        saved_path = bm25_index.save()
        print(f"Index BM25 '{corpus_name}' disimpan ke: {saved_path}")


if __name__ == "__main__":
    index_data()
