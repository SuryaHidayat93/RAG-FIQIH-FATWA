"""Script pembersih dan ekstraksi granular Kitab Fathul Qarib Al-Mujib (Syafi'i).
Menghubungkan matan Arab dengan terjemahan Indonesia per pasal secara utuh,
membersihkan footnote/noise, dan menghasilkan korpus fiqih berkualitas tinggi untuk RAG.
"""
import html
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

BAB_NAMES = {
    1: "Muqaddimah",
    2: "Thaharah (Bersuci)",
    3: "Shalat Fardhu dan Sunnah",
    4: "Shalat Berjamaah dan Khusus",
    5: "Zakat Mal dan Fitrah",
    6: "Puasa dan I'tikaf",
    7: "Haji dan Umrah",
    8: "Muamalah, Jual Beli, dan Faraidh (Waris)",
    9: "Munakahat (Pernikahan)",
    10: "Talak, Rujuk, Iddah, dan Hadhanah",
    11: "Jinayat (Pidana, Qisas, dan Diyat)",
    12: "Hudud (Zina, Qadzaf, Pencurian, Begal)",
    13: "Jihad dan Hubungan Non-Muslim",
    14: "Sembelihan, Perburuan, Qurban, Aqiqah, dan Makanan",
    15: "Perlombaan dan Memanah (Musabaqah)",
    16: "Iman (Sumpah) dan Nazar",
    17: "Peradilan (Qadha), Gugatan, dan Saksi",
    18: "Pembebasan Budak (Itqu)"
}

def clean_text(text: str) -> str:
    """Membersihkan noise encoding, entitas HTML, tag rusak, dan whitespace berlebih."""
    text = html.unescape(text)
    # Hapus tag HTML sisa dan artefak tag rusak seperti b>, i>, <> dsb
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"(?i)\b(b|i|br|strong|p|blockquote)>\s*", "", text)
    text = re.sub(r"<>|,br>|&nbsp;", " ", text)
    # Hapus garis footnote panjang
    text = re.sub(r"-{4,}", "", text)
    # Hapus prefiks pengantar
    text = re.sub(r"^(Terjemah|Artinya|Arti)\s*:\s*", "", text, flags=re.IGNORECASE)
    # Hapus karakter pengganti encoding rusak
    text = text.replace("\ufffd", " ")
    # Bersihkan whitespace
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def is_arabic_text(text: str) -> bool:
    arabic_chars = re.findall(r"[\u0600-\u06FF]", text)
    return len(arabic_chars) > 5 and (len(arabic_chars) / max(len(text), 1)) > 0.25

def extract_fasal_title(lines: list[str], default_title: str) -> str:
    for line in lines[:3]:
        clean = clean_text(line)
        if 4 < len(clean) < 70 and not clean.endswith("."):
            return re.sub(r"^(Pasal|Hukum|Tata cara|Syarat|Fardhu|Rukun)\b", r"\1", clean, flags=re.IGNORECASE).strip(": -")
    return default_title

def chunk_content(content: str, target_size: int = 1000, max_size: int = 1500) -> list[str]:
    """Membagi teks panjang menjadi chunk proporsional per batas kalimat/paragraf."""
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if not lines:
        return []

    chunks = []
    current_lines = []
    current_len = 0

    for l in lines:
        if current_len + len(l) > max_size and current_lines:
            chunks.append("\n".join(current_lines))
            current_lines = []
            current_len = 0
        current_lines.append(l)
        current_len += len(l) + 1
        if current_len >= target_size:
            chunks.append("\n".join(current_lines))
            current_lines = []
            current_len = 0

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks

