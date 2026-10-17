"""Modul evaluasi RAG Fiqih & Fatwa menggunakan BERTScore dan RAGAS."""
from typing import Dict, List
import pandas as pd
from datasets import Dataset


def evaluate_with_bertscore(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """Menghitung BERTScore (Precision, Recall, F1) antara jawaban dan referensi rujukan."""
    try:
        from bert_score import score
        P, R, F1 = score(predictions, references, lang="id", verbose=False)
        return {
            "bertscore_precision": float(P.mean().item()),
            "bertscore_recall": float(R.mean().item()),
            "bertscore_f1": float(F1.mean().item()),
        }
    except Exception as e:
        print(f"BERTScore evaluation warning: {e}")
        return {"bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0}


def evaluate_with_ragas(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: List[str],
) -> Dict[str, float]:
    """Menghitung metrik RAGAS: faithfulness, answer_relevancy, context_precision."""
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision

        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
        dataset = Dataset.from_dict(data)
        metrics = [faithfulness, answer_relevancy, context_precision]
        result = evaluate(dataset, metrics=metrics)
        return result.to_pandas().mean(numeric_only=True).to_dict()
    except Exception as e:
        print(f"RAGAS evaluation warning: {e}")
        return {}


if __name__ == "__main__":
    sample_preds = ["Menurut Fatwa DSN MUI No. 116, uang elektronik syariah diperbolehkan jika bebas riba dan gharar."]
    sample_refs = ["Fatwa DSN MUI 116 menyatakan uang elektronik halal selama akad sesuai syariah dan tidak mengandung riba."]

    print("Contoh Evaluasi BERTScore:")
    res = evaluate_with_bertscore(sample_preds, sample_refs)
    print(res)
