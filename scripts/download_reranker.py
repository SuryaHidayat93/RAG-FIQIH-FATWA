"""Script untuk mengunduh bobot model BAAI/bge-reranker-v2-m3 secara lengkap ke cache lokal HuggingFace."""
import os
import sys
from huggingface_hub import snapshot_download

# Matikan warning symlinks Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

MODEL_ID = "BAAI/bge-reranker-v2-m3"

def download_reranker():
    print(f"=== Mengunduh Model Reranker: {MODEL_ID} ===")
    print("Ukuran total sekitar ~2.2 GB. Menggunakan resumable download...")
    try:
        path = snapshot_download(
            repo_id=MODEL_ID,
            resume_download=True,
            max_workers=4,
        )
        print(f"\n✓ Berhasil mengunduh model reranker ke:\n{path}")
        return True
    except Exception as e:
        print(f"\n✗ Gagal mengunduh: {e}")
        return False

if __name__ == "__main__":
    success = download_reranker()
    if success:
        # Test inisialisasi CrossEncoder di GPU
        print("\nMemverifikasi model di CrossEncoder (device: CUDA)...")
        import torch
        from sentence_transformers import CrossEncoder
        device = "cuda" if torch.cuda.is_available() else "cpu"
        ce = CrossEncoder(MODEL_ID, device=device)
        test_score = ce.predict([["hukum bunga bank", "bunga bank adalah riba"]])
        print(f"✓ Model aktif di {device}! Skor uji: {test_score[0]:.4f}")