def process_chapter(filepath: Path, chapter_num: int) -> list[dict]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        html_raw = f.read()

    soup = BeautifulSoup(html_raw, "html.parser")

    # Buang navigasi dan footer
    for el in soup.find_all(id=["goback", "footer", "header", "script", "style"]):
        el.decompose()

    # Ubah pembatas tag menjadi newline teratur
    for tag in soup.find_all(["br", "p", "div", "li", "h3", "h4", "blockquote"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    raw_lines = [clean_text(l) for l in soup.get_text().split("\n") if clean_text(l)]

    # Filter baris navigasi bawaan web
    filtered_lines = [l for l in raw_lines if l.lower() not in ["fathul qorib", "waroeng santri", "index.html"]]

    # Pisahkan blok bergantian (Arab dan Indonesia)
    blocks = []
    current_type = None
    current_lines = []

    for l in filtered_lines:
        line_type = "AR" if is_arabic_text(l) else "ID"
        if line_type != current_type and current_lines:
            blocks.append((current_type, "\n".join(current_lines)))
            current_lines = []
        current_type = line_type
        current_lines.append(l)

    if current_lines:
        blocks.append((current_type, "\n".join(current_lines)))

    chapter_name = BAB_NAMES.get(chapter_num, f"Bab {chapter_num}")
    sections = []

    i = 0
    # Lewati baris pertama jika hanya judul bab pendek ID (misal 'Toharoh')
    if blocks and blocks[0][0] == "ID" and len(blocks[0][1]) < 40:
        i = 1

    sec_counter = 1
    while i < len(blocks):
        b_type, b_txt = blocks[i]
        ar_content = ""
        id_content = ""

        if b_type == "AR":
            ar_content = b_txt
            if i + 1 < len(blocks) and blocks[i + 1][0] == "ID":
                id_content = blocks[i + 1][1]
                i += 2
            else:
                i += 1
        else:
            id_content = b_txt
            if i + 1 < len(blocks) and blocks[i + 1][0] == "AR":
                ar_content = blocks[i + 1][1]
                i += 2
            else:
                i += 1

        ar_clean = clean_text(ar_content)
        id_clean = clean_text(id_content)

        if len(id_clean) < 30 and len(ar_clean) < 30:
            continue

        id_lines = [l for l in id_clean.split("\n") if l.strip()]
        fasal_title = extract_fasal_title(id_lines, f"Pasal {sec_counter}")

        # Chunking adaptif jika terjemahan panjang
        if len(id_clean) > 1600:
            sub_chunks = chunk_content(id_clean, target_size=1000, max_size=1500)
            for sub_idx, sub_text in enumerate(sub_chunks, 1):
                sub_lines = [l for l in sub_text.split("\n") if l.strip()]
                sub_title = extract_fasal_title(sub_lines, f"{fasal_title} (Bagian {sub_idx})")
                sections.append({
                    "fasal": sub_title if sub_idx > 1 else fasal_title,
                    "indonesian": sub_text,
                    "arabic": ar_clean if sub_idx == 1 else "",
                    "sub_idx": sub_idx,
                })
        else:
            sections.append({
                "fasal": fasal_title,
                "indonesian": id_clean,
                "arabic": ar_clean,
                "sub_idx": 1,
            })

        sec_counter += 1

    return chapter_name, sections

def run_clean_pipeline():
    raw_dir = Path("data/fiqih/raw_fathul_qarib")
    files = sorted(raw_dir.glob("fat*.html"), key=lambda p: int("".join(filter(str.isdigit, p.stem)) or 0))

    all_docs = []
    print("=== Menjalankan Pipeline Pembersihan Korpus Fathul Qarib ===")

    for f in files:
        ch_num = int("".join(filter(str.isdigit, f.stem)) or 0)
        ch_name, sections = process_chapter(f, ch_num)
        print(f"✓ Bab {ch_num:02d} ({ch_name:42s}): {len(sections):3d} chunk optimal")

        for idx, sec in enumerate(sections, 1):
            doc_id = f"fathul-qarib-bab{ch_num:02d}-sec{idx:03d}"
            
            content_parts = [
                f"[Kitab Fathul Qarib | {ch_name} | {sec['fasal']}]",
                f"Terjemahan & Hukum Fiqih:\n{sec['indonesian']}"
            ]
            if sec["arabic"]:
                content_parts.append(f"Teks Matan Arab:\n{sec['arabic']}")

            full_content = "\n\n".join(content_parts)

            all_docs.append({
                "id": doc_id,
                "content": full_content,
                "corpus": "fiqih",
                "metadata": {
                    "kitab": "Fathul Qarib Al-Mujib",
                    "pengarang": "Syamsuddin Abu Abdillah Muhammad bin Qasim Al-Ghazi & Al-Qadhi Abu Syuja'",
                    "bab": ch_name,
                    "fasal": sec["fasal"],
                    "sumber_file": f.name,
                    "mazhab": "Syafi'i"
                }
            })

    output_path = Path("data/fiqih/fathul_qarib_full.json")
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(all_docs, out, ensure_ascii=False, indent=2)

    lengths = [len(d["content"]) for d in all_docs]
    print(f"\n=======================================================")
    print(f"Total Dokumen Bersih: {len(all_docs)}")
    print(f"Distribusi Panjang: Min={min(lengths)}, Max={max(lengths)}, Rata-rata={sum(lengths)//len(lengths)} karakter")
    print(f"File tersimpan di: {output_path}")
    print(f"=======================================================")
    return all_docs

if __name__ == "__main__":
    run_clean_pipeline()
