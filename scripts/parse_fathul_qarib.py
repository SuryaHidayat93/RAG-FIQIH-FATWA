import re
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import json

BAB_NAMES = {
    1: "Muqaddimah",
    2: "Thaharah (Bersuci)",
    3: "Shalat Fardhu dan Sunnah",
    4: "Macam-macam Shalat Khusus",
    5: "Zakat Mal dan Fitrah",
    6: "Puasa dan I'tikaf",
    7: "Haji dan Umrah",
    8: "Muamalah, Transaksi dan Faraidh (Waris)",
    9: "Munakahat (Pernikahan)",
    10: "Talak, Rujuk, Iddah, dan Hak Asuh (Hadhanah)",
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
    text = text.replace("\ufffd", " ").replace("", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def is_arabic(text: str) -> bool:
    arabic_chars = re.findall(r"[\u0600-\u06FF]", text)
    return len(arabic_chars) > len(text) * 0.3 if text else False

def parse_html_chapter(filepath: Path, chapter_num: int):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    for el in soup.find_all(id=["goback", "footer", "header"]):
        el.decompose()
    for s in soup.find_all(["script", "style"]):
        s.decompose()

    h3 = soup.find("h3")
    raw_title = h3.get_text(strip=True) if h3 else ""
    chapter_name = BAB_NAMES.get(chapter_num, raw_title or f"Bab {chapter_num}")

    body = soup.find("body") or soup

    for tag in body.find_all(["br", "p", "div", "li", "h3", "h4", "blockquote"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    for st in body.find_all("strong"):
        st_text = st.get_text().strip()
        if st_text and len(st_text) < 100:
            st.replace_with(f"\n###STRONG_HEADER### {st_text}\n")

    raw_text = body.get_text()
    raw_lines = [clean_text(l) for l in raw_text.split("\n") if clean_text(l)]

    chunks = []
    current_title = "Pasal Umum"
    current_arabic = []
    current_indo = []

    def flush_chunk():
        nonlocal current_arabic, current_indo, current_title
        ar_str = " ".join(current_arabic).strip()
        in_str = " ".join(current_indo).strip()
        in_str = re.sub(r"^(Artinya|Terjemah)\s*:\s*", "", in_str, flags=re.IGNORECASE).strip()

        if len(in_str) > 25 or len(ar_str) > 25:
            content_parts = []
            if current_title:
                content_parts.append(f"[{chapter_name} - {current_title}]")
            if in_str:
                content_parts.append(f"Terjemahan: {in_str}")
            if ar_str:
                content_parts.append(f"Teks Matan Arab: {ar_str}")

            full_content = "\n\n".join(content_parts)
            chunks.append({
                "fasal": current_title,
                "arabic": ar_str,
                "indonesian": in_str,
                "content": full_content
            })
        current_arabic = []
        current_indo = []

    for line in raw_lines:
        if line in ["Waroeng Santri", "fathul qorib"]:
            continue

        if line.startswith("###STRONG_HEADER###"):
            flush_chunk()
            current_title = line.replace("###STRONG_HEADER###", "").strip()
            continue

        if line.isupper() and len(line) < 80 and not is_arabic(line) and not line.startswith("(") and not line.startswith("["):
            flush_chunk()
            current_title = line.strip()
            continue

        if line.startswith("(فصل)") or line.startswith("فصل"):
            if len(" ".join(current_indo)) > 150:
                flush_chunk()

        if is_arabic(line):
            current_arabic.append(line)
        else:
            current_indo.append(line)

        if len(" ".join(current_indo)) > 1000:
            flush_chunk()

    flush_chunk()
    return chapter_name, chunks

def parse_all_chapters():
    raw_dir = Path("data/fiqih/raw_fathul_qarib")
    all_documents = []

    files = sorted(raw_dir.glob("fat*.html"), key=lambda p: int("".join(filter(str.isdigit, p.stem)) or 0))
    print(f"Ditemukan {len(files)} file bab Fathul Qarib.")

    for f in files:
        chapter_num = int("".join(filter(str.isdigit, f.stem)) or 0)
        ch_name, chunks = parse_html_chapter(f, chapter_num)
        print(f"Bab {chapter_num:02d} ({ch_name:35s}): {len(chunks)} pasal/chunk")

        for idx, ch in enumerate(chunks, 1):
            doc_id = f"fathul-qarib-bab{chapter_num:02d}-{idx:03d}"
            all_documents.append({
                "id": doc_id,
                "content": ch["content"],
                "corpus": "fiqih",
                "metadata": {
                    "kitab": "Fathul Qarib Al-Mujib fi Syarh Alfazh Al-Ghayah wat Taqrib",
                    "pengarang": "Al-Allamah Syamsuddin Muhammad bin Qasim Al-Ghazi & Al-Qadhi Abu Syuja'",
                    "bab": ch_name,
                    "fasal": ch["fasal"],
                    "sumber_file": f.name,
                    "mazhab": "Syafi'i"
                }
            })

    output_file = Path("data/fiqih/fathul_qarib_full.json")
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(all_documents, out, ensure_ascii=False, indent=2)

    print(f"\nTotal Dokumen RAG Fiqih Syafi'i hasil ekstraksi: {len(all_documents)} dokumen.")
    print(f"File tersimpan di: {output_file}")
    return all_documents

if __name__ == "__main__":
    parse_all_chapters()
