import os
from pathlib import Path
from typing import Dict, Literal, Tuple, Union
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from src.config import settings

ID2LABEL = {0: "fatwa", 1: "fiqih", 2: "keduanya", 3: "di_luar_cakupan"}
LABEL2ID = {"fatwa": 0, "fiqih": 1, "keduanya": 2, "di_luar_cakupan": 3}

RouteType = Literal["fatwa", "fiqih", "keduanya", "di_luar_cakupan"]


class IndoBERTRouter:
    def __init__(self, model_path: Union[str, None] = None):
        self.model_path = model_path or settings.indobert_model_path
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()

    def _load_model(self):
        """Memuat model fine-tuned jika ada di direktori model_path."""
        p = Path(self.model_path)
        if p.exists() and (p / "config.json").exists():
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(str(p))
                self.model = AutoModelForSequenceClassification.from_pretrained(str(p))
                self.model.to(self.device)
                self.model.eval()
            except Exception as e:
                print(f"Peringatan: Gagal memuat fine-tuned IndoBERT dari {p}: {e}")
                self.model = None

    def is_trained_model_available(self) -> bool:
        return self.model is not None and self.tokenizer is not None

    def predict(self, text: str) -> Tuple[RouteType, float]:
        """Klasifikasi rute pertanyaan menggunakan IndoBERT fine-tuned atau rule-based fallback."""
        if self.is_trained_model_available():
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)
                pred_id = torch.argmax(probs, dim=-1).item()
                confidence = float(probs[0, pred_id].item())
                return ID2LABEL.get(pred_id, "keduanya"), confidence

        # Fallback heuristik syariah jika model belum di-train
        lower = text.lower()
        has_fatwa = any(w in lower for w in ["fatwa", "mui", "dsn", "tarjih", "bahtsul", "paylater", "crypto", "pinjol"])
        has_fiqih = any(w in lower for w in ["wudhu", "wudu", "shalat", "salat", "mazhab", "madzhab", "syafii", "faraidh", "sujud", "qunut", "thaharah", "fardhu", "rukun"])
        is_general = any(w in lower for w in ["coding", "python", "resep", "cuaca", "liga", "windows", "react", "fastapi"])

        if is_general and not (has_fatwa or has_fiqih):
            return "di_luar_cakupan", 0.90
        if has_fatwa and has_fiqih:
            return "keduanya", 0.85
        if has_fatwa:
            return "fatwa", 0.85
        if has_fiqih:
            return "fiqih", 0.85
        return "keduanya", 0.50
