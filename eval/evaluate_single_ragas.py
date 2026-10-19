"""Script evaluasi 1 pertanyaan menggunakan Ragas Faithfulness dengan Gemini 3.8 Flash via 9Router.
Mengukur:
1. Skor Faithfulness desimal (0.00 - 1.00).
2. Jumlah token input/output & estimasi biaya riil ke 9Router.
"""
import os
import sys
import time
from pathlib import Path

# Setup path root proyek & encoding utf-8
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.graph import app_graph
from src.config import settings
from langchain_openai import ChatOpenAI
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness
from ragas.llms import LangchainLLMWrapper


def run_single_ragas_evaluation(query_text: str):
    print("=" * 80)
    print(f"EVALUASI 1 PERTANYAAN MENGGUNAKAN RAGAS + GEMINI 3.8 FLASH VIA 9ROUTER")
    print(f"Pertanyaan: \"{query_text}\"")
    print("=" * 80)

    # 1. Jalankan pipeline lokal untuk mendapatkan Jawaban dan Konteks
    print("\n[Langkah 1/3] Menjalankan Pipeline RAG...")
    t0 = time.time()
    state = {
        "query": query_text,
        "retry_count": 0,
        "retrieved_documents": [],
    }
    result = app_graph.invoke(state)
    t_pipeline = time.time() - t0

    answer = result.get("generation", "")
    docs = result.get("reranked_documents", [])
    contexts = [d.get("content", "") for d in docs]

    print(f"✓ Pipeline selesai dalam {t_pipeline:.2f} detik")
    print(f"  * Dokumen konteks: {len(contexts)} dokumen")
    print(f"  * Panjang jawaban : {len(answer)} karakter")

    # 2. Setup Evaluator LLM di Ragas mengarah ke 9Router (Gemini 3.8 Flash)
    print("\n[Langkah 2/3] Menghubungkan Ragas ke 9Router Gemini 3.8 Flash...")
    api_key = os.getenv("NINEROUTER_API_KEY") or settings.ninerouter_api_key

    # Inisialisasi ChatOpenAI mengarah ke 9Router local endpoint
    evaluator_chat = ChatOpenAI(
        base_url=settings.ninerouter_base_url,
        api_key=api_key,
        model=settings.faithfulness_model,
        temperature=0.0,
    )
    evaluator_llm = LangchainLLMWrapper(evaluator_chat)
    faithfulness.llm = evaluator_llm

    # 3. Format dataset Ragas (HANYA question, answer, contexts - TANPA ground_truth)
    eval_dataset = Dataset.from_dict({
        "question": [query_text],
        "answer": [answer],
        "contexts": [contexts],
    })

    print("\n[Langkah 3/3] Menjalankan Evaluasi Ragas Faithfulness...")
    t_eval = time.time()
    eval_result = evaluate(
        dataset=eval_dataset,
        metrics=[faithfulness],
        llm=evaluator_llm,
    )
    t_eval_elapsed = time.time() - t_eval

    # Ambil hasil skor
    df_res = eval_result.to_pandas()
    faith_score = float(df_res["faithfulness"].iloc[0])

    print("\n" + "=" * 80)
    print("HASIL EVALUASI RESMI RAGAS:")
    print("=" * 80)
    print(f"Pertanyaan           : {query_text}")
    print(f"Model Evaluator      : {settings.faithfulness_model} (via 9Router)")
    print(f"Waktu Evaluasi Ragas : {t_eval_elapsed:.2f} detik")
    print(f"SKOR FAITHFULNESS    : {faith_score:.4f} / 1.0000 ({faith_score * 100:.1f}%)")
    print("=" * 80)

    # Estimasi token Ragas (2-stage evaluation: statement breakdown + verification)
    # Ragas rata-rata memakai ~7.000 - 9.000 token untuk 5 dokumen konteks
    est_prompt_tokens = int(sum(len(c) for c in contexts) / 3.5) + int(len(answer) / 3.5) + 1500
    est_completion_tokens = 350
    total_est_tokens = est_prompt_tokens + est_completion_tokens
    est_cost_usd = (est_prompt_tokens / 1_000_000) * 0.075 + (est_completion_tokens / 1_000_000) * 0.30

    print("\nESTIMASI KONSUMSI TOKEN GEMINI 3.8 FLASH DI 9ROUTER:")
    print("-" * 80)
    print(f"Estimasi Prompt Tokens     : ~{est_prompt_tokens:,} token")
    print(f"Estimasi Completion Tokens : ~{est_completion_tokens:,} token")
    print(f"Estimasi Total Tokens      : ~{total_est_tokens:,} token")
    print(f"Estimasi Biaya             : ~${est_cost_usd:.6f} USD (~Rp {est_cost_usd * 16000:.2f})")
    print("=" * 80)


if __name__ == "__main__":
    test_question = "Apa hukum bunga bank menurut fatwa MUI?"
    run_single_ragas_evaluation(test_question)
