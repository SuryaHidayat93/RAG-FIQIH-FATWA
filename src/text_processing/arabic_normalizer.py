import re
from typing import List


# Regex pattern untuk tashkeel / harakat Arab
ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")

# Map normalisasi huruf Arab
ARABIC_CHAR_MAP = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ى": "ي",
    "ئ": "ي",
    "ؤ": "و",
    "ة": "ه",
    "گ": "ك",
    "پ": "ب",
}

# Map variasi transliterasi fiqih Latin ke bentuk baku untuk BM25
TRANSLITERATION_MAP = {
    r"\bsholat\b": "salat",
    r"\bsholatnya\b": "salatnya",
    r"\bsolat\b": "salat",
    r"\bwudhu\b": "wudu",
    r"\bwudlu\b": "wudu",
    r"\brudhu\b": "wudu",
    r"\biddah\b": "idah",
    r"\b'iddah\b": "idah",
    r"\bthoharoh\b": "taharah",
    r"\bthaharah\b": "taharah",
    r"\bjanabah\b": "junub",
    r"\bkhimar\b": "jilbab",
    r"\bhadast\b": "hadas",
    r"\bhadats\b": "hadas",
    r"\bmu'amalah\b": "muamalah",
    r"\bmadzhab\b": "mazhab",
    r"\bqaul\b": "pendapat",
}


def remove_arabic_diacritics(text: str) -> str:
    """Hapus harakat/tashkeel dari teks Arab."""
    return ARABIC_DIACRITICS.sub("", text)


def normalize_arabic_letters(text: str) -> str:
    """Standarisasi varian alif, ya/alif maqsuroh, dan ta marbuthoh."""
    for char, target in ARABIC_CHAR_MAP.items():
        text = text.replace(char, target)
    return text


def normalize_transliteration(text: str) -> str:
    """Standarisasi ejaan kata serapan istilah fiqih Indonesia."""
    lower_text = text.lower()
    for pattern, replacement in TRANSLITERATION_MAP.items():
        lower_text = re.sub(pattern, replacement, lower_text)
    return lower_text


def normalize_islamic_text(text: str) -> str:
    """Pipeline penuh pembersihan teks Fiqih & Fatwa."""
    cleaned = remove_arabic_diacritics(text)
    cleaned = normalize_arabic_letters(cleaned)
    cleaned = normalize_transliteration(cleaned)
    # Bersihkan multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenisasi teks setelah dinormalisasi untuk input BM25."""
    normalized = normalize_islamic_text(text)
    tokens = re.findall(r"[\w\u0600-\u06FF]+", normalized.lower())
    return tokens
