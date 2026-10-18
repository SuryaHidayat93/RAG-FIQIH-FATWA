"""Script ekstraksi PDF Fatwa (DSN-MUI / MUI / Tarjih / Bahtsul Masail) ke korpus JSON RAG."""
import json
import re
import sys
from pathlib import Path
import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8")


def clean_pdf_text(text: str) -> str:
    """Bersihkan teks ekstraksi PDF."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Hapus baris nomor halaman tunggal
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)
    # Hapus spasi ganda
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_metadata_from_text(text: str, filename: str) -> dict:
    """Ekstraksi nomor fatwa, tahun, dan topik dari isi teks fatwa."""
    nomor_match = re.search(r"(?:Nomor|No\.?)\s*[:\s]*([0-9]+/[^\n\r]+)", text, re.IGNORECASE)
    tentang_match = re.search(r"TENTANG\s*\n+([^\n\r]+(?:\n+[^\n\r]+)?)", text, re.IGNORECASE)
    tahun_match = re.search(r"\b(19\d\d|20\d\d)\b", text)

    nomor_fatwa = nomor_match.group(1).strip() if nomor_match else ""
    topik = re.sub(r"\s+", " ", tentang_match.group(1)).strip() if tentang_match else filename
    tahun = int(tahun_match.group(1)) if tahun_match else None

    lembaga = "DSN-MUI" if "dewan syariah nasional" in text.lower() else "MUI"

    return {
        "lembaga": lembaga,
        "nomor_fatwa": nomor_fatwa,
        "topik": topik,
        "tahun": tahun,
        "sumber_file": filename,
        "mazhab": "Kompilasi Hukum Islam Kontemporer",
    }


def chunk_text(text: str, target_size: int = 1000, max_size: int = 1500) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_para = []
    current_len = 0

    for p in paragraphs:
        if current_len + len(p) > max_size and current_para:
            chunks.append("\n\n".join(current_para))
            current_para = []
            current_len = 0
        current_para.append(p)
        current_len += len(p) + 2
        if current_len >= target_size:
            chunks.append("\n\n".join(current_para))
            current_para = []
            current_len = 0

    if current_para:
        chunks.append("\n\n".join(current_para))

    return chunks


def process_fatwa_pdfs(pdf_dir: str = "./data/fatwa") -> list[dict]:
    p = Path(pdf_dir)
    pdf_files = list(p.glob("*.pdf"))

    if not pdf_files:
        print(f"Tidak ada file PDF ditemukan di {p.resolve()}.")
        print("Silakan salin file PDF dokumen fatwa ke folder tersebut.")
        return []

    print(f"Ditemukan {len(pdf_files)} file PDF fatwa di {pdf_dir}:")
    for f in pdf_files:
        print(f" - {f.name}")

    all_docs = []

    for f in pdf_files:
        print(f"\nMemproses {f.name}...")
        try:
            doc = fitz.open(f)
        except Exception as e:
            print(f"Gagal membuka {f.name}: {e}")
            continue

        full_pages_text = []
        for page_num in range(len(doc)):
            page_text = doc[page_num].get_text("text")
            cleaned_page = clean_pdf_text(page_text)
            if cleaned_page:
                full_pages_text.append((page_num + 1, cleaned_page))

        doc.close()

        if not full_pages_text:
            print(f"Warning: Tidak ada teks terbaca dari {f.name} (kemungkinan scan gambar).")
            continue

        # Gabungkan seluruh teks untuk metadata
        entire_text = "\n\n".join([pt[1] for pt in full_pages_text])
        meta = extract_metadata_from_text(entire_text[:2000], f.name)

        # Chunk per halaman atau gabungan halaman
        chunks = chunk_text(entire_text, target_size=1000, max_size=1500)
        print(f"✓ Berhasil membuat {len(chunks)} chunk dari {f.name}")

        for idx, chunk in enumerate(chunks, start=1):
            doc_id = f"fatwa-pdf-{f.stem[:20]}-chunk{idx:03d}"
            header = f"[Dokumen Fatwa | Lembaga: {meta['lembaga']} | Topik: {meta['topik']}"
            if meta.get("nomor_fatwa"):
                header += f" | No: {meta['nomor_fatwa']}"
            header += "]"

            content = f"{header}\n\n{chunk}"

            all_docs.append({
                "id": doc_id,
                "content": content,
                "corpus": "fatwa",
                "metadata": {
                    **meta,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                },
            })

    output_file = Path("data/fatwa/fatwa_pdf_corpus.json")
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(all_docs, out, ensure_ascii=False, indent=2)

    print(f"\nTotal {len(all_docs)} dokumen fatwa dari PDF disimpan ke: {output_file}")
    return all_docs


if __name__ == "__main__":
    process_fatwa_pdfs()
