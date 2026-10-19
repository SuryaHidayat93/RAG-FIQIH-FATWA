"""Script evaluasi benchmark 10 pertanyaan syariah menggunakan Ragas Faithfulness
dengan Gemini 3.8 Flash via 9Router.
"""
import os
import sys
import time
import json
from pathlib import Path

# Setup encoding & root path
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

# 10 Pertanyaan Uji Representatif (Fiqih Madzhab Syafi'i & Fatwa MUI/DSN)
BENCHMARK_QUESTIONS = [
    # Topik Fatwa Kontemporer
    {"id": 1, "query": "Apa hukum bunga bank menurut fatwa MUI?", "kategori": "Fatwa"},
    {"id": 2, "query": "Bagaimana fatwa hukum paylater dalam transaksi online menurut DSN MUI?", "kategori": "Fatwa"},
    {"id": 3, "query": "Bagaimana hukum uang elektronik syariah menurut fatwa DSN MUI?", "kategori": "Fatwa"},
    {"id": 4, "query": "Bagaimana hukum cryptocurrency atau uang kripto menurut keputusan ijtima ulama fatwa MUI?", "kategori": "Fatwa"},
    {"id": 5, "query": "Bagaimana ketentuan jual beli emas secara cicilan atau angsuran menurut fatwa DSN MUI?", "kategori": "Fatwa"},

    # Topik Fiqih Klasik Syafi'i (Kitab Fathul Qarib)
    {"id": 6, "query": "Apakah menyentuh kulit istri membatalkan wudhu menurut madzhab Syafi'i?", "kategori": "Fiqih"},
    {"id": 7, "query": "Apa saja rukun dan fardhu wudhu menurut madzhab Syafi'i?", "kategori": "Fiqih"},
    {"id": 8, "query": "Berapa syarat jarak perjalanan bagi musafir agar boleh mengqashar shalat?", "kategori": "Fiqih"},
    {"id": 9, "query": "Berapa batas minimal ukuran air dua kullah dalam liter menurut madzhab Syafi'i?", "kategori": "Fiqih"},
    {"id": 10, "query": "Berapa nisab zakat emas dan perak serta kadar zakat yang wajib dikeluarkan?", "kategori": "Fiqih"},
]


def run_10_questions_benchmark():
    print("=" * 85)
    print("MEMULAI BENCHMARK EVALUASI 10 PERTANYAAN (RAGAS + GEMINI 3.8 FLASH VIA 9ROUTER)")
    print("=" * 85)

    questions = []
    answers = []
    all_contexts = []
    categories = []

    # 1. Jalankan pipeline untuk tiap pertanyaan
    for item in BENCHMARK_QUESTIONS:
        q_id = item["id"]
        q_text = item["query"]
        q_cat = item["kategori"]

        print(f"\n[{q_id}/10] Memproses Query ({q_cat}): \"{q_text}\"")
        t0 = time.time()
        state = {
            "query": q_text,
            "retry_count": 0,
            "retrieved_documents": [],
        }

        try:
            result = app_graph.invoke(state)
            # Gunakan draf jawaban asli generator untuk evaluasi objektif Ragas
            ans = result.get("raw_generation") or result.get("generation", "")
            docs = result.get("reranked_documents", [])
            ctx = [d.get("content", "") for d in docs]
        except Exception as e:
            print(f"  * Error: {e}")
            ans = "Gagal memproses."
            ctx = []

        elapsed = time.time() - t0
        print(f"  * Selesai dalam {elapsed:.2f}s | Dokumen: {len(ctx)} | Jawaban: {len(ans)} karakter")

        questions.append(q_text)
        answers.append(ans)
        all_contexts.append(ctx)
        categories.append(q_cat)

    # 2. Inisialisasi Evaluator Ragas dengan Gemini 3.8 Flash via 9Router
    print("\n" + "=" * 85)
    print("MENGHUBUNGKAN EVALUATOR RAGAS KE GEMINI 3.8 FLASH (9ROUTER)...")
    print("=" * 85)

    api_key = os.getenv("NINEROUTER_API_KEY") or settings.ninerouter_api_key
    evaluator_chat = ChatOpenAI(
        base_url=settings.ninerouter_base_url,
        api_key=api_key,
        model=settings.faithfulness_model,
        temperature=0.0,
    )
    evaluator_llm = LangchainLLMWrapper(evaluator_chat)
    faithfulness.llm = evaluator_llm

    # 3. Buat Dataset Ragas
    eval_dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": all_contexts,
    })

    print(f"\nMenjalankan Ragas Faithfulness Evaluation untuk {len(questions)} sampel...")
    t_eval_start = time.time()
    eval_result = evaluate(
        dataset=eval_dataset,
        metrics=[faithfulness],
        llm=evaluator_llm,
    )
    t_eval_total = time.time() - t_eval_start

    # 4. Tampilkan Tabel Hasil
    df_res = eval_result.to_pandas()
    # Pastikan kompatibilitas nama kolom Ragas (user_input atau question)
    q_col = "user_input" if "user_input" in df_res.columns else "question"
    df_res["kategori"] = categories
    df_res["question_text"] = questions

    print("\n" + "=" * 85)
    print("TABEL HASIL EVALUASI RESMI RAGAS FAITHFULNESS")
    print("=" * 85)
    print(f"{'No':<4} | {'Kategori':<8} | {'Skor':<7} | {'Pertanyaan'}")
    print("-" * 85)

    scores = []
    for idx, row in df_res.iterrows():
        score_val = row.get("faithfulness", 0.0)
        score_float = float(score_val) if score_val is not None and not str(score_val).lower() == "nan" else 0.0
        scores.append(score_float)
        q_text_row = row.get("question_text") or row.get(q_col, "")
        q_preview = str(q_text_row)[:55]
        print(f"{idx+1:<4} | {row['kategori']:<8} | {score_float:<7.4f} | {q_preview}...")

    avg_score = sum(scores) / len(scores) if scores else 0.0
    print("-" * 85)
    print(f"RATA-RATA SKOR FAITHFULNESS : {avg_score:.4f} / 1.0000 ({avg_score * 100:.2f}%)")
    print(f"Total Waktu Evaluasi Ragas   : {t_eval_total:.2f} detik")
    print("=" * 85)

    # Simpan laporan ke CSV dan JSON untuk artefak portofolio
    out_csv = Path("eval/benchmark_ragas_results.csv")
    out_json = Path("eval/benchmark_ragas_results.json")
    df_res.to_csv(out_csv, index=False)

    records = []
    for idx, row in df_res.iterrows():
        q_text_val = row.get("question_text") or row.get(q_col, "")
        s_val = row.get("faithfulness", 0.0)
        s_flt = float(s_val) if s_val is not None and not str(s_val).lower() == "nan" else 0.0
        records.append({
            "question": q_text_val,
            "kategori": row.get("kategori", ""),
            "faithfulness": round(s_flt, 4)
        })

    summary_data = {
        "evaluator_model": settings.faithfulness_model,
        "provider": "9Router (Local Endpoint)",
        "total_queries": len(questions),
        "average_faithfulness": round(avg_score, 4),
        "average_percentage": f"{avg_score * 100:.2f}%",
        "evaluation_duration_seconds": round(t_eval_total, 2),
        "results": records,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Laporan evaluasi tersimpan di:")
    print(f"  - {out_csv}")
    print(f"  - {out_json}")


if __name__ == "__main__":
    run_10_questions_benchmark()
