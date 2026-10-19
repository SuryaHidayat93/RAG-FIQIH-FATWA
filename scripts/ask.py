"""Script CLI untuk mengajukan pertanyaan ke RAG Fiqih & Fatwa langsung dari terminal."""
import sys
from pathlib import Path
import requests

# Tambahkan root path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.graph import app_graph


def ask(query_text: str):
    api_url = f"http://127.0.0.1:{settings.api_port}"
    used_api = False

    try:
        h = requests.get(f"{api_url}/health", timeout=0.8)
        if h.status_code == 200:
            print(f">>> Mengirim pertanyaan ke FastAPI server ({api_url})...", flush=True)
            res = requests.post(f"{api_url}/ask", json={"query": query_text}, timeout=300)
            if res.status_code == 200:
                data = res.json()
                result = {
                    "generation": data.get("answer", ""),
                    "citations": data.get("citations", []),
                }
                used_api = True
    except Exception:
        pass

    if not used_api:
        initial_state = {
            "query": query_text,
            "retry_count": 0,
            "retrieved_documents": [],
        }
        result = app_graph.invoke(initial_state)

    print("\n" + "=" * 80)
    print("JAWABAN AKHIR SYARIAH:")
    print("=" * 80)
    print(result.get("generation", ""))
    print("=" * 80)

    citations = result.get("citations", [])
    if citations:
        print(f"\nDAFTAR SITASI ({len(citations)} Rujukan):")
        for i, c in enumerate(citations, 1):
            source = c.get("source", "Tidak diketahui")
            nomor = f" | No: {c['nomor_fatwa']}" if c.get("nomor_fatwa") else ""
            mazhab = f" | Mazhab: {c['mazhab']}" if c.get("mazhab") else ""
            bab = f" | Bab: {c['bab']}" if c.get("bab") else ""
            print(f"  {i}. [{c.get('corpus', '').upper()}] {source}{nomor}{mazhab}{bab}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = "Bagaimana fatwa hukum paylater dalam transaksi online menurut DSN MUI?"

    ask(user_query)
