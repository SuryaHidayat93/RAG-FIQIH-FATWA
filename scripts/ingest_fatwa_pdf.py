"""Script ekstraksi dan pembersihan mendalam PDF Fatwa (DSN-MUI / MUI / Tarjih / Bahtsul Masail) ke korpus JSON RAG."""
import json
import re
import sys
from pathlib import Path
import pymupdf  # PyMuPDF modern API

sys.stdout.reconfigure(encoding="utf-8")


def clean_pdf_text(text: str) -> str:
    """Membersihkan teks ekstraksi PDF dari hyphenation, artefak font, dan karakter liar."""
    # 1. Hapus kontrol karakter non-printable
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 2. Sambung pemotongan kata di akhir baris (hyphenation at line break)
    text = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", text)

    # 3. Hapus angka halaman terisolasi di satu baris
    text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)

    # 4. Hapus garis strip panjang, titik-titik panjang, garis bawah panjang
    text = re.sub(r"-{4,}", "", text)
    text = re.sub(r"\.{4,}", "", text)
    text = re.sub(r"_{4,}", "", text)

    # 5. Perbaiki tanda tanya di kata istilah Arab/Indonesia
    text = re.sub(r"(\b(?:ijtima|syar|mas|qur|ba|ru|ta|fatwa|fuqaha)\w*)\?", r"\1'", text, flags=re.IGNORECASE)
    text = re.sub(r"(\b[a-zA-Z]+)\?([a-zA-Z]+\b)", r"\1'\2", text)

    # 6. Ganti petik tanya di awal/akhir kutipan
    text = re.sub(r"\?([A-Z])", r'"\1', text)
    text = re.sub(r"([a-z\.\,\!\;])\?", r'\1"', text)

    # 7. Hapus running header/footer berbasis pola regex
    text = re.sub(
        r"(?i)^\s*(?:D\s*ew\s*an\s*Sy\s*ar\s*i\s*ah.*|Telp:.*|Fax:.*|Website:.*|Halaman\s+\d+.*)$",
        "",
        text,
        flags=re.M,
    )

    # 8. Bersihkan whitespace dan baris kosong
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_clean_blocks_from_page(page, top_margin: float = 55.0, bottom_margin: float = 55.0) -> list[str]:
    """Ekstraksi teks dengan membuang running header di margin atas dan running footer di margin bawah."""
    rect = page.rect
    blocks = page.get_text("blocks")
    page_text_blocks = []

    for b in blocks:
        x0, y0, x1, y1, text, b_no, b_type = b
        t = text.strip()
        if not t:
            continue

        # Abaikan blok di margin atas/bawah jika pendek (running header / page number / footer)
        if y1 < top_margin and len(t) < 140:
            continue
        if y0 > (rect.height - bottom_margin) and len(t) < 140:
            continue

        # Abaikan running address/footer DSN/MUI
        if re.search(r"(?:telp|fax|gedung menara topas|jl\.\s*proklamasi|sekretariat\s*:|halaman\s+\d+)", t, re.IGNORECASE):
            continue

        page_text_blocks.append(t)

    return page_text_blocks


def is_attendee_or_signatory_noise(chunk: str) -> bool:
    """Mendeteksi apakah suatu chunk hanya berisi daftar nama peserta/absensi tanpa teks fatwa."""
    if re.search(
        r"(?:MEMUTUSKAN|Menetapkan|Pertama|Kedua|Ketiga|Keempat|Ketentuan Hukum|Ketentuan Umum|Batasan|Syarat|Mengingat|Menimbang)",
        chunk,
        re.IGNORECASE,
    ):
        return False

    lines = [l.strip() for l in chunk.split("\n") if l.strip()]
    if len(lines) > 5:
        attendee_lines = sum(
            1 for l in lines if re.search(r"(?:MUI\s+[A-Za-z]|SH|MH|M\.Ag|H\.|Drs\.|K\.H\.|Prof\.|Dr\.)", l)
        )
        if attendee_lines / len(lines) > 0.4:
            return True
    return False


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
    pdf_files = sorted(list(p.glob("*.pdf")), key=lambda x: x.name)

    if not pdf_files:
        print(f"Tidak ada file PDF ditemukan di {p.resolve()}.")
        return []

    total_files = len(pdf_files)
    print(f"Ditemukan {total_files} file PDF fatwa di {pdf_dir}. Memulai pembersihan & ekstraksi...")

    all_docs = []
    scanned_count = 0
    noise_chunks_dropped = 0
    success_count = 0

    for file_idx, f in enumerate(pdf_files, start=1):
        if file_idx % 25 == 0 or file_idx == 1 or file_idx == total_files:
            print(f"[{file_idx}/{total_files}] Memproses: {f.name[:60]}... (Akumulasi chunk: {len(all_docs)})")

        try:
            doc = pymupdf.open(f)
        except Exception as e:
            print(f"Error buka {f.name}: {e}")
            continue

        full_pages_text = []
        for page_num in range(len(doc)):
            page_blocks = extract_clean_blocks_from_page(doc[page_num], top_margin=55.0, bottom_margin=55.0)
            page_content = "\n\n".join(page_blocks)
            cleaned_page = clean_pdf_text(page_content)
            if cleaned_page:
                full_pages_text.append(cleaned_page)

        doc.close()

        if not full_pages_text:
            scanned_count += 1
            continue

        entire_text = "\n\n".join(full_pages_text)
        if len(entire_text) < 50:
            scanned_count += 1
            continue

        meta = extract_metadata_from_text(entire_text[:2500], f.name)
        chunks = chunk_text(entire_text, target_size=1000, max_size=1500)
        success_count += 1

        for idx, chunk in enumerate(chunks, start=1):
            if is_attendee_or_signatory_noise(chunk):
                noise_chunks_dropped += 1
                continue

            doc_id = f"fatwa-pdf-{file_idx:04d}-chunk{idx:03d}"
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

    print(f"\nPembersihan & Ekstraksi selesai:")
    print(f"- Total file PDF: {total_files}")
    print(f"- PDF berhasil dibersihkan: {success_count}")
    print(f"- PDF tanpa teks / scan gambar: {scanned_count}")
    print(f"- Chunk noise (daftar peserta/absensi murni) dibuang: {noise_chunks_dropped}")
    print(f"- Total chunk dokumen fatwa bersih dihasilkan: {len(all_docs)}")
    print(f"- Output JSON disimpan di: {output_file}")
    return all_docs


if __name__ == "__main__":
    process_fatwa_pdfs()
