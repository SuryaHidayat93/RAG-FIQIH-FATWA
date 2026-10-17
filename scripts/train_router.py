"""Script untuk Fine-tuning IndoBERT Router menggunakan dataset pertanyaan syariah."""
import json
import os
from pathlib import Path
import numpy as np
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset
from src.config import settings
from src.router.indobert_router import ID2LABEL, LABEL2ID


def load_dataset(dataset_path: str = "./data/router_dataset.json"):
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item["text"] for item in data]
    labels = [LABEL2ID[item["label"]] for item in data]
    return texts, labels


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    preds = np.argmax(predictions, axis=1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="macro")
    return {"accuracy": acc, "macro_f1": f1}


def train_router(
    dataset_path: str = "./data/router_dataset.json",
    output_dir: str = "./models/indobert_router",
    epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 3e-5,
):
    print("Memuat dataset training router...")
    texts, labels = load_dataset(dataset_path)

    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    base_model_name = settings.indobert_base_model
    print(f"Mengunduh base model & tokenizer: {base_model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=128)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=128)

    train_dataset = Dataset.from_dict({
        "input_ids": train_encodings["input_ids"],
        "attention_mask": train_encodings["attention_mask"],
        "labels": train_labels,
    })

    val_dataset = Dataset.from_dict({
        "input_ids": val_encodings["input_ids"],
        "attention_mask": val_encodings["attention_mask"],
        "labels": val_labels,
    })

    model = AutoModelForSequenceClassification.from_pretrained(
        base_model_name,
        num_labels=len(ID2LABEL),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    training_args = TrainingArguments(
        output_dir="./models/checkpoints",
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        logging_steps=5,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print("Memulai training fine-tuning IndoBERT...")
    trainer.train()

    print(f"Menyimpan model terbaik ke {output_dir}...")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Fine-tuning IndoBERT selesai!")


if __name__ == "__main__":
    train_router()
