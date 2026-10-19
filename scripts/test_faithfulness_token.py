"""Script uji ukur konsumsi token Faithfulness Checker menggunakan Gemini 3.8 Flash via 9Router."""
import os
import sys
import time
from pathlib import Path

# Setup UTF-8 encoding untuk Windows Terminal
sys.stdout.reconfigure(encoding="utf-8")

# Setup path root proyek
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.graph import app_graph
from src.nodes.generator_node import format_context
from src.nodes.faithfulness_node import FAITHFULNESS_PROMPT, FAITHFULNESS_PARSER
from src.config import settings
from openai import OpenAI


def run_token_audit_single_query(query: str):
    print("=" * 80)
    print(f"UJI UKUR TOKEN FAITHFULNESS CHECKER (GEMINI 3.8 FLASH)")
    print(f"Pertanyaan: \"{query}\"")
    print("=" * 80)

    # 1. Jalankan pipeline RAG lokal untuk mendapatkan jawaban dan dokumen konteks
    print("\n[Langkah 1/2] Menjalankan Pipeline Lokal (Retrieval + Generator Llama 3.1)...")
    t0 = time.time()
    state = {
        "query": query,
        "retry_count": 0,
        "retrieved_documents": [],
    }
    # Jalankan sampai generator
    pipeline_res = app_graph.invoke(state)
    t_pipeline = time.time() - t0

    answer = pipeline_res.get("generation", "")
    docs = pipeline_res.get("reranked_documents", [])
    context_str = format_context(docs)

    print(f"✓ Pipeline selesai dalam {t_pipeline:.2f} detik")
    print(f"  * Dokumen Terambil: {len(docs)} dokumen ({len(context_str)} karakter)")
    print(f"  * Panjang Jawaban : {len(answer)} karakter")

    # 2. Siapkan prompt Faithfulness Checker persis seperti di pipeline
    print("\n[Langkah 2/2] Mengirim Audit ke Gemini 3.8 Flash via 9Router...")
    prompt_value = FAITHFULNESS_PROMPT.format_prompt(
        context=context_str,
        generation=answer,
        format_instructions=FAITHFULNESS_PARSER.get_format_instructions(),
    )
    messages = prompt_value.to_messages()

    openai_messages = []
    for m in messages:
        role = "system" if m.type == "system" else "user"
        openai_messages.append({"role": role, "content": m.content})

    api_key = os.getenv("NINEROUTER_API_KEY") or settings.ninerouter_api_key
    client = OpenAI(
        base_url=settings.ninerouter_base_url,
        api_key=api_key,
    )

    t_eval = time.time()
    response = client.chat.completions.create(
        model=settings.faithfulness_model,
        messages=openai_messages,
        temperature=0.0,
    )
    t_eval_elapsed = time.time() - t_eval

    # Ambil rincian token dari response OpenAI/9Router
    usage = response.usage
    output_text = response.choices[0].message.content

    print("=" * 80)
    print("HASIL PENGUJIAN & KONSUMSI TOKEN GEMINI 3.8 FLASH:")
    print("=" * 80)
    print(f"Model Evaluator   : {settings.faithfulness_model}")
    print(f"Waktu Respon      : {t_eval_elapsed:.2f} detik")
    print("-" * 80)
    if usage:
        print(f"Prompt Tokens     : {usage.prompt_tokens:,} token (Konteks 5 dokumen + Draf Jawaban)")
        print(f"Completion Tokens : {usage.completion_tokens:,} token (Output Evaluasi JSON)")
        print(f"Total Tokens      : {usage.total_tokens:,} token")
        print("-" * 80)
        # Estimasi biaya Gemini 1.5/2.0 Flash ($0.075 per 1M prompt tokens, $0.30 per 1M output tokens)
        est_cost_prompt = (usage.prompt_tokens / 1_000_000) * 0.075
        est_cost_completion = (usage.completion_tokens / 1_000_000) * 0.30
        est_cost_total = est_cost_prompt + est_cost_completion
        print(f"Estimasi Biaya    : ${est_cost_total:.6f} USD (~Rp {est_cost_total * 16000:.2f}) per pertanyaan")
    else:
        print("Usage token info tidak dikirim oleh provider.")

    print("-" * 80)
    print("Output Evaluasi Gemini:")
    print(output_text)
    print("=" * 80)


if __name__ == "__main__":
    test_query = "Apa hukum bunga bank menurut fatwa MUI?"
    run_token_audit_single_query(test_query)
